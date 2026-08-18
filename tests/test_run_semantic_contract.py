import copy
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "src/skills/run/references/semantic-contract.json"
FIXTURE_PATH = ROOT / "tests/fixtures/run_semantic_scenarios_v1_9_0.json"
MARKDOWN_PATHS = (
    ROOT / "src/skills/run/SKILL.md",
    ROOT / "src/skills/run/references/orchestration.md",
    ROOT / "src/skills/run/references/harness-lifecycle.md",
)
TOP_LEVEL_KEYS = {"schema_version", "contract_id", "vocabulary", "invariants"}
ASSERTION_OPS = {"count", "forbid", "before", "same", "owner"}
EXPECTED_INVARIANT_KINDS = {
    "RUN-ROUTE-TOPOLOGY": "route_topology",
    "RUN-EXTERNAL-PROOF": "external_proof",
    "RUN-FAIL-CLOSED": "failure_overlay",
    "RUN-COMPLETION-REUSE": "completion_reuse",
    "RUN-CONCERN-DISPOSITION": "concern_disposition",
    "RUN-LIFECYCLE-OWNERSHIP": "lifecycle_ownership",
    "RUN-REVIEW-TOPOLOGY": "review_topology",
    "RUN-OUTPUT-SEMANTICS": "output_semantics",
}
EXPECTED_VOCABULARY = {
    "route": ["direct", "single_risky", "parallel", "external"],
    "overlay": ["failure"],
    "outcome": ["green", "non_green", "unevaluable", "clear", "blocking"],
    "disposition": [
        "resolved",
        "explicitly_accepted",
        "user_accepted",
        "promoted_to_failure",
        "pending",
    ],
    "owner": [
        "orchestrator",
        "implementer",
        "harness_lifecycle",
        "runtime_failure_overlay",
        "user",
    ],
    "event": [
        "route_selected",
        "worktree_created",
        "isolated_task_worktrees",
        "task_implementation",
        "task_verification",
        "task_verifications_complete",
        "evidence_captured",
        "merge_precondition",
        "merge_gate",
        "merge_gates_complete",
        "serial_merge",
        "task_merged",
        "regeneration",
        "wiring",
        "integration_gate",
        "external_action",
        "external_evidence",
        "base_commit",
        "conditional_base_commit",
        "independent_commit_proof",
        "failure_overlay_entered",
        "retry",
        "cleanup",
        "downstream_dispatch",
        "progress",
        "completion_gate",
        "runtime_result",
        "review_result",
        "prior_integration",
        "prior_verify_set",
        "current_verify_set",
        "prior_gate_base_tip",
        "current_base_tip",
        "verify_set_changed",
        "base_tip_changed",
        "completion_reused",
        "completion_full_verify",
        "concern_recorded",
        "user_owned_requirement_concern",
        "user_owned_compatibility_concern",
        "user_owned_safety_concern",
        "concern_disposition",
        "completion",
        "user_gate",
        "startup",
        "interrupted_run",
        "archive",
        "migration",
        "runtime_task_failure",
        "runtime_gate_failure",
        "runtime_review_failure",
        "risky_task",
        "non_risky_task",
        "downstream_cascade_risk",
        "no_downstream_cascade_risk",
        "conditional_spec_review",
        "final_full_diff_review",
        "review_verdict",
        "blocking_finding",
        "routine_read",
        "routine_write",
        "routine_dispatch",
        "routine_merge",
        "routine_gate",
        "routine_cleanup",
        "user_output_needed_question",
        "user_output_actual_blocker",
        "user_output_wave_completion",
        "user_output_final_result",
        "user_output_approval_request",
    ],
    "invariant_kind": list(EXPECTED_INVARIANT_KINDS.values()),
}
EXPECTED_CARDINALITY = {
    "RUN-ROUTE-TOPOLOGY": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 4,
        "mutations": 2,
    },
    "RUN-EXTERNAL-PROOF": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 1,
        "mutations": 2,
    },
    "RUN-FAIL-CLOSED": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 14,
        "mutations": 1,
    },
    "RUN-COMPLETION-REUSE": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 5,
        "mutations": 2,
    },
    "RUN-CONCERN-DISPOSITION": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 7,
        "mutations": 2,
    },
    "RUN-LIFECYCLE-OWNERSHIP": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 1,
        "mutations": 1,
    },
    "RUN-REVIEW-TOPOLOGY": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 3,
        "mutations": 1,
    },
    "RUN-OUTPUT-SEMANTICS": {
        "definitions": 1,
        "blocks": 1,
        "scenarios": 2,
        "mutations": 1,
    },
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_exact_keys(value, expected, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    actual = set(value)
    if actual != set(expected):
        raise ValueError(
            f"{label} keys must be {sorted(expected)}, got {sorted(actual)}"
        )


def validate_selector(selector, vocabulary, label):
    if not isinstance(selector, dict):
        raise ValueError(f"{label} must be an object")
    allowed = {"event", "route", "overlay", "outcome", "disposition"}
    if "event" not in selector or not set(selector).issubset(allowed):
        raise ValueError(f"{label} has unknown keys or lacks event")
    if selector["event"] not in vocabulary["event"]:
        raise ValueError(f"{label} references unknown event {selector['event']!r}")
    for enum_name in ("route", "overlay", "outcome", "disposition"):
        if enum_name in selector and selector[enum_name] not in vocabulary[enum_name]:
            raise ValueError(
                f"{label} references unknown {enum_name} {selector[enum_name]!r}"
            )


def validate_assertion(assertion, vocabulary, label, contract_rule):
    if not isinstance(assertion, dict):
        raise ValueError(f"{label} must be an object")
    op = assertion.get("op")
    if op not in ASSERTION_OPS:
        raise ValueError(f"{label} has unknown assertion op {op!r}")
    reason_keys = {"reason"} if contract_rule else set()
    expected = {
        "count": {"op", "target", "equals"} | reason_keys,
        "forbid": {"op", "target"} | reason_keys,
        "before": {"op", "first", "second"} | reason_keys,
        "same": {"op", "first", "second", "field"} | reason_keys,
        "owner": {"op", "target", "equals"} | reason_keys,
    }[op]
    require_exact_keys(assertion, expected, label)
    if contract_rule and (
        not isinstance(assertion["reason"], str) or not assertion["reason"]
    ):
        raise ValueError(f"{label}.reason must be a non-empty string")
    if op in {"count", "forbid", "owner"}:
        validate_selector(assertion["target"], vocabulary, f"{label}.target")
    if op in {"before", "same"}:
        validate_selector(assertion["first"], vocabulary, f"{label}.first")
        validate_selector(assertion["second"], vocabulary, f"{label}.second")
    if op == "count" and (
        type(assertion["equals"]) is not int or assertion["equals"] < 0
    ):
        raise ValueError(f"{label}.equals must be a non-negative integer")
    if op == "same" and assertion["field"] != "value":
        raise ValueError(f"{label}.field must be 'value'")
    if op == "owner" and assertion["equals"] not in vocabulary["owner"]:
        raise ValueError(f"{label} references unknown owner {assertion['equals']!r}")


def validate_contract(contract):
    require_exact_keys(contract, TOP_LEVEL_KEYS, "contract")
    if type(contract["schema_version"]) is not int or contract["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    if contract["contract_id"] != "leanforge.run.semantics":
        raise ValueError("contract_id must be 'leanforge.run.semantics'")
    require_exact_keys(
        contract["vocabulary"], EXPECTED_VOCABULARY, "vocabulary"
    )
    if contract["vocabulary"] != EXPECTED_VOCABULARY:
        raise ValueError("vocabulary enums must exactly match the closed vocabulary")

    invariants = contract["invariants"]
    if not isinstance(invariants, list):
        raise ValueError("invariants must be an array")
    if [item.get("id") for item in invariants] != list(EXPECTED_INVARIANT_KINDS):
        raise ValueError("invariant IDs must exactly match the protected stable IDs")

    for index, invariant in enumerate(invariants):
        label = f"invariants[{index}]"
        require_exact_keys(invariant, {"id", "kind", "definition", "cases"}, label)
        invariant_id = invariant["id"]
        if invariant["kind"] != EXPECTED_INVARIANT_KINDS[invariant_id]:
            raise ValueError(f"{label} has the wrong invariant kind")
        if not isinstance(invariant["definition"], str) or not invariant["definition"]:
            raise ValueError(f"{label}.definition must be one non-empty string")
        if not isinstance(invariant["cases"], list) or not invariant["cases"]:
            raise ValueError(f"{label}.cases must be a non-empty array")
        seen_cases = set()
        for case_index, contract_case in enumerate(invariant["cases"]):
            case_label = f"{label}.cases[{case_index}]"
            require_exact_keys(contract_case, {"name", "assertions"}, case_label)
            if (
                not isinstance(contract_case["name"], str)
                or not contract_case["name"]
                or contract_case["name"] in seen_cases
            ):
                raise ValueError(f"{case_label}.name must be non-empty and unique")
            seen_cases.add(contract_case["name"])
            if (
                not isinstance(contract_case["assertions"], list)
                or not contract_case["assertions"]
            ):
                raise ValueError(f"{case_label}.assertions must be non-empty")
            for rule_index, assertion in enumerate(contract_case["assertions"]):
                validate_assertion(
                    assertion,
                    contract["vocabulary"],
                    f"{case_label}.assertions[{rule_index}]",
                    contract_rule=True,
                )


def validate_trace(trace, vocabulary, label):
    if not isinstance(trace, list):
        raise ValueError(f"{label} must be an array")
    for index, occurrence in enumerate(trace):
        occurrence_label = f"{label}[{index}]"
        if not isinstance(occurrence, dict):
            raise ValueError(f"{occurrence_label} must be an object")
        allowed = {
            "event",
            "owner",
            "route",
            "overlay",
            "outcome",
            "disposition",
            "value",
        }
        if "event" not in occurrence or not set(occurrence).issubset(allowed):
            raise ValueError(f"{occurrence_label} has unknown keys or lacks event")
        if occurrence["event"] not in vocabulary["event"]:
            raise ValueError(
                f"{occurrence_label} has unknown event {occurrence['event']!r}"
            )
        if "owner" in occurrence and occurrence["owner"] not in vocabulary["owner"]:
            raise ValueError(f"{occurrence_label} has unknown owner")
        for enum_name in ("route", "overlay", "outcome", "disposition"):
            if (
                enum_name in occurrence
                and occurrence[enum_name] not in vocabulary[enum_name]
            ):
                raise ValueError(f"{occurrence_label} has unknown {enum_name}")
        if "value" in occurrence and not isinstance(occurrence["value"], str):
            raise ValueError(f"{occurrence_label}.value must be a string")


def invariant_case_map(contract):
    return {
        invariant["id"]: {item["name"]: item for item in invariant["cases"]}
        for invariant in contract["invariants"]
    }


def validate_fixture(fixture, contract):
    require_exact_keys(
        fixture,
        {
            "schema_version",
            "behavior_origin_commit",
            "assertion_language",
            "cardinality",
            "scenarios",
            "mutants",
        },
        "fixture",
    )
    if type(fixture["schema_version"]) is not int or fixture["schema_version"] != 1:
        raise ValueError("fixture schema_version must be integer 1")
    if fixture["behavior_origin_commit"] != (
        "fb252b4236cc607002e131210f6161db72f6841e"
    ):
        raise ValueError("fixture behavior_origin_commit is not protected v1.8.1")
    if fixture["assertion_language"] != [
        "count",
        "forbid",
        "before",
        "same",
        "owner",
    ]:
        raise ValueError("fixture assertion_language is not the closed language")
    if fixture["cardinality"] != EXPECTED_CARDINALITY:
        raise ValueError("fixture cardinality must match the hand-authored values")

    cases = invariant_case_map(contract)
    seen_item_ids = set()
    for collection_name, expected_keys in (
        ("scenarios", {"id", "contracts", "trace", "assertions"}),
        (
            "mutants",
            {
                "id",
                "contracts",
                "trace",
                "assertions",
                "expected_contract_id",
                "expected_reason",
            },
        ),
    ):
        collection = fixture[collection_name]
        if not isinstance(collection, list):
            raise ValueError(f"fixture.{collection_name} must be an array")
        for index, item in enumerate(collection):
            label = f"{collection_name}[{index}]"
            require_exact_keys(item, expected_keys, label)
            if (
                not isinstance(item["id"], str)
                or not item["id"]
                or item["id"] in seen_item_ids
            ):
                raise ValueError(f"{label}.id must be non-empty and unique")
            seen_item_ids.add(item["id"])
            if not isinstance(item["contracts"], list) or not item["contracts"]:
                raise ValueError(f"{label}.contracts must be a non-empty array")
            seen_refs = set()
            referenced_reasons = set()
            for ref_index, contract_ref in enumerate(item["contracts"]):
                ref_label = f"{label}.contracts[{ref_index}]"
                require_exact_keys(contract_ref, {"id", "case"}, ref_label)
                pair = (contract_ref["id"], contract_ref["case"])
                if pair in seen_refs:
                    raise ValueError(f"{ref_label} is duplicated")
                seen_refs.add(pair)
                if contract_ref["id"] not in cases:
                    raise ValueError(f"{ref_label} has unknown invariant")
                if contract_ref["case"] not in cases[contract_ref["id"]]:
                    raise ValueError(f"{ref_label} has unknown case")
                referenced_reasons.update(
                    assertion["reason"]
                    for assertion in cases[contract_ref["id"]][
                        contract_ref["case"]
                    ]["assertions"]
                )
            validate_trace(item["trace"], contract["vocabulary"], f"{label}.trace")
            if not isinstance(item["assertions"], list) or not item["assertions"]:
                raise ValueError(f"{label}.assertions must be non-empty")
            for assertion_index, assertion in enumerate(item["assertions"]):
                validate_assertion(
                    assertion,
                    contract["vocabulary"],
                    f"{label}.assertions[{assertion_index}]",
                    contract_rule=False,
                )
            if collection_name == "mutants":
                if item["expected_contract_id"] not in {
                    contract_ref["id"] for contract_ref in item["contracts"]
                }:
                    raise ValueError(f"{label} expects an unreferenced invariant")
                if item["expected_reason"] not in referenced_reasons:
                    raise ValueError(f"{label}.expected_reason is not a closed reason")


def matching_indexes(trace, selector):
    return [
        index
        for index, occurrence in enumerate(trace)
        if all(occurrence.get(key) == value for key, value in selector.items())
    ]


def evaluate_assertion(trace, assertion):
    op = assertion["op"]
    if op in {"count", "forbid", "owner"}:
        indexes = matching_indexes(trace, assertion["target"])
    if op == "count":
        return len(indexes) == assertion["equals"]
    if op == "forbid":
        return not indexes
    if op == "before":
        first = matching_indexes(trace, assertion["first"])
        second = matching_indexes(trace, assertion["second"])
        return bool(first and second) and max(first) < min(second)
    if op == "same":
        first = matching_indexes(trace, assertion["first"])
        second = matching_indexes(trace, assertion["second"])
        field = assertion["field"]
        return (
            len(first) == 1
            and len(second) == 1
            and trace[first[0]].get(field) == trace[second[0]].get(field)
        )
    if op == "owner":
        return bool(indexes) and all(
            trace[index].get("owner") == assertion["equals"] for index in indexes
        )
    raise AssertionError(f"unreachable assertion op {op!r}")


def validate_against_contract(contract, item):
    cases = invariant_case_map(contract)
    for contract_ref in item["contracts"]:
        contract_case = cases[contract_ref["id"]][contract_ref["case"]]
        for assertion in contract_case["assertions"]:
            if not evaluate_assertion(item["trace"], assertion):
                return contract_ref["id"], assertion["reason"]
    return None


def render_protected_block(invariant):
    projection = {key: invariant[key] for key in ("id", "kind", "definition")}
    invariant_json = json.dumps(projection, ensure_ascii=False, indent=2)
    invariant_id = invariant["id"]
    return (
        f"<!-- leanforge:run-semantic:{invariant_id}:start -->\n"
        "```json\n"
        f"{invariant_json}\n"
        "```\n"
        f"<!-- leanforge:run-semantic:{invariant_id}:end -->"
    )


def assertion_without_reason(assertion):
    return {key: value for key, value in assertion.items() if key != "reason"}


class RunSemanticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_json(CONTRACT_PATH)
        validate_contract(cls.contract)
        cls.fixture = load_json(FIXTURE_PATH)
        validate_fixture(cls.fixture, cls.contract)

    def test_hand_authored_behavior_scenarios(self):
        for scenario in self.fixture["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                for assertion in scenario["assertions"]:
                    self.assertTrue(
                        evaluate_assertion(scenario["trace"], assertion),
                        f"hand-authored expectation failed: {assertion}",
                    )
                self.assertIsNone(validate_against_contract(self.contract, scenario))

    def test_known_opposite_mutants_fail_with_exact_reason(self):
        survivors = []
        for mutant in self.fixture["mutants"]:
            with self.subTest(mutant=mutant["id"]):
                for assertion in mutant["assertions"]:
                    self.assertTrue(
                        evaluate_assertion(mutant["trace"], assertion),
                        f"mutant setup expectation failed: {assertion}",
                    )
                failure = validate_against_contract(self.contract, mutant)
                if failure is None:
                    survivors.append(mutant["id"])
                self.assertEqual(
                    failure,
                    (mutant["expected_contract_id"], mutant["expected_reason"]),
                )
        self.assertEqual(survivors, [], f"surviving mutants: {survivors}")

    def test_definition_block_scenario_mutation_cardinality(self):
        combined_markdown = "\n".join(
            path.read_text(encoding="utf-8") for path in MARKDOWN_PATHS
        )
        invariants = {
            invariant["id"]: invariant for invariant in self.contract["invariants"]
        }
        marker_ids = re.findall(
            r"<!-- leanforge:run-semantic:([^:]+):start -->",
            combined_markdown,
        )
        self.assertEqual(sorted(marker_ids), sorted(EXPECTED_INVARIANT_KINDS))

        for invariant_id, expected in EXPECTED_CARDINALITY.items():
            with self.subTest(invariant=invariant_id):
                self.assertEqual(
                    sum(
                        item["id"] == invariant_id
                        for item in self.contract["invariants"]
                    ),
                    expected["definitions"],
                )
                marker = re.compile(
                    rf"(?ms)<!-- leanforge:run-semantic:{re.escape(invariant_id)}:"
                    rf"start -->.*?<!-- leanforge:run-semantic:"
                    rf"{re.escape(invariant_id)}:end -->"
                )
                blocks = marker.findall(combined_markdown)
                self.assertEqual(len(blocks), expected["blocks"])
                self.assertEqual(
                    blocks[0], render_protected_block(invariants[invariant_id])
                )
                scenario_count = sum(
                    any(
                        contract_ref["id"] == invariant_id
                        for contract_ref in scenario["contracts"]
                    )
                    for scenario in self.fixture["scenarios"]
                )
                mutation_count = sum(
                    any(
                        contract_ref["id"] == invariant_id
                        for contract_ref in mutant["contracts"]
                    )
                    for mutant in self.fixture["mutants"]
                )
                self.assertEqual(scenario_count, expected["scenarios"])
                self.assertEqual(mutation_count, expected["mutations"])

    def test_every_case_has_independent_scenario_coverage(self):
        expected_pairs = {
            (invariant["id"], contract_case["name"])
            for invariant in self.contract["invariants"]
            for contract_case in invariant["cases"]
        }
        covered_pairs = {
            (contract_ref["id"], contract_ref["case"])
            for scenario in self.fixture["scenarios"]
            for contract_ref in scenario["contracts"]
        }
        self.assertEqual(covered_pairs, expected_pairs)

        cases = invariant_case_map(self.contract)
        for scenario in self.fixture["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                canonical_assertions = [
                    assertion_without_reason(assertion)
                    for contract_ref in scenario["contracts"]
                    for assertion in cases[contract_ref["id"]][
                        contract_ref["case"]
                    ]["assertions"]
                ]
                self.assertNotEqual(
                    scenario["assertions"],
                    canonical_assertions,
                    "scenario expectations must not be copied from contract rules",
                )

    def test_contract_schema_fails_closed(self):
        mutations = []

        unknown_top_level = copy.deepcopy(self.contract)
        unknown_top_level["extensions"] = {}
        mutations.append(("unknown top-level key", unknown_top_level))

        unknown_vocabulary_key = copy.deepcopy(self.contract)
        unknown_vocabulary_key["vocabulary"]["host"] = ["example"]
        mutations.append(("unknown vocabulary key", unknown_vocabulary_key))

        unknown_enum = copy.deepcopy(self.contract)
        unknown_enum["vocabulary"]["route"].append("fallback")
        mutations.append(("unknown enum", unknown_enum))

        unknown_kind = copy.deepcopy(self.contract)
        unknown_kind["invariants"][0]["kind"] = "fallback"
        mutations.append(("unknown invariant kind", unknown_kind))

        unknown_invariant_key = copy.deepcopy(self.contract)
        unknown_invariant_key["invariants"][0]["expression"] = "true"
        mutations.append(("unknown invariant key", unknown_invariant_key))

        unknown_assertion_event = copy.deepcopy(self.contract)
        unknown_assertion_event["invariants"][0]["cases"][0]["assertions"][0][
            "target"
        ]["event"] = "unknown_event"
        mutations.append(("unknown assertion reference", unknown_assertion_event))

        for label, mutation in mutations:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    validate_contract(mutation)

    def test_fixture_schema_fails_closed(self):
        mutations = []

        unknown_invariant = copy.deepcopy(self.fixture)
        unknown_invariant["scenarios"][0]["contracts"][0]["id"] = "RUN-UNKNOWN"
        mutations.append(("unknown invariant reference", unknown_invariant))

        unknown_case = copy.deepcopy(self.fixture)
        unknown_case["scenarios"][0]["contracts"][0]["case"] = "fallback"
        mutations.append(("unknown case reference", unknown_case))

        unknown_event = copy.deepcopy(self.fixture)
        unknown_event["scenarios"][0]["trace"][0]["event"] = "unknown_event"
        mutations.append(("unknown event", unknown_event))

        unknown_disposition = copy.deepcopy(self.fixture)
        unknown_disposition["scenarios"][23]["trace"][1][
            "disposition"
        ] = "ignored"
        mutations.append(("unknown disposition", unknown_disposition))

        unknown_assertion = copy.deepcopy(self.fixture)
        unknown_assertion["scenarios"][0]["assertions"][0]["op"] = "unless"
        mutations.append(("unknown assertion op", unknown_assertion))

        unknown_item_key = copy.deepcopy(self.fixture)
        unknown_item_key["mutants"][0]["survived"] = False
        mutations.append(("unknown mutant key", unknown_item_key))

        for label, mutation in mutations:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    validate_fixture(mutation, self.contract)

    def test_contract_has_no_forbidden_extension_surfaces(self):
        serialized = json.dumps(self.contract, ensure_ascii=False).lower()
        for forbidden in (
            '"extensions"',
            '"expression"',
            "claude",
            "codex",
            "git ",
            "byte budget",
            "token budget",
            "latency",
            "runtime_state",
            "child_total",
            "commit_total",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)

    def test_semantic_contract_is_not_runtime_force_loaded(self):
        force_load = re.compile(
            r"(?is)force-load[^\n]{0,200}semantic-contract\.json"
        )
        for path in (ROOT / "src/skills/run").rglob("*.md"):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(
                    force_load.search(path.read_text(encoding="utf-8"))
                )


if __name__ == "__main__":
    unittest.main()
