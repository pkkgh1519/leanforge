import copy
import hashlib
import json
import re
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

    def test_lifecycle_header_preserves_each_runtime_phase_boundary(self):
        lifecycle = self.documents["run/references/harness-lifecycle.md"]
        support.validate_lifecycle_header(lifecycle)

    def test_lifecycle_header_rejects_boundary_negation_mutations(self):
        lifecycle = self.documents["run/references/harness-lifecycle.md"]
        mutations = (
            lifecycle.replace(
                "recovery and migration run before mutation",
                "recovery and migration do not run before mutation",
            ),
            lifecycle.replace(
                "harness creation or update runs after the\ncompletion gate",
                "harness creation or update does not run after the\n"
                "completion gate",
            ),
            lifecycle.replace(
                "archive runs only after user approval",
                "archive does not run only after user approval",
            ),
        )
        for index, mutated in enumerate(mutations):
            self.assertNotEqual(lifecycle, mutated)
            with self.subTest(mutation=index):
                self.assert_contract_error(
                    "lifecycle header semantic drift",
                    lambda mutated=mutated: support.validate_lifecycle_header(
                        mutated
                    ),
                )

    def test_foundation_format_is_producer_provenance_not_a_hidden_run_load(self):
        run_foundation = (
            ROOT / "src/skills/run/references/foundation-format.md"
        ).read_text(encoding="utf-8")
        prime_foundation = (
            ROOT / "src/skills/prime/references/foundation-format.md"
        ).read_text(encoding="utf-8")
        lifecycle = " ".join(
            self.documents["run/references/harness-lifecycle.md"].split()
        )

        self.assertEqual(prime_foundation, run_foundation)
        self.assertIn("Run does not load this reference", run_foundation)
        self.assertIn("embedded Project Foundation", lifecycle)
        self.assertIn(
            "Map the embedded Foundation to files as follows",
            lifecycle,
        )
        self.assertNotIn("per `foundation-format.md`", lifecycle)

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

    def test_read_and_consult_imperatives_cannot_bypass_the_graph(self):
        cases = (
            ("run/SKILL.md", "Read", "references/harness-review.md"),
            ("run/SKILL.md", "Consult", "references/foundation-format.md"),
            ("run/SKILL.md", "Read", "run/references/harness-review.md"),
            ("run/SKILL.md", "Consult", "run/references/foundation-format.md"),
            ("run/SKILL.md", "Read", "foundation-format.md"),
            ("run/SKILL.md", "Consult", "./references/harness-review.md"),
            (
                "run/SKILL.md",
                "Read",
                "run/../run/references/harness-review.md",
            ),
            (
                "run/references/orchestration.md",
                "Read",
                "../references/harness-review.md",
            ),
            (
                "run/references/orchestration.md",
                "Consult",
                "../references/foundation-format.md",
            ),
        )
        for document_path, verb, path in cases:
            with self.subTest(document=document_path, verb=verb, path=path):
                documents = dict(self.documents)
                documents[document_path] += (
                    f"\n{verb} `{path}` before continuing.\n"
                )
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )


    def test_packaged_markdown_occurrences_require_closed_classification(self):
        cases = (
            "Open `references/harness-review.md` before continuing.",
            "Inspect `references/harness-review.md` before continuing.",
            "Read " + ("x" * 161) + " `references/harness-review.md` before continuing.",
            "`references/harness-review.md` must be read before continuing.",
            "For details, see harness-review.m**d**.",
            "For details, see "
            "[harness-review.m](https://example.invalid/a(b)c)d.",
            "For details, see "
            "[harness-review.m](<https://example.invalid/a(b>)d.",
            'For details, see [harness-review.m]('
            'https://example.invalid/ "title(foo")d.',
            'For details, see [harness-review.m]('
            'https://example.invalid/ (note"foo))d.',
            "For details, see harness-review.m<!-- >\n -->d.",
        )
        for sentence in cases:
            with self.subTest(sentence=sentence):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{sentence}\n"
                self.assert_contract_error(
                    "unclassified packaged Markdown reference",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_invalid_inline_link_fallback_remains_visible_and_is_rejected(self):
        raw_html_constructs = (
            "<span></span>",
            "<!--hidden-->",
            "<?hidden?>",
            "<![CDATA[hidden]]>",
            "<!HIDDEN>",
        )

        for construct in raw_html_constructs:
            with self.subTest(construct=construct):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    "\n[x](Open references/harness-"
                    f"{construct}review.md)\n"
                )
                self.assert_contract_error(
                    "unclassified packaged Markdown reference",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents,
                            self.node_paths,
                        )
                    ),
                )

    def test_non_link_markdown_contexts_keep_inline_fallback_visible(self):
        cases = (
            r"\[x](Open)",
            r"[x\](Open)",
            "`[x](Open)`",
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_code_block_link_fallback_remains_visible(self):
        cases = (
            "~~~\n[x](Open)\n~~~",
            "> ~~~\n> [x](Open)\n> ~~~",
            "# boundary\n\n    [x](Open)",
            "# boundary\n\n\t- [x](Open)",
            "# boundary\n\n\t> [x](Open)",
            "# boundary\n\n\t# [x](Open)",
            "# boundary\n\n \t- [x](Open)",
            "\t```\n\t[x](Open)\n\t```",
            "\t<div>\n\t[x](Open)",
            "# boundary\n\n`<!--`\nOpen\n-->",
            "# boundary\n\n    <!--\nOpen\n-->",
            "# boundary\n\n```\n<!--\n```\nOpen\n-->",
            "# boundary\n\n- x <!--\n- Open\n-->",
            "# boundary\n\nx <!--\n===\nOpen\n-->",
            "# boundary\n\n`\n2. [x](Open)\n`",
            "# boundary\n\n<script\n[x](Open)\n</script>",
            "# boundary\n\n<div\n[x](Open)",
            "# boundary\n\n```\n\t```\n[x](Open)\n````",
            "# boundary\n\n> \t```\n> [x](Open)\n> ````",
            "# boundary\n\n> - ```\n>   \t```\n>   [x](Open)",
            "# boundary\n\n> ```\n>\t  ```\n> [x](Open)",
            "# boundary\n\n>\t  [x](Open)",
            "# boundary\n\n>\t>\t  [x](Open)",
            "# boundary\n\n-  >\t [x](Open)",
            "# boundary\n\n1. >\t [x](Open)",
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_container_code_and_html_do_not_bind_fake_definitions(self):
        cases = (
            "[x][r]\n\n- ```\n  [r]: Open\n  ```",
            "[x][r]\n\n- ~~~\n  [r]: Open\n  ~~~",
            "[x][r]\n\n<div>\n[r]: Open\n</div>",
            "<div>\n[x](Open)\n</div>",
            "<pre>\n[x](Open)\n</pre>",
            "[x][r]\n\n- > ```\n  > [r]: Open\n  > ```",
            "[x][r]\n\n- [r]:\n- Open",
            '[x][r]\n\n- [r]: https://example.invalid/\n- "Open"',
            "[x][Open]\n\n<!--\n[Open]: https://example.invalid/\n-->",
            "[x][Open]\n\n<?x\n[Open]: https://example.invalid/\n?>",
            "[x][Open]\n\n<![CDATA[\n[Open]: https://example.invalid/\n]]>",
            "[x][Open]\n\n<!X\n[Open]: https://example.invalid/\n>",
            "[x][r]\n\n- item\n  - ```\n    [r]: Open\n    ```",
            "<custom>\n[x](Open)\n",
            (
                "[\u00a0]: https://example.invalid/\n"
                "<custom>\n[x](Open)"
            ),
            "</div>\n[x](Open)\n",
            (
                "[x][Open]\n\n<custom>\n"
                "[Open]: https://example.invalid/\n"
            ),
            (
                "[x][Open]\n\n</div>\n"
                "[Open]: https://example.invalid/\n"
            ),
            (
                "[x][r]\n\n- > - ```\n"
                "  >   [r]: Open\n"
                "  >   ```"
            ),
            (
                "[x][r]\n\n> - > ```\n"
                ">   > [r]: Open\n"
                ">   > ```"
            ),
            "# h\n<custom>\n[x](Open)\n",
            "---\n<custom data-x=one>\n[x](Open)\n",
            "```\nx\n```\n<custom>\n[x](Open)\n",
            (
                "[x][r]\n\n- ```\n"
                "  - code\n"
                "  [r]: Open\n"
                "  ```"
            ),
            "[x][r]\n\n```\n- ```\n[r]: Open\n```",
            "[x][r]\n\n<div>\n>\n[r]: Open\n\n",
            "- - -\n<custom>\n[x](Open)\n",
            "* * *\n<custom>\n[x](Open)\n",
            "# boundary\n\n    code\n<custom>\n[x](Open)\n",
            "# boundary\n\nheading\n-\n<custom>\n[x](Open)\n",
            "# boundary\n\n*\n<custom>\n[x](Open)\n",
            "# boundary\n\n1.\n<custom>\n[x](Open)\n",
            (
                '[r]: https://example.invalid/\n'
                '  "title\n'
                '  more"\n'
                '<custom>\n[x](Open)'
            ),            (
                "# boundary\n\n[x][r]\n\n"
                "-     [r]: Open"
            ),
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_fenced_code_definition_does_not_bind_reference_label(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\n[x][r]\n\n```\n[r]: Open\n```\n"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

    def test_undefined_reference_label_remains_visible_and_is_rejected(self):
        cases = (
            "[x][Open]",
            "[x][Open]\n\n[other]: https://example.invalid/",
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_ascii_whitespace_only_reference_definition_label_remains_visible(self):
        markdown_cases = (
            "[ ]: Open&#32;harness-review\\.md",
            "[\t]: Open&#32;harness-review\\.md",
            "[ \n ]: Open&#32;harness-review\\.md",
            (
                "["
                + "a" * 499
                + "\n "
                + "b" * 499
                + "]: Open&#32;harness-review\\.md"
            ),
        )
        for markdown in markdown_cases:
            with self.subTest(markdown=ascii(markdown)):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )
    def test_unicode_separator_does_not_alias_ascii_reference_label(self):
        separators = (
            "\u00a0",
            "\u1680",
            "\u2003",
            "\u202f",
            "\u205f",
            "\u3000",
        )
        for separator in separators:
            with self.subTest(separator=ascii(separator)):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    f"\n[x][Open{separator}SKILL\\.md]\n\n"
                    "[Open SKILL\\.md]: /\n"
                )
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )
    def test_unicode_separator_reference_label_is_valid_metadata(self):
        separators = (
            "\u000b",
            "\u000c",
            "\u001c",
            "\u001d",
            "\u001e",
            "\u0085",
            "\u00a0",
            "\u1680",
            "\u2003",
            "\u2028",
            "\u2029",
            "\u202f",
            "\u205f",
            "\u3000",
        )
        for separator in separators:
            with self.subTest(separator=ascii(separator)):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    f"\n[{separator}]: "
                    "Open&#32;harness-review\\.md\n"
                )
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents, self.node_paths
                    ),
                )

    def test_non_commonmark_line_separator_preserves_reference_label_identity(self):
        separators = (
            "\u000b",
            "\u000c",
            "\u001c",
            "\u001d",
            "\u001e",
            "\u0085",
            "\u2028",
            "\u2029",
        )
        for separator in separators:
            with self.subTest(separator=ascii(separator)):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    f"\n[x][Open{separator}SKILL\\.md]\n\n"
                    f"[Open{separator}SKILL\\.md]: /\n"
                )
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents, self.node_paths
                    ),
                )
    def test_unicode_space_does_not_make_invalid_inline_fallback_hidden(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            '\n[x](<https://x.test>\u00a0"Open")\n'
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

    def test_ascii_control_in_bare_link_destination_remains_visible(self):
        controls = tuple(chr(codepoint) for codepoint in range(1, 0x20)) + (
            "\x7f",
        )
        destinations = ("\x0bOpen&#32;SKILL\\.md",) + tuple(
            "a" + control + "Open&#32;SKILL\\.md"
            for control in controls
        )
        for destination in destinations:
            with self.subTest(destination=ascii(destination)):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    "\n[x]("
                    + destination
                    + ")"
                )
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents,
                            self.node_paths,
                        )
                    ),
                )

    def test_nul_and_angle_destination_controls_remain_hidden_metadata(self):
        cases = (
            "[x](a\x00Open&#32;SKILL\\.md)",
            "[x](<\x0bOpen&#32;SKILL\\.md>)",
            "[x](<\x7fOpen&#32;SKILL\\.md>)",
        )
        for markdown in cases:
            with self.subTest(markdown=ascii(markdown)):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += "\n" + markdown
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents,
                        self.node_paths,
                    ),
                )

    def test_unescaped_open_parenthesis_in_link_title_remains_visible(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\n[x](a (Open SKILL\\.md())"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents,
                self.node_paths,
            ),
        )

    def test_escaped_parenthesis_in_link_title_remains_hidden_metadata(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\n[x](a (Open SKILL\\.md\\())"
        )
        self.assertEqual(
            self.directives,
            support.discover_directives_from_documents(
                documents,
                self.node_paths,
            ),
        )

    def test_code_span_bracket_cannot_open_link_text(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\n`[`x](Open&#32;SKILL\\.md)"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents,
                self.node_paths,
            ),
        )

    def test_code_span_bracket_inside_link_text_remains_hidden_metadata(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\n[x `[`](Open&#32;SKILL\\.md)"
        )
        self.assertEqual(
            self.directives,
            support.discover_directives_from_documents(
                documents,
                self.node_paths,
            ),
        )

    def test_autolink_bracket_cannot_open_link_text(self):
        cases = (
            "<aa:[>](SKILL\\.md)",
            "<i><aa:[></i>](SKILL\\.md)",
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}"
                self.assert_contract_error(
                    "packaged Markdown reference visible-text drift",
                    lambda: support.discover_directives_from_documents(
                        documents,
                        self.node_paths,
                    ),
                )

    def test_nul_preprocessing_preserves_autolink_bracket_ownership(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += "\n<aa:\x00[>](SKILL\\.md)"
        self.assert_contract_error(
            "packaged Markdown reference visible-text drift",
            lambda: support.discover_directives_from_documents(
                documents,
                self.node_paths,
            ),
        )

    def test_autolink_brackets_inside_image_text_remain_hidden_metadata(self):
        cases = (
            "![<aa:[>](SKILL\\.md)",
            "![<aa:]>](SKILL\\.md)",
            "![<a@b.co>](SKILL\\.md)",
            "![<aa:\x00[>](SKILL\\.md)",
            "![<aa:\x00]>](SKILL\\.md)",
            "\\<aa:[>](SKILL\\.md)",
            "<a:[>](SKILL\\.md)",
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}"
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents,
                        self.node_paths,
                    ),
                )

    def test_non_punctuation_backslash_does_not_hide_inline_fallback(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += "\n[x](Open\\ now)\n"
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

    def test_nested_link_fallback_remains_visible(self):
        cases = (
            "[x [y](https://y.test)](Open)",
            "[x <https://y.test>](Open)",
            "[x <a@b.co>](Open)",
            "[x [y]](Open)\n\n[y]: /",
            "[x [y][]](Open)\n\n[y]: /",
            "# boundary\n\n[x][r]\n\n\t[r]: Open",
            "[x <i [y]>](Open)\n\n[y]: /",
            "[x </i [y]>](Open)\n\n[y]: /",
            "[x \<i title=\"[y]\">](Open)\n\n[y]: /",
            "[x ![[y](/)]](Open)",
            "# boundary\n\n[x\n\ny](Open)",
            "# boundary\n\n![x\n\ny](Open)",
            "[x <!--> [y] -->](Open)\n\n[y]: /",
            "# boundary\n\n[x\n# y](Open)",
            "# boundary\n\n[x\n---\ny](Open)",
            "# boundary\n\n[x\n- y](Open)",
            "# boundary\n\n[x\n===\ny](Open)",
            "[x [y][a b]](Open)\n\n[a\n b]: /",
            "[x](" + "(" * 33 + "Open" + ")" * 33 + ")",
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_reference_definition_cannot_interrupt_an_open_paragraph(self):
        cases = (
            "[x][a]\n[a]: Open&#32;harness-review\\.md",
            "> [x][a]\n> [a]: Open&#32;harness-review\\.md",
            "- [x][a]\n  [a]: Open&#32;harness-review\\.md",
            "- > [x][a]\n  > [a]: Open&#32;harness-review\\.md",
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_reference_definition_cannot_cross_a_structural_block_boundary(self):
        cases = (
            '[a]: / "Open&#32;harness-review\\.md\n# end"',
            "[a]: / 'Open&#32;harness-review\\.md\n***\nend'",
            "[a]: / (Open&#32;harness-review\\.md\n# end)",
            "[a\n---\nb]: Open&#32;harness-review\\.md",
            '[a]:\n-\n"Open&#32;harness-review\\.md"',
            '[a]:\n---\n"Open&#32;harness-review\\.md"',
            "[a\n# boundary\nb]: Open&#32;harness-review\\.md",
            '[a]: / "Open&#32;harness-review\\.md\n<!-- -->"',
            '[a]: / "Open&#32;harness-review\\.md\n   <!-- -->"',
            '[a]: / "Open&#32;harness-review\\.md\n<div>"',
            '> [a]: / "Open&#32;harness-review\\.md\n> # end"',
            '- [a]: / "Open&#32;harness-review\\.md\n  # end"',
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )
    def test_same_line_multiline_reference_title_closes_before_html(self):
        cases = (
            '[a]: / "title\n more"\n<custom>\n[x](Open)',
            '> [a]: / "title\n> more"\n> <custom>\n> [x](Open)',
            '- [a]: / "title\n  more"\n  <custom>\n  [x](Open)',
        )
        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )
    def test_valid_hidden_link_metadata_is_not_a_visible_instruction(self):
        cases = (
            '[x](https://example.invalid/ "Open <span></span>")',
            '[x]( "Open")',
            '[x][r]\n\n[r]: https://example.invalid/ "Open"',
            '[x][r]\n\n[r]: https://example.invalid/\n  "Open"',
            "[x][r]\n\n[r]: https://example.invalid/\n  (Open)",
            "[x][r]\n\n[r]:\n  Open",
            '[x][r]\n\n[r]: https://example.invalid/\n  "Open\n  more"',
            "[a\n b]: Open&#32;harness-review\\.md",
            "> [a\n> b]: Open&#32;harness-review\\.md",
            "- [a\n  b]: Open&#32;harness-review\\.md",
            "- > [a\n  > b]: Open&#32;harness-review\\.md",

            "[a\n middle\n b]: Open&#32;harness-review\\.md",
            '[a]: /\n    "Open&#32;harness-review\\.md"',
            '[a]: /\n\t"Open&#32;harness-review\\.md"',
            '> - [a]: /\n> "Open&#32;harness-review\\.md"',
            '[a]: / "Open&#32;harness-review\\.md\n===\nend"',
            '[a]:\n===\n"Open&#32;harness-review\\.md"',
            '[a]:\n--\n"Open&#32;harness-review\\.md"',
            '[a]: / "Open&#32;harness-review\\.md\n--\nend"',
            '[a\n--\n b]: Open&#32;harness-review\\.md',
            '> - [a]: / "Open&#32;harness-review\\.md\n> --\n> end"',
            '[a]: / "Open&#32;harness-review\\.md\n    <!-- --> more"',
            '[a]: / "Open&#32;harness-review\\.md\n\t<? x ?> more"',
            '[a\n    <!-- --> middle\n b]: Open&#32;harness-review\\.md',
            '[a]:\n    Open&#32;harness-review\\.md',
            '[a]:\n\tOpen&#32;harness-review\\.md',
            '[a]: / "Open\n    more"',
            '[a]: / "Open\n\tmore"',
            '> - [a]: / "Open\n> more"',
            '- [a]: / "Open\nmore"',
            '> p\n>\n> [a]: Open&#32;harness-review\\.md',
            '- > p\n  >\n  > [a]: Open&#32;harness-review\\.md',
            '[a]: / "Open\n more"',
            '> [a]: / "Open\n> more"',
            '- [a]: / "Open\n  more"',
            '- > [a]: / "Open\n  > more"',
            (
                "- > [a\n"
                "  > middle\n"
                "  > b]: Open&#32;harness-review\\.md"
            ),
            (
                "["
                + "a" * 498
                + "\n "
                + "b" * 499
                + "]: Open&#32;harness-review\\.md"
            ),
            "[x][oPeN]\n\n[OPEN]: https://example.invalid/",
            '[x][r]\n\n> [r]: https://example.invalid/ "Open"',
            '[x][r]\n\n- [r]: https://example.invalid/ "Open"',
            "[x][r]\n\n> ```\n[r]: Open",
            "[x][r]\n\n<div>\ny\n\n[r]: Open",
            (
                '[x][r]\n\n- item\n'
                '  - [r]: https://example.invalid/ "Open"'
            ),
            (
                'paragraph\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '- paragraph\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '> paragraph\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '- 1. [r]: https://example.invalid/ "Open"\n'
                '  [x][r]'
            ),
            (
                '- > 1. [r]: https://example.invalid/ "Open"\n'
                '  >   [x][r]'
            ),
            (
                'paragraph\n---abc\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                'paragraph\n***abc\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                'paragraph\n___abc\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                'paragraph\n--- abc\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\n=\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\nparagraph\n2. <custom>\n'
                '   [x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\nparagraph\n* \n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\nparagraph\n+ \n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\nparagraph\n1. \n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\n[z]: not valid title\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\n[z]: <unterminated\n<custom>\n'
                '[x](https://example.invalid/ "Open")'
            ),
            (
                '# boundary\n\n> paragraph\nlazy\n> <custom>\n'
                '> [x](https://example.invalid/ "Open")\n>'
            ),
            (
                '# boundary\n\n- > paragraph\nlazy\n  > <custom>\n'
                '  > [x](https://example.invalid/ "Open")\n  >'
            ),
            '- outer\n\n    [x](Open)',
            '- outer\n\n\n    [x](Open)',
            '- outer\n  - inner\n\n      [x](Open)',
            '1. outer\n   - inner\n\n       [x](Open)',
            '- > p\nlazy\n    > <custom>\n    > [x](Open)',
            '> - p\nlazy\n>   <custom>\n>   [x](Open)',
            '- > - p\nlazy\n  >   <custom>\n  >   [x](Open)',
            '[x ![y](i)](Open)',
            '[x `<https://y.test>`](Open)',
            '[x \<https://y.test>](Open)',
            '- outer\n\n\t[x](Open)',
            '-\touter\n\n\t[x](Open)',
            '1.\touter\n\n\t[x](Open)',
            '-\touter\n\t-\tinner\n\n\t\t[x](Open)',
            '-\t> p\nlazy\n\t> <custom>\n\t> [x](Open)',
            '[x ![y [z](/)](i)](Open)',
            '[x ![y [z](/)][img]](Open)\n\n[img]: i',
            '[x ![y [z]](i)](Open)\n\n[z]: /',
            '[x ![y <https://z.test>](i)](Open)',
            '[x [a&amp;b]](Open)\n\n[a&b]: /',
            '[x [a\\*b]](Open)\n\n[a*b]: /',
            '[x <span title="[y]">z</span>](Open)\n\n[y]: /',
            '[x <!-- <https://y.test> --> z](Open)',
            '[x <span title="<https://y.test>">z</span>](Open)',
            (
                '# boundary\n\n    `\n[x](Open)\n`'
            ),
            (
                '# boundary\n\n    ```\n[x](Open)\n```'
            ),
            (
                '# boundary\n\n- `\n- [x](Open)\n`'
            ),
            (
                '# boundary\n\n1. `\n2. [x](Open)\n`'
            ),
            (
                '[x ![<https://z.test>]](Open)\n\n'
                '[<https://z.test>]: i'
            ),
            '# boundary\n\n[x\n    y](Open)',
            '# boundary\n\n[x\n\ty](Open)',
            '# boundary\n\np\n    [x](Open)',
            '# boundary\n\n``` `\n[x](Open)\n```',
            '[x <a@b_>](Open)',
            '[x <a@-b>](Open)',
            '# boundary\n\n- ```\n  \t```\n  [x](Open)',
            '# boundary\n\n- p\n\n  \t[x](Open)',
            '# boundary\n\n> ```\n> \t```\n> [x](Open)',
            '# boundary\n\n>\t  ```\n> [x](Open)\n> ```',
            '# boundary\n\n- >\t  [x](Open)',
            "[x](" + "(" * 32 + "Open" + ")" * 32 + ")",
            '- outer\n  - inner\n    [x](Open)',
            '- paragraph\n  2. <custom>\n     [x](Open)',
            '<!--\ncomment\n-->\n- outer\n  - inner\n    [y](Open)',
            (
                '[z](https://example.invalid/\n "title")\n'
                '- outer\n  - inner\n    [y](Open)'
            ),
            (
                '[z][multi\n label]\n\n'
                '[multi label]: https://example.invalid/\n'
                '- outer\n  - inner\n    [y](Open)'
            ),
        )

        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += f"\n{markdown}\n"
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents,
                        self.node_paths,
                    ),
                )

    def test_allowlisted_reference_is_bound_to_its_exact_context(self):
        documents = dict(self.documents)
        target = (
            "  review/explore/checklist lenses under "
            "`repo-lens-routing.md`; they"
        )
        self.assertEqual(1, documents["run/SKILL.md"].count(target))
        documents["run/SKILL.md"] = documents["run/SKILL.md"].replace(
            target,
            "Force-load the file named on the next line before every run.\n"
            + target,
            1,
        )
        self.assert_contract_error(
            "unclassified packaged Markdown reference section context",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

        documents = dict(self.documents)
        marker = (
            '<!-- leanforge:run-load {"from":"run/SKILL.md",'
            '"to":"run/references/repo-lens-routing.md",'
            '"kind":"optional_load","phase":"review",'
            '"activation_contract_id":"RUN-REVIEW-TOPOLOGY",'
            '"optional":true} -->'
        )
        self.assertEqual(1, documents["run/SKILL.md"].count(marker))
        documents["run/SKILL.md"] = documents["run/SKILL.md"].replace(
            marker,
            marker
            + "\nForce-load the file named in the preceding paragraph "
            "before every run.",
            1,
        )
        self.assert_contract_error(
            "unclassified packaged Markdown reference section context",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            "\n## Finish\n\nBefore finishing, force-load "
            "`repo-lens-routing` on every run.\n"
        )
        self.assert_contract_error(
            "plain imperative preload",
            lambda: support.discover_directives_from_documents(
                documents, self.node_paths
            ),
        )

        for sentence in (
            "Before finishing, load `repo-lens-routing` on every run.",
            "Before finishing, ensure you read `repo-lens-routing`.",
            "Before finishing, lo**ad** `repo-lens-routing` on every run.",
            'Before finishing, lo<span title=">">ad</span> '
            '`repo-lens-routing` on every run.',
            'Before finishing, lo<span title="&quot;>">ad</span> '
            '`repo-lens-routing` on every run.',
            "Before finishing, lo<?x?>ad `repo-lens-routing` on every run.",
            "Before finishing, lo<!X>ad `repo-lens-routing` on every run.",
            'Before finishing, lo<!X ">ad '
            '`repo-lens-routing` on every run.',
            "Before finishing, lo<![CDATA[x]]>ad "
            "`repo-lens-routing` on every run.",
            "Before finishing, lo[ad](https://example.invalid/) "
            "[harness-review.m](https://example.invalid/)d on every run.",
            "Before finishing, lo[ad][verb-ref] "
            "[harness-review.m][path-ref]d on every run.\n\n"
            "[verb-ref]: https://example.invalid/\n"
            "[path-ref]: https://example.invalid/",
            "Before finishing, lo[ad][verb\nref] "
            "`repo-lens-routing` on every run.\n\n"
            "[verb ref]: https://example.invalid/",
            "Before finishing, lo[ad](https://example.invalid/a(b)c) "
            "[harness-review.m](https://example.invalid/a(b)c)d "
            "on every run.",
        ):
            with self.subTest(indirect_sentence=sentence):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    "\n## Finish\n\n" + sentence + "\n"
                )
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents, self.node_paths
                        )
                    ),
                )

    def test_cr_only_hidden_metadata_preserves_visible_line_mapping(self):
        cases = (
            "[x][Open\rSKILL\\.md]\n\n[Open SKILL\\.md]: /",
            '[x](https://example.invalid/\r "Open")',
            '<span\r title="Open">x</span>',
        )

        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    "\n# CR Probe\n\n" + markdown + "\n"
                )
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents,
                        self.node_paths,
                    ),
                )

    def test_crlf_inline_metadata_preserves_visible_line_mapping(self):
        documents = dict(self.documents)
        documents["run/SKILL.md"] += (
            '\n# CRLF Probe\n\n'
            '[x](https://example.invalid/\r\n "Open")\n'
        )

        self.assertEqual(
            self.directives,
            support.discover_directives_from_documents(
                documents,
                self.node_paths,
            ),
        )

    def test_multiline_hidden_metadata_at_eof_preserves_line_mapping(self):
        cases = (
            '[x](https://example.invalid/\n "Open")',
            '[Open SKILL\\.md]: /\n\n[x][Open\nSKILL\\.md]',
            '<span\n title="Open">',
        )

        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += (
                    "\n# EOF Probe\n\n" + markdown
                )
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents,
                        self.node_paths,
                    ),
                )

    def test_link_metadata_cannot_cross_commonmark_block_boundary(self):
        cases = (
            '[x](/ "\n- Open SKILL\\.md")',
            (
                '[Open - SKILL\\.md]: /\n\n'
                '[x][Open\n- SKILL\\.md]'
            ),
            (
                '[Open SKILL\\.md]: /\n\n'
                '[x][Open\n2. SKILL\\.md]'
            ),
            (
                '[Open SKILL\\.md]: /\n\n'
                '![x][Open\n2. SKILL\\.md]'
            ),
            (
                '[Open 2. a SKILL\\.md]: /\n\n'
                '[x][Open\n2. a\n2. SKILL\\.md]'
            ),
            (
                '[Open 2. a SKILL\\.md]: /\n\n'
                '![x][Open\n2. a\n2. SKILL\\.md]'
            ),
            (
                '[Open - SKILL\\.md]: /\n\n'
                '[x][Open\n-\nSKILL\\.md]'
            ),
            (
                '[Open - SKILL\\.md]: /\n\n'
                '![x][Open\n-\nSKILL\\.md]'
            ),
        )

        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += "\n" + markdown
                self.assert_contract_error(
                    "plain imperative preload",
                    lambda documents=documents: (
                        support.discover_directives_from_documents(
                            documents,
                            self.node_paths,
                        )
                    ),
                )

    def test_same_paragraph_container_prefixes_keep_metadata_hidden(self):
        cases = (
            '> [x](/\n> "Open")',
            '> > [x](/\n> > "Open")',
            '- > [x](/\n  > "Open")',
            '> - [x](/ "hidden\n> Open")',
            (
                '[Open SKILL\\.md]: /\n\n'
                '> [x][Open\n> SKILL\\.md]'
            ),
            (
                '[Open 2. a 2. SKILL\\.md]: /\n\n'
                '[x][Open\n2. a\n2. SKILL\\.md]'
            ),
        )

        for markdown in cases:
            with self.subTest(markdown=markdown):
                documents = dict(self.documents)
                documents["run/SKILL.md"] += "\n" + markdown
                self.assertEqual(
                    self.directives,
                    support.discover_directives_from_documents(
                        documents,
                        self.node_paths,
                    ),
                )

    def test_reference_labels_normalize_single_line_breaks(self):
        source = (
            "Before finishing, lo[ad][verb\nref] "
            "`repo-lens-routing` on every run.\n\n"
            "[verb ref]: https://example.invalid/"
        )
        normalized = support.normalize_markdown_visible_text(source)
        self.assertRegex(
            normalized,
            r"(?i)\bload\s+repo-lens-routing\b",
        )

    def test_codex_default_prompt_rejects_hidden_loads_and_generated_drift(self):
        cases = (
            ("hidden packaged Markdown load", "plain"),
            ("hidden packaged Markdown load", "escaped"),
            ("direct child of top-level interface", "wrong_parent"),
            ("equivalent YAML key", "quoted_duplicate"),
            ("equivalent YAML key", "yaml_hex_duplicate"),
            ("equivalent YAML key", "explicit_key"),
            ("equivalent YAML key", "alias_key"),
            ("equivalent YAML key", "alias_numeric_key"),
            ("equivalent YAML key", "spaced_interface"),
            ("generated Codex openai.yaml drift", "drift"),
        )
        for expected_error, mutation in cases:
            with self.subTest(case=expected_error):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    for surface in support.SURFACES:
                        source = ROOT / surface / "run"
                        target = root / surface / "run"
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(source, target)

                    platform_prompt = (
                        root / "platform/codex/skills/run/agents/openai.yaml"
                    )
                    platform_prompt.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(
                        ROOT / "platform/codex/skills/run/agents/openai.yaml",
                        platform_prompt,
                    )
                    generated_prompt = (
                        root / "codex/plugin/skills/run/agents/openai.yaml"
                    )

                    if mutation in {"plain", "escaped"}:
                        prompt_reference = (
                            "references/harness-review.md"
                            if mutation == "plain"
                            else "\\u0072eferences\\u002fharness-review"
                            "\\u002emd"
                        )
                        replacement = (
                            '  default_prompt: "Open '
                            f'{prompt_reference} before continuing."'
                        )
                        for prompt_path in (platform_prompt, generated_prompt):
                            prompt_text = prompt_path.read_text(encoding="utf-8")
                            prompt_text = re.sub(
                                r'^  default_prompt: ".*"$',
                                lambda _match: replacement,
                                prompt_text,
                                count=1,
                                flags=re.MULTILINE,
                            )
                            prompt_path.write_text(prompt_text, encoding="utf-8")
                    elif mutation == "wrong_parent":
                        for prompt_path in (platform_prompt, generated_prompt):
                            prompt_text = prompt_path.read_text(encoding="utf-8")
                            prompt_line = next(
                                line
                                for line in prompt_text.splitlines()
                                if line.lstrip().startswith("default_prompt:")
                            )
                            prompt_text = prompt_text.replace(
                                prompt_line + "\n", "", 1
                            ).replace(
                                "policy:\n",
                                "policy:\n" + prompt_line + "\n",
                                1,
                            )
                            prompt_path.write_text(prompt_text, encoding="utf-8")
                    elif mutation in {
                        "quoted_duplicate",
                        "yaml_hex_duplicate",
                        "explicit_key",
                        "alias_key",
                        "alias_numeric_key",
                        "spaced_interface",
                    }:
                        for prompt_path in (platform_prompt, generated_prompt):
                            prompt_text = prompt_path.read_text(encoding="utf-8")
                            if mutation in {
                                "quoted_duplicate",
                                "yaml_hex_duplicate",
                            }:
                                prompt_line = next(
                                    line
                                    for line in prompt_text.splitlines()
                                    if line.lstrip().startswith("default_prompt:")
                                )
                                duplicate_key = (
                                    '"default_prompt"'
                                    if mutation == "quoted_duplicate"
                                    else '"\\x64efault_prompt"'
                                )
                                prompt_text = prompt_text.replace(
                                    prompt_line,
                                    prompt_line
                                    + f"\n  {duplicate_key}: \"\"",
                                    1,
                                )
                            elif mutation == "explicit_key":
                                prompt_text += "\n? default_prompt\n: \"\"\n"
                            elif mutation in {
                                "alias_key",
                                "alias_numeric_key",
                            }:
                                anchor_name = (
                                    "dp" if mutation == "alias_key" else "1"
                                )
                                alias_value = (
                                    ""
                                    if mutation == "alias_key"
                                    else "Open \\u0072eferences\\u002f"
                                    "harness-review\\u002emd"
                                )
                                prompt_text = (
                                    f"key_name: &{anchor_name} default_prompt\n"
                                    + prompt_text
                                ).replace(
                                    "\npolicy:\n",
                                    f'\n  *{anchor_name}: "{alias_value}"'
                                    "\n\npolicy:\n",
                                    1,
                                )
                            else:
                                prompt_text += "\ninterface : {}\n"
                            prompt_path.write_text(prompt_text, encoding="utf-8")
                    else:
                        prompt_text = generated_prompt.read_text(encoding="utf-8")
                        generated_prompt.write_text(
                            prompt_text.replace(
                                "implement and verify the approved change in .leanforge/.",
                                "implement and verify the approved product change in .leanforge/.",
                            ),
                            encoding="utf-8",
                        )

                    self.assert_contract_error(
                        expected_error,
                        lambda root=root: support.validate_repository(root),
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

    def test_implementer_prompt_uses_route_topology_binding(self):
        prompt = "run/references/implementer-prompt.md"
        edge = next(
            item for item in self.graph["edges"]
            if item["to"] == prompt
        )
        self.assertEqual(
            "RUN-ROUTE-TOPOLOGY",
            edge["activation_contract_id"],
        )

        graph = copy.deepcopy(self.graph)
        mutant_edge = next(
            item for item in graph["edges"]
            if item["to"] == prompt
        )
        mutant_edge["activation_contract_id"] = "RUN-FAIL-CLOSED"
        directives = copy.deepcopy(self.directives)
        mutant_directive = next(
            item for item in directives
            if item["to"] == prompt
        )
        mutant_directive["activation_contract_id"] = "RUN-FAIL-CLOSED"
        self.assert_contract_error(
            "unsupported load edge binding",
            lambda: self.validate(graph, directives=directives),
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

    def test_harness_changed_repo_lens_profile_composes_both_optional_edges(self):
        default = self.closure()
        combined = self.closure(profile="harness_changed_repo_lens")
        self.assertEqual(
            {
                "run/references/harness-review.md",
                "run/references/repo-lens-routing.md",
            },
            set(combined["instruction_nodes"])
            - set(default["instruction_nodes"]),
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

    def test_read_only_hash_covers_canonical_and_both_generated_run_surfaces(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            fixture_target = temporary_root / support.FIXTURE_RELATIVE_PATH
            fixture_target.parent.mkdir(parents=True)
            shutil.copy2(FIXTURE_PATH, fixture_target)
            for relative in (
                "src/skills/run",
                "claude/skills/run",
                "codex/plugin/skills/run",
            ):
                shutil.copytree(ROOT / relative, temporary_root / relative)

            baseline = support.scoped_product_hash(temporary_root)
            for relative in (
                "src/skills/run/references/orchestration.md",
                "claude/skills/run/references/orchestration.md",
                "codex/plugin/skills/run/references/orchestration.md",
            ):
                with self.subTest(relative=relative):
                    target = temporary_root / relative
                    original = target.read_bytes()
                    target.write_bytes(original + b"\nread-only-hash-mutation\n")
                    self.assertNotEqual(
                        baseline,
                        support.scoped_product_hash(temporary_root),
                    )
                    target.write_bytes(original)

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
