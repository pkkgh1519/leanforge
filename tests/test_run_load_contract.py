import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import run_load_contract_support as support


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "src/skills/run/references/load-graph.json"
CONTRACT_PATH = (
    ROOT / "src/skills/run/references/semantic-contract.json"
)
FIXTURE_PATH = (
    ROOT / "tests/fixtures/forced_load_baseline_v1_9_0.json"
)
TOP_LEVEL_KEYS = {
    "schema_version",
    "graph_id",
    "nodes",
    "edges",
    "named_roots",
    "profiles",
}
EXPECTED_NODES = {
    "run/SKILL.md",
    "run/references/graph-contract.md",
    "run/references/harness-format.md",
    "run/references/harness-lifecycle.md",
    "run/references/harness-review.md",
    "run/references/implementer-prompt.md",
    "run/references/orchestration.md",
    "run/references/repo-lens-routing.md",
    "run/references/reviewer-prompt.md",
    "run/references/spec-review-prompt.md",
}


class RunLoadContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = support.load_json(GRAPH_PATH)
        cls.contract = support.load_json(CONTRACT_PATH)
        cls.surface_root = ROOT / "src/skills"
        cls.available_paths = {
            path.relative_to(cls.surface_root).as_posix()
            for path in (cls.surface_root / "run").rglob("*")
            if path.is_file()
        }
        cls.documents = {
            path.relative_to(cls.surface_root).as_posix():
                path.read_text(encoding="utf-8")
            for path in (cls.surface_root / "run").rglob("*.md")
        }
        cls.node_paths = {
            node["path"] for node in cls.graph["nodes"]
        }
        cls.directives = (
            support.discover_directives_from_documents(
                cls.documents, cls.node_paths
            )
        )

    def validate(self, graph, directives=None, available_paths=None):
        support.validate_graph(
            graph,
            self.contract,
            available_paths=(
                self.available_paths
                if available_paths is None
                else available_paths
            ),
            directives=directives,
        )

    def assert_contract_error(self, text, operation):
        with self.assertRaisesRegex(
            support.LoadContractError, text
        ):
            operation()

    def closure(
        self,
        *,
        route="direct",
        overlay=None,
        phase="route_union",
        profile="default",
        graph=None,
    ):
        return support.instruction_closure(
            self.graph if graph is None else graph,
            self.contract,
            root="run",
            route=route,
            overlay=overlay,
            phase=phase,
            profile=profile,
        )

    def test_canonical_graph_has_a_closed_versioned_envelope(self):
        self.assertEqual(TOP_LEVEL_KEYS, set(self.graph))
        self.assertEqual(1, self.graph["schema_version"])
        self.assertEqual(
            "leanforge.run.instruction-loads",
            self.graph["graph_id"],
        )
        self.assertEqual(
            EXPECTED_NODES,
            {node["path"] for node in self.graph["nodes"]},
        )
        self.assertEqual(10, len(self.graph["edges"]))
        self.validate(self.graph, self.directives)

    def test_graph_contains_only_contract_nodes_edges_roots_profiles(self):
        self.assertNotIn(
            "run/references/semantic-contract.json",
            self.node_paths,
        )
        self.assertEqual(
            {"force_load", "prompt_load", "optional_load"},
            {edge["kind"] for edge in self.graph["edges"]},
        )
        forbidden = {
            "condition", "conditions", "union", "unions",
            "total", "totals", "manual_overlay",
        }
        self.assertTrue(
            forbidden.isdisjoint(self.graph)
        )
        for edge in self.graph["edges"]:
            self.assertTrue(forbidden.isdisjoint(edge))

    def test_structured_markers_stay_within_approved_canonical_markdown(self):
        self.assertEqual(
            {
                "run/SKILL.md",
                "run/references/orchestration.md",
                "run/references/harness-lifecycle.md",
            },
            {directive["from"] for directive in self.directives},
        )

    def test_unknown_top_level_or_graph_local_conditions_fail_closed(self):
        for mutation in (
            lambda graph: graph.update({"totals": {}}),
            lambda graph: graph["edges"][0].update(
                {"condition": "route == direct"}
            ),
        ):
            with self.subTest(mutation=mutation):
                graph = copy.deepcopy(self.graph)
                mutation(graph)
                self.assert_contract_error(
                    "envelope is not closed",
                    lambda graph=graph: self.validate(graph),
                )

    def test_unknown_kind_and_optional_mismatch_fail_closed(self):
        graph = copy.deepcopy(self.graph)
        graph["edges"][0]["kind"] = "preload"
        self.assert_contract_error(
            "unknown load edge kind",
            lambda: self.validate(graph),
        )
        graph = copy.deepcopy(self.graph)
        graph["edges"][0]["optional"] = True
        self.assert_contract_error(
            "optional flag",
            lambda: self.validate(graph),
        )

    def test_absolute_traversal_unknown_and_duplicate_paths_fail(self):
        cases = (
            ("C:/outside.md", "absolute logical path"),
            ("run/../outside.md", "path traversal"),
            ("run/references/unknown.md", "unknown logical node"),
        )
        for path, reason in cases:
            with self.subTest(path=path):
                graph = copy.deepcopy(self.graph)
                old = graph["nodes"][1]["path"]
                graph["nodes"][1]["path"] = path
                for edge in graph["edges"]:
                    if edge["from"] == old:
                        edge["from"] = path
                    if edge["to"] == old:
                        edge["to"] = path
                self.assert_contract_error(
                    reason,
                    lambda graph=graph: self.validate(graph),
                )
        graph = copy.deepcopy(self.graph)
        graph["nodes"].append(copy.deepcopy(graph["nodes"][0]))
        self.assert_contract_error(
            "duplicate logical node identity",
            lambda: self.validate(graph),
        )

    def test_orphan_activation_missing_binding_and_wrong_phase_fail(self):
        graph = copy.deepcopy(self.graph)
        graph["edges"][0]["activation_contract_id"] = "RUN-ORPHAN"
        self.assert_contract_error(
            "orphan activation contract id",
            lambda: self.validate(graph),
        )

        graph = copy.deepcopy(self.graph)
        graph["edges"][0]["phase"] = "harness"
        self.assert_contract_error(
            "wrong phase",
            lambda: self.validate(graph),
        )

        same_kind_phase_mutations = (
            (0, "graph_preflight"),
            (7, "review"),
            (8, "final_review"),
        )
        for edge_index, mutated_phase in same_kind_phase_mutations:
            with self.subTest(
                edge_index=edge_index, mutated_phase=mutated_phase
            ):
                graph = copy.deepcopy(self.graph)
                original_edge = copy.deepcopy(graph["edges"][edge_index])
                graph["edges"][edge_index]["phase"] = mutated_phase
                directives = copy.deepcopy(self.directives)
                directive = next(
                    item for item in directives if item == original_edge
                )
                directive["phase"] = mutated_phase
                for profile in graph["profiles"]:
                    for selector in profile["optional_edges"]:
                        if (
                            selector["from"] == original_edge["from"]
                            and selector["to"] == original_edge["to"]
                            and selector["phase"] == original_edge["phase"]
                        ):
                            selector["phase"] = mutated_phase
                self.assert_contract_error(
                    "wrong phase",
                    lambda graph=graph, directives=directives: self.validate(
                        graph, directives=directives
                    ),
                )

        directives = list(self.directives)
        directives.pop()
        self.assert_contract_error(
            "missing its structured marker",
            lambda: self.validate(
                self.graph, directives=directives
            ),
        )

    def test_markers_are_discovered_outside_heading_assumptions(self):
        documents = dict(self.documents)
        source = "run/SKILL.md"
        marker_match = support.MARKER_RE.search(documents[source])
        self.assertIsNotNone(marker_match)
        marker = marker_match.group(0)
        documents[source] = documents[source].replace(marker, "", 1)
        documents[source] += (
            "\n# Marker moved\n~~~text\n" + marker + "\n~~~\n"
        )
        directives = support.discover_directives_from_documents(
            documents, self.node_paths
        )
        self.validate(self.graph, directives=directives)

    def test_hidden_undeclared_marker_and_plain_preload_fail(self):
        documents = dict(self.documents)
        hidden = copy.deepcopy(self.graph["edges"][7])
        hidden["to"] = "run/references/harness-review.md"
        documents["run/references/orchestration.md"] += (
            "\n~~~text\n<!-- leanforge:run-load "
            + json.dumps(hidden, separators=(",", ":"))
            + " -->\n~~~\n"
        )
        directives = support.discover_directives_from_documents(
            documents, self.node_paths
        )
        self.assert_contract_error(
            "undeclared edge",
            lambda: self.validate(
                self.graph, directives=directives
            ),
        )

        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\nPreload references/harness-review.md "
            "before continuing.\n"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\nForce-load\n`references/harness-review.md` "
            "before continuing.\n"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\nCompatibility-only (non-operative legacy assertion): "
            "~~Preload references/harness-review.md before continuing.~~\n"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\n" + support.LEGACY_COMPATIBILITY_LITERAL + "\n"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

    def test_direct_failure_recurses_to_implementer_prompt(self):
        happy = self.closure()
        failed = self.closure(
            overlay="failure",
            phase="failure_route_union",
        )
        prompt = "run/references/implementer-prompt.md"
        self.assertNotIn(prompt, happy["instruction_nodes"])
        self.assertIn(prompt, failed["instruction_nodes"])
        self.assertEqual(
            happy["forced_load_nodes"],
            failed["forced_load_nodes"],
        )

        invariant = next(
            item
            for item in self.contract["invariants"]
            if item["id"] == "RUN-FAIL-CLOSED"
        )
        invariant_text = json.dumps(invariant)
        self.assertIn("remedial worktree", invariant_text)
        self.assertIn(
            "run/references/orchestration.md",
            failed["instruction_nodes"],
        )

    def test_dispatched_routes_and_conditional_review_use_prompts(self):
        prompt = "run/references/implementer-prompt.md"
        for route in ("single_risky", "parallel", "external"):
            with self.subTest(route=route):
                closure = self.closure(
                    route=route,
                    phase="entry_execution",
                )
                self.assertIn(
                    prompt, closure["instruction_nodes"]
                )

        conditional = self.closure(
            route="single_risky",
            phase="conditional_review",
        )
        self.assertIn(
            "run/references/spec-review-prompt.md",
            conditional["instruction_nodes"],
        )
        self.assertIn(
            "run/references/reviewer-prompt.md",
            conditional["instruction_nodes"],
        )

    def test_optional_loads_are_excluded_by_default(self):
        default = self.closure()
        self.assertNotIn(
            "run/references/harness-review.md",
            default["instruction_nodes"],
        )
        self.assertNotIn(
            "run/references/repo-lens-routing.md",
            default["instruction_nodes"],
        )

        harness = self.closure(profile="harness_changed")
        self.assertIn(
            "run/references/harness-review.md",
            harness["instruction_nodes"],
        )
        lens = self.closure(profile="repo_lens")
        self.assertIn(
            "run/references/repo-lens-routing.md",
            lens["instruction_nodes"],
        )
        self.assertNotIn(
            "run/references/harness-review.md",
            lens["instruction_nodes"],
        )

    def test_content_identical_paths_keep_distinct_identity(self):
        graph = copy.deepcopy(self.graph)
        copy_path = (
            "run/references/implementer-prompt-copy.md"
        )
        graph["nodes"].append({"path": copy_path})
        edge = copy.deepcopy(
            next(
                edge
                for edge in graph["edges"]
                if edge["to"]
                == "run/references/implementer-prompt.md"
            )
        )
        edge["to"] = copy_path
        graph["edges"].append(edge)
        closure = self.closure(
            graph=graph,
            overlay="failure",
            phase="failure_route_union",
        )
        self.assertIn(
            "run/references/implementer-prompt.md",
            closure["instruction_nodes"],
        )
        self.assertIn(copy_path, closure["instruction_nodes"])

    def test_baseline_fixture_has_exact_provenance_and_node_metadata(self):
        fixture = support.load_json(FIXTURE_PATH)
        support.validate_fixture(fixture)
        self.assertEqual(
            support.BEHAVIOR_ORIGIN_COMMIT,
            fixture["behavior_origin_commit"],
        )
        self.assertEqual(
            support.BYTE_BASELINE_COMMIT,
            fixture["byte_baseline_commit"],
        )
        self.assertEqual(
            set(support.SURFACES),
            set(fixture["surfaces"]),
        )
        for surface in support.SURFACES:
            records = fixture["surfaces"][surface]["nodes"]
            self.assertEqual(10, len(records))
            for record in records:
                self.assertRegex(
                    record["git_blob_oid"], r"^[0-9a-f]{40}$"
                )
                self.assertRegex(
                    record["sha256"], r"^[0-9a-f]{64}$"
                )
                self.assertGreater(record["raw_bytes"], 0)
                self.assertGreater(record["words"], 0)

    def test_graph_and_fixture_numeric_types_are_closed(self):
        graph = copy.deepcopy(self.graph)
        graph["schema_version"] = True
        self.assert_contract_error(
            "schema_version must be integer 1",
            lambda: self.validate(graph),
        )

        mutations = (
            (
                lambda fixture: fixture.update(
                    {"schema_version": True}
                ),
                "fixture schema version",
            ),
            (
                lambda fixture: fixture["surfaces"]["src/skills"][
                    "nodes"
                ][0].update({"raw_bytes": True}),
                "raw byte count must be a nonnegative integer",
            ),
            (
                lambda fixture: fixture["surfaces"]["src/skills"][
                    "closures"
                ][0].update(
                    {
                        "raw_bytes": float(
                            fixture["surfaces"]["src/skills"][
                                "closures"
                            ][0]["raw_bytes"]
                        )
                    }
                ),
                "closure raw byte count must be a nonnegative integer",
            ),
            (
                lambda fixture: fixture["surfaces"]["src/skills"][
                    "closures"
                ][0].update({"instruction_nodes": "run/SKILL.md"}),
                "closure instruction_nodes must be a list",
            ),
        )
        for mutation, reason in mutations:
            with self.subTest(reason=reason):
                fixture = support.load_json(FIXTURE_PATH)
                mutation(fixture)
                self.assert_contract_error(
                    reason,
                    lambda fixture=fixture: support.validate_fixture(
                        fixture
                    ),
                )

    def test_capture_is_deterministic_and_uses_exact_git_blobs(self):
        first = support.capture_baseline(ROOT)
        second = support.capture_baseline(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(
            support.serialize_fixture(first),
            support.serialize_fixture(second),
        )
        for surface in support.SURFACES:
            for record in first["surfaces"][surface]["nodes"]:
                raw = support._git(
                    ROOT,
                    "cat-file",
                    "blob",
                    record["git_blob_oid"],
                    binary=True,
                )
                self.assertEqual(
                    record["sha256"],
                    hashlib.sha256(raw).hexdigest(),
                )
                self.assertEqual(
                    record["raw_bytes"], len(raw)
                )
                self.assertEqual(
                    record["words"],
                    len(raw.decode("utf-8").split()),
                )

    def test_predecessor_forced_overlay_is_empty_but_full_direct_delta_is_not(self):
        fixture = support.load_json(FIXTURE_PATH)
        for surface in support.SURFACES:
            closures = {
                item["name"]: item
                for item
                in fixture["surfaces"][surface]["closures"]
            }
            for route in (
                "direct", "single_risky", "parallel", "external"
            ):
                report = closures[
                    f"failure_overlay_report.{route}"
                ]
                self.assertEqual([], report["forced_load_nodes"])
                self.assertEqual(0, report["raw_bytes"])
                self.assertEqual(0, report["words"])
            self.assertEqual(
                ["run/references/implementer-prompt.md"],
                closures[
                    "failure_overlay_report.direct"
                ]["instruction_nodes"],
            )

    def test_manual_overlay_mutation_is_rejected(self):
        fixture = support.load_json(FIXTURE_PATH)
        mutant = copy.deepcopy(fixture)
        report = mutant["surfaces"]["src/skills"][
            "closures"
        ][-4]
        report["forced_load_nodes"] = [
            "run/references/orchestration.md"
        ]
        report["raw_bytes"] = 1
        self.assert_contract_error(
            "forced-load overlay must be empty",
            lambda: support.validate_fixture(mutant),
        )

    def test_crlf_and_generated_only_drift_change_raw_measurement(self):
        baseline = support.measure_candidate(
            ROOT, self.graph, self.contract
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for surface in support.SURFACES:
                source = ROOT / surface / "run"
                target = root / surface / "run"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, target)

            codex_skill = (
                root / "codex/plugin/skills/run/SKILL.md"
            )
            raw = codex_skill.read_bytes()
            lf = raw.replace(b"\r\n", b"\n")
            codex_skill.write_bytes(
                lf.replace(b"\n", b"\r\n")
                + b"generated-only-drift\r\n"
            )
            mutated = support.measure_candidate(
                root, self.graph, self.contract
            )

        def record(measurement, surface, path):
            return next(
                item
                for item in measurement[surface]["nodes"]
                if item["path"] == path
            )

        path = "run/SKILL.md"
        self.assertEqual(
            record(baseline, "src/skills", path),
            record(mutated, "src/skills", path),
        )
        self.assertNotEqual(
            record(baseline, "codex/plugin/skills", path)[
                "sha256"
            ],
            record(mutated, "codex/plugin/skills", path)[
                "sha256"
            ],
        )
        self.assertNotEqual(
            record(baseline, "codex/plugin/skills", path)[
                "raw_bytes"
            ],
            record(mutated, "codex/plugin/skills", path)[
                "raw_bytes"
            ],
        )

    def test_surface_plus_path_identity_is_not_cross_surface_deduped(self):
        candidate = support.measure_candidate(
            ROOT, self.graph, self.contract
        )
        identities = [
            (surface, node["path"])
            for surface in support.SURFACES
            for node in candidate[surface]["nodes"]
        ]
        self.assertEqual(30, len(identities))
        self.assertEqual(30, len(set(identities)))

    def test_read_only_verify_has_four_separate_reports_and_never_captures(self):
        before = support.scoped_product_hash(ROOT)
        with mock.patch.object(
            support,
            "capture_baseline",
            side_effect=AssertionError(
                "verify called capture"
            ),
        ):
            result = support.verify_baseline(ROOT)
        after = support.scoped_product_hash(ROOT)
        self.assertEqual(
            {
                "predecessor_fixture_match",
                "candidate_measurement",
                "closure_delta",
                "failure_overlay_difference",
                "read_only",
            },
            set(result),
        )
        self.assertTrue(
            result["predecessor_fixture_match"]["matched"]
        )
        self.assertTrue(result["read_only"]["unchanged"])
        self.assertEqual(before, after)

    def test_capture_and_verify_are_runnable_as_separate_direct_entry_points(self):
        verify = subprocess.run(
            [sys.executable, str(ROOT / "tests/verify_run_load_baseline.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, verify.returncode, verify.stderr)
        self.assertEqual(
            {
                "predecessor_fixture_match",
                "candidate_measurement",
                "closure_delta",
                "failure_overlay_difference",
                "read_only",
            },
            set(json.loads(verify.stdout)),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "captured.json"
            capture = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tests/capture_run_load_baseline.py"),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, capture.returncode, capture.stderr)
            self.assertEqual(
                json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
                json.loads(output.read_text(encoding="utf-8")),
            )

    def test_candidate_size_equality_is_reported_not_required(self):
        result = support.verify_baseline(ROOT)
        deltas = [
            closure["raw_bytes_delta"]
            for surface in support.SURFACES
            for closure
            in result["closure_delta"][surface].values()
        ]
        self.assertTrue(any(delta != 0 for delta in deltas))
        for view in (
            "predecessor", "candidate"
        ):
            for surface in support.SURFACES:
                for report in result[
                    "failure_overlay_difference"
                ][view][surface].values():
                    self.assertEqual(
                        [], report["forced_load_nodes"]
                    )
                    self.assertEqual(0, report["raw_bytes"])

    def test_generated_surfaces_repeat_the_canonical_contract(self):
        graph, contract = support.validate_repository(ROOT)
        self.assertEqual(self.graph, graph)
        self.assertEqual(self.contract, contract)


if __name__ == "__main__":
    unittest.main()
