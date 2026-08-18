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
        "selected_base",
        "external_base_pin",
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
        "user_output_routine_progress",
    ],
    "invariant_kind": list(EXPECTED_INVARIANT_KINDS.values()),
}
EXPECTED_SCENARIO_IDS = {
    "direct-success",
    "single-risky-success",
    "parallel-success",
    "external-success",
    "failure-verification-non-green",
    "failure-verification-unevaluable",
    "failure-merge-non-green",
    "failure-merge-unevaluable",
    "failure-integration-non-green",
    "failure-integration-unevaluable",
    "failure-completion-non-green",
    "failure-completion-unevaluable",
    "failure-runtime-non-green",
    "failure-runtime-unevaluable",
    "failure-review-non-green",
    "failure-review-unevaluable",
    "failure-regeneration-non-green",
    "failure-regeneration-unevaluable",
    "failure-terminal-non-green",
    "failure-merge-precondition-unevaluable",
    "completion-reuse",
    "completion-rerun-after-non-green",
    "completion-rerun-after-unevaluable",
    "completion-rerun-after-verify-set-change",
    "completion-rerun-after-base-tip-change",
    "concern-resolved",
    "concern-explicitly-accepted",
    "concern-user-requirement-accepted",
    "concern-user-compatibility-accepted",
    "concern-user-safety-accepted",
    "concern-promoted-failure-wins",
    "concern-pending-blocks",
    "lifecycle-ownership-matrix",
    "review-conditional-and-final-clear",
    "review-non-risky-skips-conditional",
    "review-no-cascade-skips-conditional",
    "output-allowed-events",
    "output-routine-silence",
    "output-allowed-after-routine-operation",
}
EXPECTED_MUTANT_IDS = {
    "external-conditional-base-commit",
    "external-missing-independent-proof",
    "external-mismatched-base-pin",
    "single-risky-merge-before-verification",
    "parallel-missing-integration-gate",
    "completion-reuse-missing-sha",
    "completion-reuse-missing-verify-set",
    "unevaluable-verification-treated-as-green",
    "merge-precondition-labeled-lifecycle-only",
    "startup-wrong-owner",
    "pending-concern-completes",
    "user-safety-non-user-acceptance",
    "conditional-review-replaces-final",
    "routine-progress-narration",
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


def validate_contract(contract):
    require_exact_keys(contract, TOP_LEVEL_KEYS, "contract")
    if type(contract["schema_version"]) is not int or contract["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    if contract["contract_id"] != "leanforge.run.semantics":
        raise ValueError("contract_id must be 'leanforge.run.semantics'")
    require_exact_keys(contract["vocabulary"], EXPECTED_VOCABULARY, "vocabulary")
    if contract["vocabulary"] != EXPECTED_VOCABULARY:
        raise ValueError("vocabulary enums must exactly match the closed vocabulary")

    invariants = contract["invariants"]
    if not isinstance(invariants, list):
        raise ValueError("invariants must be an array")
    if [item.get("id") for item in invariants] != list(EXPECTED_INVARIANT_KINDS):
        raise ValueError("invariant IDs must exactly match the protected stable IDs")
    for index, invariant in enumerate(invariants):
        label = f"invariants[{index}]"
        require_exact_keys(invariant, {"id", "kind", "definition", "constraints"}, label)
        invariant_id = invariant["id"]
        if invariant["kind"] != EXPECTED_INVARIANT_KINDS[invariant_id]:
            raise ValueError(f"{label} has the wrong invariant kind")
        if not isinstance(invariant["definition"], str) or not invariant["definition"]:
            raise ValueError(f"{label}.definition must be one non-empty string")
        constraints = invariant["constraints"]
        if (
            not isinstance(constraints, list)
            or not constraints
            or any(not isinstance(item, str) or not item for item in constraints)
            or len(constraints) != len(set(constraints))
        ):
            raise ValueError(f"{label}.constraints must be non-empty unique strings")

    forbidden_keys = {
        "cases",
        "scenarios",
        "traces",
        "trace",
        "mutants",
        "assertions",
        "assertion_language",
        "op",
        "target",
    }

    def visit(value):
        if isinstance(value, dict):
            if forbidden_keys.intersection(value):
                raise ValueError("contract contains a trace/assertion program surface")
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(contract)


def validate_trace(trace, vocabulary, label):
    if not isinstance(trace, list):
        raise ValueError(f"{label} must be an array")
    allowed = {"event", "owner", "route", "overlay", "outcome", "disposition", "value"}
    for index, occurrence in enumerate(trace):
        occurrence_label = f"{label}[{index}]"
        if not isinstance(occurrence, dict):
            raise ValueError(f"{occurrence_label} must be an object")
        if "event" not in occurrence or not set(occurrence).issubset(allowed):
            raise ValueError(f"{occurrence_label} has unknown keys or lacks event")
        if occurrence["event"] not in vocabulary["event"]:
            raise ValueError(f"{occurrence_label} has unknown event")
        if "owner" in occurrence and occurrence["owner"] not in vocabulary["owner"]:
            raise ValueError(f"{occurrence_label} has unknown owner")
        for enum_name in ("route", "overlay", "outcome", "disposition"):
            if enum_name in occurrence and occurrence[enum_name] not in vocabulary[enum_name]:
                raise ValueError(f"{occurrence_label} has unknown {enum_name}")
        if "value" in occurrence and not isinstance(occurrence["value"], str):
            raise ValueError(f"{occurrence_label}.value must be a string")


def validate_fixture(fixture, vocabulary):
    require_exact_keys(
        fixture,
        {"schema_version", "behavior_origin_commit", "scenarios", "mutants"},
        "fixture",
    )
    if type(fixture["schema_version"]) is not int or fixture["schema_version"] != 1:
        raise ValueError("fixture schema_version must be integer 1")
    if fixture["behavior_origin_commit"] != "fb252b4236cc607002e131210f6161db72f6841e":
        raise ValueError("fixture behavior_origin_commit is not protected v1.8.1")

    seen_ids = set()
    for collection_name, expected_keys, expected_valid, expected_outcome in (
        (
            "scenarios",
            {"id", "trace", "expected_valid", "expected_outcome"},
            True,
            "accepted",
        ),
        (
            "mutants",
            {
                "id",
                "trace",
                "expected_valid",
                "expected_outcome",
                "expected_contract_id",
                "expected_reason",
            },
            False,
            "rejected",
        ),
    ):
        collection = fixture[collection_name]
        if not isinstance(collection, list):
            raise ValueError(f"fixture.{collection_name} must be an array")
        for index, item in enumerate(collection):
            label = f"{collection_name}[{index}]"
            require_exact_keys(item, expected_keys, label)
            if not isinstance(item["id"], str) or not item["id"] or item["id"] in seen_ids:
                raise ValueError(f"{label}.id must be non-empty and unique")
            seen_ids.add(item["id"])
            if item["expected_valid"] is not expected_valid:
                raise ValueError(f"{label}.expected_valid has the wrong literal")
            if item["expected_outcome"] != expected_outcome:
                raise ValueError(f"{label}.expected_outcome has the wrong literal")
            validate_trace(item["trace"], vocabulary, f"{label}.trace")
            if collection_name == "mutants":
                if item["expected_contract_id"] not in EXPECTED_INVARIANT_KINDS:
                    raise ValueError(f"{label}.expected_contract_id is unknown")
                if not isinstance(item["expected_reason"], str) or not item["expected_reason"]:
                    raise ValueError(f"{label}.expected_reason must be non-empty")

    if {item["id"] for item in fixture["scenarios"]} != EXPECTED_SCENARIO_IDS:
        raise ValueError("fixture scenarios must exactly match the hand-authored set")
    if {item["id"] for item in fixture["mutants"]} != EXPECTED_MUTANT_IDS:
        raise ValueError("fixture mutants must exactly match the known-opposite set")


def matching_indexes(trace, event, **facts):
    return [
        index
        for index, occurrence in enumerate(trace)
        if occurrence.get("event") == event
        and all(occurrence.get(key) == value for key, value in facts.items())
    ]


def has_event(trace, event, **facts):
    return bool(matching_indexes(trace, event, **facts))


def owner_is(trace, event, owner):
    indexes = matching_indexes(trace, event)
    return bool(indexes) and all(trace[index].get("owner") == owner for index in indexes)


def ordered(trace, first, second):
    first_indexes = matching_indexes(trace, first)
    second_indexes = matching_indexes(trace, second)
    return bool(first_indexes and second_indexes) and max(first_indexes) < min(second_indexes)


def same_single_value(trace, first, second):
    first_indexes = matching_indexes(trace, first)
    second_indexes = matching_indexes(trace, second)
    return (
        len(first_indexes) == 1
        and len(second_indexes) == 1
        and trace[first_indexes[0]].get("value") == trace[second_indexes[0]].get("value")
    )


def validate_route_topology(trace):
    selected = matching_indexes(trace, "route_selected")
    if not selected:
        return None
    if len(selected) != 1:
        return "a success route must be selected exactly once"
    route = trace[selected[0]].get("route")
    if route == "direct":
        checks = (
            (owner_is(trace, "task_implementation", "orchestrator"), "direct implementation must be orchestrator-owned"),
            (len(matching_indexes(trace, "evidence_captured")) == 1, "direct route requires captured evidence"),
            (len(matching_indexes(trace, "base_commit")) == 1, "direct route requires one base commit"),
            (not has_event(trace, "worktree_created"), "direct route forbids a task worktree"),
            (not has_event(trace, "integration_gate"), "direct route has no wave integration gate"),
        )
    elif route == "single_risky":
        checks = (
            (len(matching_indexes(trace, "worktree_created")) == 1, "single-risky route requires one task worktree"),
            (owner_is(trace, "task_implementation", "implementer"), "single-risky implementation must be implementer-owned"),
            (len(matching_indexes(trace, "task_verification", outcome="green")) == 1, "single-risky route requires green task verification"),
            (len(matching_indexes(trace, "merge_precondition", outcome="green")) == 1, "single-risky route requires a green merge precondition"),
            (len(matching_indexes(trace, "merge_gate", outcome="green")) == 1, "single-risky route requires a green merge gate"),
            (ordered(trace, "task_verification", "task_merged"), "single-risky verification must precede merge"),
            (ordered(trace, "task_verification", "merge_precondition"), "single-risky verification must precede merge precondition"),
            (ordered(trace, "merge_precondition", "merge_gate"), "single-risky merge precondition must precede merge gate"),
            (ordered(trace, "merge_gate", "task_merged"), "single-risky merge gate must precede merge"),
        )
    elif route == "parallel":
        checks = (
            (len(matching_indexes(trace, "isolated_task_worktrees")) == 1, "parallel route requires isolated task worktrees"),
            (owner_is(trace, "task_implementation", "implementer"), "parallel implementation must be implementer-owned"),
            (len(matching_indexes(trace, "task_verifications_complete", outcome="green")) == 1, "parallel route requires green task verification"),
            (len(matching_indexes(trace, "merge_gates_complete", outcome="green")) == 1, "parallel route requires green merge gates"),
            (len(matching_indexes(trace, "serial_merge")) == 1, "parallel route requires serial merge"),
            (len(matching_indexes(trace, "regeneration", outcome="green")) == 1, "parallel route requires green regeneration"),
            (len(matching_indexes(trace, "wiring", outcome="green")) == 1, "parallel route requires green wiring"),
            (len(matching_indexes(trace, "integration_gate", outcome="green")) == 1, "parallel route requires one green integration gate"),
            (ordered(trace, "isolated_task_worktrees", "task_verifications_complete"), "parallel isolation must precede task verification"),
            (ordered(trace, "task_verifications_complete", "merge_gates_complete"), "parallel task verification must precede merge gates"),
            (ordered(trace, "merge_gates_complete", "serial_merge"), "parallel merge gates must precede serial merge"),
            (ordered(trace, "serial_merge", "regeneration"), "parallel serial merge must precede regeneration"),
            (ordered(trace, "regeneration", "wiring"), "parallel regeneration must precede wiring"),
            (ordered(trace, "wiring", "integration_gate"), "parallel wiring must precede integration gate"),
        )
    elif route == "external":
        checks = (
            (owner_is(trace, "external_action", "implementer"), "external action must be implementer-owned"),
            (not has_event(trace, "worktree_created"), "external route forbids a task worktree"),
            (not has_event(trace, "isolated_task_worktrees"), "external route forbids isolated task worktrees"),
        )
    else:
        return "selected route is outside the closed route vocabulary"
    for passed, reason in checks:
        if not passed:
            return reason
    return None


def validate_external_proof(trace):
    external_events = {
        "selected_base",
        "external_base_pin",
        "external_action",
        "external_evidence",
        "conditional_base_commit",
        "independent_commit_proof",
    }
    selected_external = matching_indexes(trace, "route_selected", route="external")
    if not selected_external and not any(item.get("event") in external_events for item in trace):
        return None
    if len(selected_external) != 1:
        return "external proof applies only to one selected external route"
    if len(matching_indexes(trace, "selected_base")) != 1:
        return "external route requires one selected base"
    if len(matching_indexes(trace, "external_base_pin")) != 1:
        return "external implementer must be pinned to the selected base before action"
    if not same_single_value(trace, "selected_base", "external_base_pin"):
        return "external base pin must match the selected base"
    if not owner_is(trace, "external_base_pin", "implementer") or not ordered(
        trace, "selected_base", "external_base_pin"
    ) or not ordered(trace, "external_base_pin", "external_action"):
        return "external implementer must be pinned to the selected base before action"
    checks = (
        (owner_is(trace, "external_action", "implementer"), "external action must be implementer-owned"),
        (len(matching_indexes(trace, "external_evidence", outcome="green")) == 1, "external route requires captured green external evidence"),
        (len(matching_indexes(trace, "base_commit")) == 1, "external route requires an unconditional base commit"),
        (not has_event(trace, "conditional_base_commit"), "external base commit must not be conditional"),
        (len(matching_indexes(trace, "independent_commit_proof")) == 1, "external route requires independent commit proof"),
        (owner_is(trace, "independent_commit_proof", "orchestrator"), "external commit proof must be independently owned"),
        (ordered(trace, "external_action", "external_evidence"), "external action must precede captured evidence"),
        (ordered(trace, "external_evidence", "base_commit"), "external evidence must precede base commit"),
        (ordered(trace, "base_commit", "independent_commit_proof"), "external base commit must precede independent proof"),
    )
    for passed, reason in checks:
        if not passed:
            return reason
    return None


def validate_failure_overlay(trace):
    phases = {
        "task_verification": "verification result",
        "task_verifications_complete": "verification result",
        "merge_precondition": "merge precondition",
        "merge_gate": "merge result",
        "merge_gates_complete": "merge result",
        "integration_gate": "integration result",
        "completion_gate": "completion result",
        "runtime_result": "runtime result",
        "review_result": "review result",
        "regeneration": "regeneration result",
    }
    continuations = {
        "retry",
        "task_merged",
        "serial_merge",
        "cleanup",
        "downstream_dispatch",
        "progress",
    }
    for result_index, occurrence in enumerate(trace):
        event = occurrence.get("event")
        outcome = occurrence.get("outcome")
        if event not in phases or outcome not in {"non_green", "unevaluable"}:
            continue
        overlays = [
            index
            for index in matching_indexes(trace, "failure_overlay_entered", overlay="failure")
            if index > result_index
        ]
        if not overlays:
            return f"{outcome} {phases[event]} must enter failure overlay"
        overlay_index = min(overlays)
        if any(
            result_index < index < overlay_index
            and later.get("event") in continuations
            for index, later in enumerate(trace)
        ):
            return "failure overlay must precede any present continuation"
    return None


def validate_completion_reuse(trace):
    reuse = has_event(trace, "completion_reused")
    full_verify = has_event(trace, "completion_full_verify")
    if reuse:
        checks = (
            (len(matching_indexes(trace, "prior_integration", outcome="green")) == 1, "completion reuse requires prior green integration"),
            (len(matching_indexes(trace, "prior_verify_set")) == 1, "completion reuse requires the prior verify set"),
            (len(matching_indexes(trace, "current_verify_set")) == 1, "completion reuse requires the current verify set"),
            (same_single_value(trace, "prior_verify_set", "current_verify_set"), "completion reuse requires an identical verify set"),
            (len(matching_indexes(trace, "prior_gate_base_tip")) == 1, "completion reuse requires the prior gate base-tip SHA"),
            (len(matching_indexes(trace, "current_base_tip")) == 1, "completion reuse requires the current base-tip SHA"),
            (same_single_value(trace, "prior_gate_base_tip", "current_base_tip"), "completion reuse requires the same gate and current base-tip SHA"),
            (not full_verify, "matching completion evidence avoids a redundant full verify"),
        )
        for passed, reason in checks:
            if not passed:
                return reason

    requires_full = (
        bool(matching_indexes(trace, "prior_integration", outcome="non_green"))
        or bool(matching_indexes(trace, "prior_integration", outcome="unevaluable"))
        or has_event(trace, "verify_set_changed")
        or has_event(trace, "base_tip_changed")
    )
    if requires_full and not full_verify:
        return "changed or non-green completion evidence requires full verify"
    if requires_full and reuse:
        return "changed or non-green completion evidence forbids completion reuse"
    return None


def validate_concern_disposition(trace):
    concern_events = {
        "concern_recorded",
        "user_owned_requirement_concern",
        "user_owned_compatibility_concern",
        "user_owned_safety_concern",
        "concern_disposition",
    }
    if not any(item.get("event") in concern_events for item in trace):
        return None
    dispositions = matching_indexes(trace, "concern_disposition")
    if not dispositions:
        return "concern must have a closed disposition"
    for index in dispositions:
        disposition = trace[index].get("disposition")
        if disposition == "user_accepted" and trace[index].get("owner") != "user":
            return "user acceptance must be user-owned"
        if disposition == "pending":
            if has_event(trace, "completion"):
                return "pending concern blocks completion"
            if has_event(trace, "user_gate"):
                return "pending concern blocks user gate"
        if disposition == "promoted_to_failure":
            if not has_event(trace, "failure_overlay_entered", overlay="failure"):
                return "promoted concern requires failure overlay"
            if has_event(trace, "completion"):
                return "failure overlay blocks completion"
            if has_event(trace, "user_gate"):
                return "failure overlay blocks user gate"
            if has_event(trace, "progress"):
                return "failure overlay blocks progress"

    user_concerns = {
        "user_owned_requirement_concern": "requirement",
        "user_owned_compatibility_concern": "compatibility",
        "user_owned_safety_concern": "safety",
    }
    for event, label in user_concerns.items():
        if has_event(trace, event) and not any(
            trace[index].get("disposition") == "user_accepted"
            and trace[index].get("owner") == "user"
            for index in dispositions
        ):
            return f"user-owned {label} concern requires user acceptance"
    return None


def validate_lifecycle_ownership(trace):
    owners = {
        "startup": ("harness_lifecycle", "startup ownership belongs to harness lifecycle"),
        "interrupted_run": ("harness_lifecycle", "interrupted-run ownership belongs to harness lifecycle"),
        "archive": ("harness_lifecycle", "archive ownership belongs to harness lifecycle"),
        "migration": ("harness_lifecycle", "migration ownership belongs to harness lifecycle"),
        "runtime_task_failure": ("runtime_failure_overlay", "runtime task failure ownership belongs to failure overlay"),
        "runtime_gate_failure": ("runtime_failure_overlay", "runtime gate failure ownership belongs to failure overlay"),
        "runtime_review_failure": ("runtime_failure_overlay", "runtime review failure ownership belongs to failure overlay"),
    }
    for event, (owner, reason) in owners.items():
        indexes = matching_indexes(trace, event)
        if indexes and any(trace[index].get("owner") != owner for index in indexes):
            return reason
    return None


def validate_review_topology(trace):
    has_risky = has_event(trace, "risky_task")
    has_non_risky = has_event(trace, "non_risky_task")
    has_cascade = has_event(trace, "downstream_cascade_risk")
    no_cascade = has_event(trace, "no_downstream_cascade_risk")
    review_facts = has_risky or has_non_risky or has_cascade or no_cascade
    conditional = has_event(trace, "conditional_spec_review")
    final_review = has_event(trace, "final_full_diff_review")
    if has_risky and has_cascade:
        if not conditional:
            return "risky downstream cascade requires conditional spec review"
        if not final_review:
            return "conditional review never replaces final full-diff review"
        if has_event(trace, "downstream_dispatch") and not ordered(
            trace, "conditional_spec_review", "downstream_dispatch"
        ):
            return "conditional review must precede downstream dispatch"
        if not ordered(trace, "conditional_spec_review", "final_full_diff_review"):
            return "conditional review must precede final full-diff review"
    if (has_non_risky or no_cascade) and conditional:
        return "conditional review applies only to risky downstream cascade"
    if review_facts and not final_review:
        return "final full-diff review is required"
    if has_event(trace, "review_verdict", outcome="clear") and has_event(
        trace, "blocking_finding"
    ):
        return "clear final verdict requires zero blocking findings"
    return None


def validate_output_semantics(trace):
    if has_event(trace, "user_output_routine_progress"):
        return "routine progress narration is forbidden"
    return None


INVARIANT_VALIDATORS = {
    "RUN-ROUTE-TOPOLOGY": validate_route_topology,
    "RUN-EXTERNAL-PROOF": validate_external_proof,
    "RUN-FAIL-CLOSED": validate_failure_overlay,
    "RUN-COMPLETION-REUSE": validate_completion_reuse,
    "RUN-CONCERN-DISPOSITION": validate_concern_disposition,
    "RUN-LIFECYCLE-OWNERSHIP": validate_lifecycle_ownership,
    "RUN-REVIEW-TOPOLOGY": validate_review_topology,
    "RUN-OUTPUT-SEMANTICS": validate_output_semantics,
}


def validate_semantics(contract, trace):
    """Derive and apply every applicable invariant from the trace itself."""
    validate_contract(contract)
    validate_trace(trace, contract["vocabulary"], "trace")
    for invariant in contract["invariants"]:
        invariant_id = invariant["id"]
        reason = INVARIANT_VALIDATORS[invariant_id](trace)
        if reason is not None:
            return {
                "valid": False,
                "outcome": "rejected",
                "contract_id": invariant_id,
                "reason": reason,
            }
    return {"valid": True, "outcome": "accepted", "contract_id": None, "reason": None}


def render_protected_block(invariant):
    invariant_json = json.dumps(invariant, ensure_ascii=False, indent=2)
    invariant_id = invariant["id"]
    return (
        f"<!-- leanforge:run-semantic:{invariant_id}:start -->\n"
        "```json\n"
        f"{invariant_json}\n"
        "```\n"
        f"<!-- leanforge:run-semantic:{invariant_id}:end -->"
    )


class RunSemanticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_json(CONTRACT_PATH)
        validate_contract(cls.contract)
        cls.fixture = load_json(FIXTURE_PATH)
        validate_fixture(cls.fixture, cls.contract["vocabulary"])

    def test_hand_authored_behavior_scenarios(self):
        for scenario in self.fixture["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                result = validate_semantics(self.contract, scenario["trace"])
                self.assertEqual(result["valid"], scenario["expected_valid"])
                self.assertEqual(result["outcome"], scenario["expected_outcome"])
                self.assertIsNone(result["contract_id"])
                self.assertIsNone(result["reason"])

    def test_known_opposite_mutants_fail_with_exact_reason(self):
        survivors = []
        for mutant in self.fixture["mutants"]:
            with self.subTest(mutant=mutant["id"]):
                result = validate_semantics(self.contract, mutant["trace"])
                if result["valid"]:
                    survivors.append(mutant["id"])
                self.assertEqual(result["valid"], mutant["expected_valid"])
                self.assertEqual(result["outcome"], mutant["expected_outcome"])
                self.assertEqual(result["contract_id"], mutant["expected_contract_id"])
                self.assertEqual(result["reason"], mutant["expected_reason"])
        self.assertEqual(survivors, [], f"surviving mutants: {survivors}")

    def test_contract_is_a_small_semantic_kernel_not_a_trace_dsl(self):
        self.assertEqual(len(self.contract["invariants"]), 8)
        serialized = json.dumps(self.contract, ensure_ascii=False)
        for forbidden_key in (
            '"cases"',
            '"scenarios"',
            '"traces"',
            '"trace"',
            '"mutants"',
            '"assertions"',
            '"assertion_language"',
            '"op"',
            '"target"',
        ):
            with self.subTest(forbidden_key=forbidden_key):
                self.assertNotIn(forbidden_key, serialized)

    def test_validator_derives_external_proof_and_base_pin(self):
        trace = [
            {"event": "route_selected", "route": "external", "owner": "orchestrator"},
            {"event": "external_action", "owner": "implementer"},
            {"event": "external_evidence", "outcome": "green", "owner": "implementer"},
            {"event": "base_commit", "owner": "orchestrator"},
        ]
        result = validate_semantics(self.contract, trace)
        self.assertEqual(result["contract_id"], "RUN-EXTERNAL-PROOF")
        self.assertEqual(result["reason"], "external route requires one selected base")

    def test_validator_derives_failure_overlay_despite_lifecycle_facts(self):
        trace = [
            {"event": "startup", "owner": "harness_lifecycle"},
            {"event": "merge_precondition", "outcome": "unevaluable", "owner": "orchestrator"},
            {"event": "progress", "owner": "orchestrator"},
        ]
        result = validate_semantics(self.contract, trace)
        self.assertEqual(result["contract_id"], "RUN-FAIL-CLOSED")
        self.assertEqual(
            result["reason"],
            "unevaluable merge precondition must enter failure overlay",
        )

    def test_terminal_failure_overlay_does_not_require_continuations(self):
        trace = [
            {"event": "task_verification", "outcome": "non_green", "owner": "implementer"},
            {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

    def test_routine_operation_may_precede_actual_result_output(self):
        trace = [
            {"event": "routine_read", "owner": "orchestrator"},
            {"event": "user_output_actual_blocker", "owner": "orchestrator"},
            {"event": "user_output_final_result", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

    def test_fixture_is_an_independent_oracle_without_rule_selection(self):
        serialized = json.dumps(self.fixture, ensure_ascii=False)
        for forbidden_key in ('"contracts"', '"assertions"', '"assertion_language"'):
            with self.subTest(forbidden_key=forbidden_key):
                self.assertNotIn(forbidden_key, serialized)
        for collection_name in ("scenarios", "mutants"):
            for item in self.fixture[collection_name]:
                with self.subTest(collection=collection_name, item=item["id"]):
                    self.assertIn("expected_valid", item)
                    self.assertIn("expected_outcome", item)

    def test_exactly_one_deterministic_protected_block_per_invariant(self):
        combined_markdown = "\n".join(
            path.read_text(encoding="utf-8") for path in MARKDOWN_PATHS
        )
        invariants = {item["id"]: item for item in self.contract["invariants"]}
        marker_ids = re.findall(
            r"<!-- leanforge:run-semantic:([^:]+):start -->", combined_markdown
        )
        self.assertEqual(sorted(marker_ids), sorted(EXPECTED_INVARIANT_KINDS))
        for invariant_id, invariant in invariants.items():
            with self.subTest(invariant=invariant_id):
                marker = re.compile(
                    rf"(?ms)<!-- leanforge:run-semantic:{re.escape(invariant_id)}:"
                    rf"start -->.*?<!-- leanforge:run-semantic:"
                    rf"{re.escape(invariant_id)}:end -->"
                )
                blocks = marker.findall(combined_markdown)
                self.assertEqual(len(blocks), 1)
                self.assertEqual(blocks[0], render_protected_block(invariant))

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
        embedded_cases = copy.deepcopy(self.contract)
        embedded_cases["invariants"][0]["cases"] = []
        mutations.append(("embedded cases", embedded_cases))
        embedded_assertions = copy.deepcopy(self.contract)
        embedded_assertions["invariants"][0]["assertions"] = []
        mutations.append(("embedded assertions", embedded_assertions))
        for label, mutation in mutations:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    validate_contract(mutation)

    def test_fixture_schema_fails_closed(self):
        mutations = []
        caller_contracts = copy.deepcopy(self.fixture)
        caller_contracts["scenarios"][0]["contracts"] = ["RUN-ROUTE-TOPOLOGY"]
        mutations.append(("caller-selected contracts", caller_contracts))
        assertion_program = copy.deepcopy(self.fixture)
        assertion_program["scenarios"][0]["assertions"] = []
        mutations.append(("fixture assertion program", assertion_program))
        unknown_event = copy.deepcopy(self.fixture)
        unknown_event["scenarios"][0]["trace"][0]["event"] = "unknown_event"
        mutations.append(("unknown event", unknown_event))
        false_scenario = copy.deepcopy(self.fixture)
        false_scenario["scenarios"][0]["expected_valid"] = False
        mutations.append(("wrong scenario literal", false_scenario))
        unknown_item_key = copy.deepcopy(self.fixture)
        unknown_item_key["mutants"][0]["survived"] = False
        mutations.append(("unknown mutant key", unknown_item_key))
        for label, mutation in mutations:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    validate_fixture(mutation, self.contract["vocabulary"])

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
        force_load = re.compile(r"(?is)force-load[^\n]{0,200}semantic-contract\.json")
        for path in (ROOT / "src/skills/run").rglob("*.md"):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(force_load.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
