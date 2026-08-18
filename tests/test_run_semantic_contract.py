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
ASSERTION_OPERATORS = ["count", "forbid", "before", "same", "owner"]
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
RESULT_EVENTS = [
    "task_verification",
    "task_verifications_complete",
    "merge_precondition",
    "merge_gate",
    "merge_gates_complete",
    "regeneration",
    "wiring",
    "integration_gate",
    "external_evidence",
    "completion_gate",
    "completion_full_verify",
    "runtime_smoke",
    "conditional_spec_review",
    "final_full_diff_review",
    "review_verdict",
]
CONTINUATION_EVENTS = RESULT_EVENTS + [
    "route_selected",
    "worktree_created",
    "isolated_task_worktrees",
    "task_implementation",
    "evidence_captured",
    "selected_base",
    "external_base_pin",
    "external_action",
    "retry",
    "task_merged",
    "serial_merge",
    "conditional_base_commit",
    "base_commit",
    "independent_commit_proof",
    "cleanup",
    "downstream_dispatch",
    "progress",
    "completion_reused",
    "completion",
    "user_gate",
    "routine_read",
    "routine_write",
    "routine_dispatch",
    "routine_merge",
    "routine_gate",
    "routine_cleanup",
    "remedial_worktree_created",
    "remedial_implementer_continuation",
]
FAILURE_OUTCOMES = {"non_green", "unevaluable", "blocking"}
RESULT_OUTCOMES = {
    event: {"green", "non_green", "unevaluable"}
    for event in RESULT_EVENTS
}
RESULT_OUTCOMES["conditional_spec_review"] = {
    "clear",
    "blocking",
    "non_green",
    "unevaluable",
}
RESULT_OUTCOMES["final_full_diff_review"] = {
    "green",
    "blocking",
}
RESULT_OUTCOMES["review_verdict"] = {"clear", "blocking"}
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
        "reviewer",
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
        "runtime_smoke",
        "prior_integration",
        "prior_verify_set",
        "completion_verify_set",
        "prior_gate_base_tip",
        "current_base_tip",
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
        "routine_read",
        "routine_write",
        "routine_dispatch",
        "routine_merge",
        "routine_gate",
        "routine_cleanup",
        "remedial_worktree_created",
        "remedial_implementer_continuation",
        "user_output_needed_question",
        "user_output_actual_blocker",
        "user_output_wave_completion",
        "user_output_final_result",
        "user_output_approval_request",
        "user_output_routine_progress",
    ],
    "result_event": RESULT_EVENTS,
    "continuation_event": CONTINUATION_EVENTS,
    "invariant_kind": list(EXPECTED_INVARIANT_KINDS.values()),
}


TASK_CORRELATION_EVENTS = {
    "worktree_created",
    "task_implementation",
    "evidence_captured",
    "task_verification",
    "merge_precondition",
    "merge_gate",
    "task_merged",
}
REVIEW_CORRELATION_EVENTS = {
    "risky_task",
    "non_risky_task",
    "downstream_cascade_risk",
    "no_downstream_cascade_risk",
    "conditional_spec_review",
}


def event_metadata_schema():
    schema = {
        event: {
            "allowed": {"event", "owner"},
            "required": {"event"},
            "types": {"event": str, "owner": str},
        }
        for event in EXPECTED_VOCABULARY["event"]
    }

    def add(event, key, *, required=False):
        schema[event]["allowed"].add(key)
        schema[event]["types"][key] = str
        if required:
            schema[event]["required"].add(key)

    add("route_selected", "route", required=True)
    schema["route_selected"]["required"].add("owner")
    for event in TASK_CORRELATION_EVENTS:
        add(event, "task_id")
    for event in REVIEW_CORRELATION_EVENTS:
        add(event, "task_id", required=True)
    add("failure_overlay_entered", "overlay", required=True)
    schema["failure_overlay_entered"]["required"].add("owner")
    for event in RESULT_EVENTS:
        add(event, "outcome", required=True)
    add("prior_integration", "outcome", required=True)
    add("review_verdict", "outcome", required=True)
    for event in (
        "conditional_spec_review",
        "final_full_diff_review",
        "review_verdict",
        "completion",
        "user_gate",
    ):
        schema[event]["required"].add("owner")
    for event in (
        "selected_base",
        "external_base_pin",
        "prior_verify_set",
        "completion_verify_set",
        "prior_gate_base_tip",
        "current_base_tip",
        "concern_recorded",
        "user_owned_requirement_concern",
        "user_owned_compatibility_concern",
        "user_owned_safety_concern",
    ):
        add(event, "value", required=True)
    add("concern_disposition", "value", required=True)
    add("concern_disposition", "disposition", required=True)
    return schema


EVENT_METADATA_SCHEMA = event_metadata_schema()
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
    "failure-final-review-blocking-retry",
    "failure-review-verdict-blocking-cleanup",
    "failure-regeneration-non-green",
    "failure-regeneration-unevaluable",
    "failure-terminal-non-green",
    "failure-merge-precondition-unevaluable",
    "failure-merge-precondition-non-green",
    "failure-task-verifications-complete-non-green",
    "failure-task-verifications-complete-unevaluable",
    "failure-merge-gates-complete-non-green",
    "failure-merge-gates-complete-unevaluable",
    "failure-wiring-non-green",
    "failure-wiring-unevaluable",
    "failure-external-evidence-unevaluable",
    "failure-completion-full-verify-unevaluable",
    "failure-conditional-review-blocking",
    "failure-conditional-review-unevaluable",
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
    "single-risky-terminal-failure",
    "failure-external-evidence-non-green",
    "failure-completion-full-verify-non-green",
    "failure-conditional-review-non-green",
    "failure-final-review-blocking",
    "completion-forced-rerun",
    "completion-without-reuse-runs-full-verify",
    "concern-user-requirement-pending",
    "concern-user-safety-promoted",
    "direct-substantive-failure-remedial-worktree",
    "review-blocking-verdict-failure",
}
EXPECTED_MUTANT_IDS = {
    "external-conditional-base-commit",
    "external-missing-independent-proof",
    "external-mismatched-base-pin",
    "single-risky-merge-before-verification",
    "single-risky-merge-before-precondition",
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
    "external-missing-base-pin-value",
    "completion-skip-full-verify-missing-green",
    "completion-skip-full-verify-mismatched-set",
    "completion-skip-full-verify-mismatched-sha",
    "failure-external-evidence-no-overlay",
    "failure-completion-full-verify-no-overlay",
    "failure-conditional-review-no-overlay",
    "failure-final-review-blocking-verdict-no-overlay",
    "failure-overlay-wrong-owner",
    "concern-missing-disposition-value",
    "concern-unknown-disposition-value",
    "conditional-review-without-cascade",
    "direct-parallel-action-mixing",
    "single-risky-work-after-failed-verification-before-overlay",
    "completion-reuse-conflicting-prior-integration",
    "direct-completion-without-final-review",
    "direct-user-gate-without-final-review",
    "blocking-conditional-review-clear-verdict",
    "clear-verdict-without-green-final-review",
    "task-verification-missing-outcome",
    "failure-overlay-missing-overlay",
    "failure-overlay-missing-owner",
    "route-omitted-direct-events",
    "route-omitted-complete-single-risky",
    "failure-routine-write-before-overlay",
    "failure-routine-dispatch-before-overlay",
    "failure-routine-merge-before-overlay",
    "failure-routine-gate-before-overlay",
    "failure-routine-cleanup-before-overlay",
    "final-review-clear-success",
    "review-verdict-blocking-no-overlay",
    "review-verdict-conflicting-completion",
    "completion-endpoint-without-reuse-or-full-verify",
    "failure-routine-read-before-overlay",
    "blocking-verdict-without-review",
    "green-review-blocking-verdict",
    "external-base-commit-wrong-owner",
    "concern-disposition-before-record",
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


def validate_trace(trace, vocabulary, label, *, check_event_outcomes=True):
    if not isinstance(trace, list):
        raise ValueError(f"{label} must be an array")
    value_events = {
        "selected_base",
        "external_base_pin",
        "prior_verify_set",
        "completion_verify_set",
        "prior_gate_base_tip",
        "current_base_tip",
        "concern_recorded",
        "user_owned_requirement_concern",
        "user_owned_compatibility_concern",
        "user_owned_safety_concern",
    }
    for index, occurrence in enumerate(trace):
        occurrence_label = f"{label}[{index}]"
        if not isinstance(occurrence, dict):
            raise ValueError(f"{occurrence_label} must be an object")
        event = occurrence.get("event")
        if event not in vocabulary["event"]:
            raise ValueError(f"{occurrence_label} has unknown event or lacks event")

        allowed = {"event", "owner"}
        if event == "route_selected":
            allowed.add("route")
        if event in TASK_CORRELATION_EVENTS.union(REVIEW_CORRELATION_EVENTS):
            allowed.add("task_id")
        if event == "failure_overlay_entered":
            allowed.add("overlay")
        if event in vocabulary["result_event"] or event in {
            "prior_integration",
            "review_verdict",
        }:
            allowed.add("outcome")
        if event in value_events:
            allowed.add("value")
        if event == "concern_disposition":
            allowed.update({"value", "disposition"})
        schema = EVENT_METADATA_SCHEMA[event]
        if allowed != schema["allowed"]:
            raise ValueError(f"{occurrence_label} metadata schema is inconsistent")
        if not set(occurrence).issubset(allowed):
            raise ValueError(f"{occurrence_label} has keys not allowed for {event}")

        for key, value in occurrence.items():
            if type(value) is not schema["types"][key]:
                raise ValueError(f"{occurrence_label}.{key} has the wrong type")

        if "owner" in occurrence and occurrence["owner"] not in vocabulary["owner"]:
            raise ValueError(f"{occurrence_label} has unknown owner")
        for enum_name in ("route", "overlay", "outcome"):
            if enum_name in occurrence and occurrence[enum_name] not in vocabulary[enum_name]:
                raise ValueError(f"{occurrence_label} has unknown {enum_name}")
        if "disposition" in occurrence and not isinstance(occurrence["disposition"], str):
            raise ValueError(f"{occurrence_label}.disposition must be a string")
        if "value" in occurrence and not isinstance(occurrence["value"], str):
            raise ValueError(f"{occurrence_label}.value must be a string")
        if (
            check_event_outcomes
            and event in RESULT_OUTCOMES
            and "outcome" in occurrence
            and occurrence["outcome"] not in RESULT_OUTCOMES[event]
        ):
            raise ValueError(f"{occurrence_label} has an invalid result outcome")
        if event == "prior_integration" and "outcome" in occurrence:
            if occurrence["outcome"] not in {"green", "non_green", "unevaluable"}:
                raise ValueError(f"{occurrence_label} has an invalid prior integration result")
        if event == "review_verdict" and "outcome" in occurrence:
            if occurrence["outcome"] not in {"clear", "blocking"}:
                raise ValueError(f"{occurrence_label} has an invalid review verdict")


def validate_trace_shape(trace, vocabulary, label):
    if not isinstance(trace, list):
        raise ValueError(f"{label} must be an array")
    for index, occurrence in enumerate(trace):
        occurrence_label = f"{label}[{index}]"
        if not isinstance(occurrence, dict):
            raise ValueError(f"{occurrence_label} must be an object")
        event = occurrence.get("event")
        if event not in vocabulary["event"]:
            raise ValueError(f"{occurrence_label} has unknown event or lacks event")
        schema = EVENT_METADATA_SCHEMA[event]
        if not set(occurrence).issubset(schema["allowed"]):
            raise ValueError(f"{occurrence_label} has keys not allowed for {event}")
        for key, value in occurrence.items():
            if type(value) is not schema["types"][key]:
                raise ValueError(f"{occurrence_label}.{key} has the wrong type")


def validate_required_metadata(trace, vocabulary):
    result_reasons = {
        "task_verification": "task verification requires a non-empty closed outcome",
        "task_verifications_complete": "task verifications complete requires a non-empty closed outcome",
        "merge_precondition": "merge precondition requires a non-empty closed outcome",
        "merge_gate": "merge gate requires a non-empty closed outcome",
        "merge_gates_complete": "merge gates complete requires a non-empty closed outcome",
        "regeneration": "regeneration requires a non-empty closed outcome",
        "wiring": "wiring requires a non-empty closed outcome",
        "integration_gate": "integration gate requires a non-empty closed outcome",
        "external_evidence": "external evidence requires a non-empty closed outcome",
        "completion_gate": "completion gate requires a non-empty closed outcome",
        "completion_full_verify": "completion full verify requires a non-empty closed outcome",
        "runtime_smoke": "runtime smoke requires a non-empty closed outcome",
        "conditional_spec_review": "conditional spec review requires an actual result",
        "final_full_diff_review": "final full-diff review requires an actual result",
        "review_verdict": "review verdict requires a non-empty closed outcome",
    }
    completion_value_reasons = {
        "prior_verify_set": "completion reuse requires the prior verify set",
        "completion_verify_set": "completion reuse requires the completion verify set",
        "prior_gate_base_tip": "completion reuse requires the prior gate base-tip SHA",
        "current_base_tip": "completion reuse requires the current base-tip SHA",
    }
    review_owners = {
        "conditional_spec_review": (
            "reviewer",
            "conditional spec review must be fresh-reviewer-owned",
        ),
        "final_full_diff_review": (
            "reviewer",
            "final full-diff review must be fresh-reviewer-owned",
        ),
        "review_verdict": (
            "reviewer",
            "review verdict must be fresh-reviewer-owned",
        ),
        "completion": (
            "orchestrator",
            "completion and user gate must be orchestrator-owned",
        ),
        "user_gate": (
            "orchestrator",
            "completion and user gate must be orchestrator-owned",
        ),
    }
    for occurrence in trace:
        event = occurrence["event"]
        if event in review_owners:
            expected_owner, reason = review_owners[event]
            if occurrence.get("owner") != expected_owner:
                return "RUN-REVIEW-TOPOLOGY", reason
        if event == "route_selected":
            if occurrence.get("route") not in vocabulary["route"]:
                return "RUN-ROUTE-TOPOLOGY", "selected route is outside the closed route vocabulary"
            if occurrence.get("owner") != "orchestrator":
                return "RUN-ROUTE-TOPOLOGY", "route selection must be orchestrator-owned"
        if event in RESULT_OUTCOMES and occurrence.get("outcome") not in RESULT_OUTCOMES[event]:
            invariant_id = (
                "RUN-REVIEW-TOPOLOGY"
                if event in {
                    "conditional_spec_review",
                    "final_full_diff_review",
                    "review_verdict",
                }
                else "RUN-FAIL-CLOSED"
            )
            return invariant_id, result_reasons[event]
        if event == "prior_integration" and occurrence.get("outcome") not in {
            "green",
            "non_green",
            "unevaluable",
        }:
            return "RUN-COMPLETION-REUSE", "prior integration requires a non-empty closed outcome"
        if event == "review_verdict" and occurrence.get("outcome") not in {"clear", "blocking"}:
            return "RUN-REVIEW-TOPOLOGY", "review verdict requires a non-empty closed outcome"
        if event in REVIEW_CORRELATION_EVENTS and not occurrence.get("task_id"):
            return (
                "RUN-REVIEW-TOPOLOGY",
                "conditional review facts and result require a non-empty task_id",
            )
        if event == "failure_overlay_entered":
            if occurrence.get("overlay") != "failure":
                return "RUN-FAIL-CLOSED", "failure overlay requires explicit failure identity"
            if occurrence.get("owner") != "runtime_failure_overlay":
                return "RUN-FAIL-CLOSED", "failure overlay must be runtime-failure-overlay-owned"
        if event == "selected_base" and not occurrence.get("value"):
            return "RUN-EXTERNAL-PROOF", "external selected base requires a non-empty scalar value"
        if event == "external_base_pin" and not occurrence.get("value"):
            return "RUN-EXTERNAL-PROOF", "external base pin requires a non-empty scalar value"
        if event in completion_value_reasons and not occurrence.get("value"):
            return "RUN-COMPLETION-REUSE", completion_value_reasons[event]
    return None


def validate_assertions(assertions, vocabulary, label):
    if not isinstance(assertions, list) or not assertions:
        raise ValueError(f"{label} must be a non-empty array")
    expected_keys = {
        "count": {"op", "event", "filter", "expected"},
        "forbid": {"op", "event", "filter"},
        "before": {"op", "event_a", "event_b"},
        "same": {"op", "event_a", "field_a", "event_b", "field_b"},
        "owner": {"op", "event", "expected_owner"},
    }
    for index, assertion in enumerate(assertions):
        assertion_label = f"{label}[{index}]"
        if not isinstance(assertion, dict):
            raise ValueError(f"{assertion_label} must be an object")
        operator = assertion.get("op")
        if operator not in ASSERTION_OPERATORS:
            raise ValueError(f"{assertion_label} has an unknown assertion operator")
        require_exact_keys(assertion, expected_keys[operator], assertion_label)

        event_keys = [key for key in assertion if key in {"event", "event_a", "event_b"}]
        for key in event_keys:
            if assertion[key] not in vocabulary["event"]:
                raise ValueError(f"{assertion_label}.{key} has an unknown event")

        if operator in {"count", "forbid"}:
            event = assertion["event"]
            filters = assertion["filter"]
            if not isinstance(filters, dict):
                raise ValueError(f"{assertion_label}.filter must be an object")
            allowed_filters = EVENT_METADATA_SCHEMA[event]["allowed"] - {"event"}
            if not set(filters).issubset(allowed_filters):
                raise ValueError(f"{assertion_label}.filter has an invalid field")
            if any(type(value) is not str for value in filters.values()):
                raise ValueError(f"{assertion_label}.filter values must be strings")
        if operator == "count" and (
            type(assertion["expected"]) is not int or assertion["expected"] < 0
        ):
            raise ValueError(f"{assertion_label}.expected must be a non-negative integer")
        if operator == "same":
            for event_key, field_key in (
                ("event_a", "field_a"),
                ("event_b", "field_b"),
            ):
                allowed_fields = EVENT_METADATA_SCHEMA[assertion[event_key]]["allowed"] - {
                    "event"
                }
                if assertion[field_key] not in allowed_fields:
                    raise ValueError(f"{assertion_label}.{field_key} is invalid for its event")
        if operator == "owner" and assertion["expected_owner"] not in vocabulary["owner"]:
            raise ValueError(f"{assertion_label}.expected_owner is unknown")


def evaluate_assertions(trace, assertions):
    """Evaluate fixture literals without consulting the semantic validator."""

    def occurrences(event, filters=None):
        filters = filters or {}
        return [
            occurrence
            for occurrence in trace
            if occurrence.get("event") == event
            and all(occurrence.get(key) == value for key, value in filters.items())
        ]

    failures = []
    for index, assertion in enumerate(assertions):
        operator = assertion["op"]
        passed = False
        if operator == "count":
            passed = (
                len(occurrences(assertion["event"], assertion["filter"]))
                == assertion["expected"]
            )
        elif operator == "forbid":
            passed = not occurrences(assertion["event"], assertion["filter"])
        elif operator == "before":
            first = [
                trace_index
                for trace_index, occurrence in enumerate(trace)
                if occurrence.get("event") == assertion["event_a"]
            ]
            second = [
                trace_index
                for trace_index, occurrence in enumerate(trace)
                if occurrence.get("event") == assertion["event_b"]
            ]
            passed = bool(first and second) and max(first) < min(second)
        elif operator == "same":
            first = occurrences(assertion["event_a"])
            second = occurrences(assertion["event_b"])
            passed = (
                len(first) == 1
                and len(second) == 1
                and assertion["field_a"] in first[0]
                and assertion["field_b"] in second[0]
                and first[0][assertion["field_a"]]
                == second[0][assertion["field_b"]]
            )
        elif operator == "owner":
            owned = occurrences(assertion["event"])
            passed = bool(owned) and all(
                occurrence.get("owner") == assertion["expected_owner"]
                for occurrence in owned
            )
        if not passed:
            failures.append(f"assertions[{index}] {operator} failed")
    return failures


def validate_fixture(fixture, vocabulary):
    require_exact_keys(
        fixture,
        {
            "schema_version",
            "behavior_origin_commit",
            "assertion_language",
            "scenarios",
            "mutants",
        },
        "fixture",
    )
    if type(fixture["schema_version"]) is not int or fixture["schema_version"] != 1:
        raise ValueError("fixture schema_version must be integer 1")
    if fixture["behavior_origin_commit"] != "fb252b4236cc607002e131210f6161db72f6841e":
        raise ValueError("fixture behavior_origin_commit is not protected v1.8.1")
    if fixture["assertion_language"] != ASSERTION_OPERATORS:
        raise ValueError("fixture assertion language must exactly match the closed operators")

    seen_ids = set()
    for collection_name, expected_keys, expected_valid, expected_outcome in (
        (
            "scenarios",
            {"id", "trace", "assertions", "expected_valid", "expected_outcome"},
            True,
            "accepted",
        ),
        (
            "mutants",
            {
                "id",
                "trace",
                "assertions",
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
            if collection_name == "scenarios":
                actual_keys = set(item)
                allowed_keys = set(expected_keys).union({"failure_case"})
                if actual_keys != set(expected_keys) and actual_keys != allowed_keys:
                    raise ValueError(
                        f"{label} keys must be {sorted(expected_keys)} or "
                        f"{sorted(allowed_keys)}, got {sorted(actual_keys)}"
                    )
            else:
                require_exact_keys(item, expected_keys, label)
            if not isinstance(item["id"], str) or not item["id"] or item["id"] in seen_ids:
                raise ValueError(f"{label}.id must be non-empty and unique")
            seen_ids.add(item["id"])
            if item["expected_valid"] is not expected_valid:
                raise ValueError(f"{label}.expected_valid has the wrong literal")
            if item["expected_outcome"] != expected_outcome:
                raise ValueError(f"{label}.expected_outcome has the wrong literal")
            validate_trace(
                item["trace"],
                vocabulary,
                f"{label}.trace",
                check_event_outcomes=collection_name == "scenarios",
            )
            validate_assertions(item["assertions"], vocabulary, f"{label}.assertions")
            assertion_failures = evaluate_assertions(item["trace"], item["assertions"])
            if assertion_failures:
                raise ValueError(
                    f"{label}.assertions do not match the fixture trace: {assertion_failures}"
                )
            if collection_name == "scenarios" and "failure_case" in item:
                failure_case = item["failure_case"]
                require_exact_keys(
                    failure_case,
                    {"event", "outcome", "expected_contract_id", "expected_reason"},
                    f"{label}.failure_case",
                )
                event = failure_case["event"]
                outcome = failure_case["outcome"]
                if event not in RESULT_EVENTS:
                    raise ValueError(f"{label}.failure_case.event is not a result event")
                if outcome not in RESULT_OUTCOMES[event].intersection(FAILURE_OUTCOMES):
                    raise ValueError(f"{label}.failure_case.outcome is not a closed failure outcome")
                if failure_case["expected_contract_id"] != "RUN-FAIL-CLOSED":
                    raise ValueError(f"{label}.failure_case has the wrong expected contract")
                if not isinstance(failure_case["expected_reason"], str) or not failure_case["expected_reason"]:
                    raise ValueError(f"{label}.failure_case expected reason must be non-empty")
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


def result_failed(occurrence):
    return occurrence.get("outcome") in FAILURE_OUTCOMES


ROUTE_SPECIFIC_EVENTS = {
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
}
ROUTE_ALLOWED_EVENTS = {
    "direct": {"task_implementation", "evidence_captured", "base_commit"},
    "single_risky": {
        "worktree_created",
        "task_implementation",
        "evidence_captured",
        "task_verification",
        "merge_precondition",
        "merge_gate",
        "task_merged",
    },
    "parallel": {
        "isolated_task_worktrees",
        "worktree_created",
        "task_implementation",
        "task_verification",
        "task_verifications_complete",
        "merge_gate",
        "merge_gates_complete",
        "serial_merge",
        "task_merged",
        "regeneration",
        "wiring",
        "integration_gate",
    },
    "external": {
        "selected_base",
        "external_base_pin",
        "external_action",
        "external_evidence",
        "base_commit",
        "conditional_base_commit",
        "independent_commit_proof",
    },
}
ROUTE_STAGE_ORDER = {
    "direct": ["task_implementation", "evidence_captured", "base_commit"],
    "single_risky": [
        "worktree_created",
        "task_implementation",
        "evidence_captured",
        "task_verification",
        "merge_precondition",
        "merge_gate",
        "task_merged",
    ],
    "parallel": [
        "isolated_task_worktrees",
        "worktree_created",
        "task_implementation",
        "task_verification",
        "task_verifications_complete",
        "merge_gate",
        "merge_gates_complete",
        "serial_merge",
        "task_merged",
        "regeneration",
        "wiring",
        "integration_gate",
    ],
    "external": [
        "selected_base",
        "external_base_pin",
        "external_action",
        "external_evidence",
        "base_commit",
        "independent_commit_proof",
    ],
}


def first_failed_result_index(trace):
    return next(
        (
            index
            for index, occurrence in enumerate(trace)
            if occurrence.get("event") in RESULT_EVENTS and result_failed(occurrence)
        ),
        None,
    )


REMEDIAL_EVENTS = {
    "remedial_worktree_created",
    "remedial_implementer_continuation",
}


def validate_direct_remedial_topology(trace, route_index):
    if not any(occurrence.get("event") in REMEDIAL_EVENTS for occurrence in trace):
        return None
    if trace[route_index].get("route") != "direct":
        return "post-failure remedial topology requires the selected direct route"
    worktrees = matching_indexes(trace, "remedial_worktree_created")
    continuations = matching_indexes(trace, "remedial_implementer_continuation")
    if len(worktrees) != 1 or len(continuations) != 1:
        return "direct remediation requires one remedial worktree and implementer continuation"
    if trace[worktrees[0]].get("owner") != "orchestrator":
        return "direct remedial worktree must be orchestrator-owned"
    if trace[continuations[0]].get("owner") != "implementer":
        return "direct remedial continuation must be implementer-owned"
    failures = [
        index
        for index, occurrence in enumerate(trace)
        if occurrence.get("event") in RESULT_EVENTS and result_failed(occurrence)
    ]
    overlays = matching_indexes(trace, "failure_overlay_entered", overlay="failure")
    if not any(
        route_index < failure < overlay < worktrees[0] < continuations[0]
        and trace[overlay].get("owner") == "runtime_failure_overlay"
        for failure in failures
        for overlay in overlays
    ):
        return (
            "direct substantive failure must precede failure overlay, remedial worktree, "
            "and implementer continuation"
        )
    return None


ROUTE_EVENT_OWNERS = {
    "direct": {
        "route_selected": "orchestrator",
        "task_implementation": "orchestrator",
        "evidence_captured": "orchestrator",
        "base_commit": "orchestrator",
    },
    "single_risky": {
        "route_selected": "orchestrator",
        "worktree_created": "orchestrator",
        "task_implementation": "implementer",
        "evidence_captured": "implementer",
        "task_verification": "implementer",
        "merge_precondition": "orchestrator",
        "merge_gate": "orchestrator",
        "task_merged": "orchestrator",
    },
    "parallel": {
        "route_selected": "orchestrator",
        "isolated_task_worktrees": "orchestrator",
        "worktree_created": "orchestrator",
        "task_implementation": "implementer",
        "task_verification": "implementer",
        "task_verifications_complete": "orchestrator",
        "merge_gate": "orchestrator",
        "merge_gates_complete": "orchestrator",
        "serial_merge": "orchestrator",
        "task_merged": "orchestrator",
        "regeneration": "orchestrator",
        "wiring": "orchestrator",
        "integration_gate": "orchestrator",
    },
    "external": {
        "route_selected": "orchestrator",
        "selected_base": "orchestrator",
        "external_base_pin": "implementer",
        "external_action": "implementer",
        "external_evidence": "implementer",
        "base_commit": "implementer",
        "independent_commit_proof": "orchestrator",
    },
}
SINGLE_RISKY_OWNER_REASONS = {
    "worktree_created": "single-risky worktree must be orchestrator-owned",
    "task_implementation": "single-risky implementation must be implementer-owned",
    "evidence_captured": "single-risky evidence must be implementer-owned",
    "task_verification": "single-risky verification must be implementer-owned",
    "merge_precondition": "single-risky merge precondition must be orchestrator-owned",
    "merge_gate": "single-risky merge gate must be orchestrator-owned",
    "task_merged": "single-risky merge must be orchestrator-owned",
}
ROUTE_OWNER_REASONS = {
    "direct": {
        "route_selected": "route selection must be orchestrator-owned",
        "task_implementation": "direct implementation must be orchestrator-owned",
        "evidence_captured": "direct evidence must be orchestrator-owned",
        "base_commit": "direct base commit must be orchestrator-owned",
    },
    "single_risky": {
        "route_selected": "route selection must be orchestrator-owned",
        **SINGLE_RISKY_OWNER_REASONS,
    },
    "parallel": {
        **{
            event: f"parallel route {event} must be {owner}-owned"
            for event, owner in ROUTE_EVENT_OWNERS["parallel"].items()
        },
        "route_selected": "route selection must be orchestrator-owned",
    },
    "external": {
        "route_selected": "route selection must be orchestrator-owned",
        "selected_base": "external selected base must be orchestrator-owned",
        "external_base_pin": "external base pin must be implementer-owned",
        "external_action": "external action must be implementer-owned",
        "external_evidence": "external evidence must be implementer-owned",
        "base_commit": "external base commit must be implementer-owned",
        "independent_commit_proof": "external commit proof must be independently owned",
    },
}


def validate_route_event_contract(trace, route, boundary_index):
    prefix = trace[: boundary_index + 1]
    repeatable = TASK_CORRELATION_EVENTS if route == "parallel" else set()
    for event in ["route_selected", *ROUTE_STAGE_ORDER[route]]:
        indexes = matching_indexes(prefix, event)
        if event not in repeatable and len(indexes) > 1:
            return f"{route.replace('_', '-')} route requires exactly one {event}"
        expected_owner = ROUTE_EVENT_OWNERS[route][event]
        if any(trace[index].get("owner") != expected_owner for index in indexes):
            return ROUTE_OWNER_REASONS[route][event]

    if route == "single_risky":
        task_ids = [
            trace[index].get("task_id")
            for event in TASK_CORRELATION_EVENTS
            for index in matching_indexes(prefix, event)
        ]
        if task_ids and (any(not task_id for task_id in task_ids) or len(set(task_ids)) != 1):
            return "single-risky per-task events must correlate by task_id"

    if route == "parallel":
        reached = [
            event
            for event in TASK_CORRELATION_EVENTS
            if matching_indexes(prefix, event)
        ]
        if reached:
            worktrees = route_task_index_map(prefix, "worktree_created")
            if worktrees is None or len(worktrees) < 2:
                return "parallel route requires at least two isolated task worktrees with stable task_id"
            task_ids = set(worktrees)
            for event in reached:
                event_indexes = route_task_index_map(prefix, event)
                failure_stage = (
                    event == trace[boundary_index].get("event")
                    and result_failed(trace[boundary_index])
                )
                correlated_ids = set(event_indexes or {})
                if event_indexes is None or (
                    failure_stage
                    and (not correlated_ids or not correlated_ids.issubset(task_ids))
                ) or (not failure_stage and correlated_ids != task_ids):
                    return "parallel task work, verification, gate, and merge evidence must correlate by task_id"
    return None


def route_task_index_map(trace, event):
    indexes = matching_indexes(trace, event)
    result = {}
    for index in indexes:
        task_id = trace[index].get("task_id")
        if not task_id or task_id in result:
            return None
        result[task_id] = index
    return result


def validate_reached_route_prefix(
    trace,
    route,
    route_index,
    failure_index,
    *,
    stage_order=None,
):
    stages = list(stage_order or ROUTE_STAGE_ORDER[route])
    if any(
        index > failure_index and occurrence.get("event") in ROUTE_ALLOWED_EVENTS[route]
        for index, occurrence in enumerate(trace)
    ):
        return f"{route.replace('_', '-')} route cannot advance after a failed result"
    prefix = trace[: failure_index + 1]
    positions = []
    repeatable = TASK_CORRELATION_EVENTS if route == "parallel" else set()
    for position, event in enumerate(stages):
        indexes = matching_indexes(prefix, event)
        if len(indexes) > 1 and event not in repeatable:
            if route == "single_risky":
                return f"single-risky route requires exactly one {event}"
            return f"{route.replace('_', '-')} route prefix contains duplicate {event}"
        if indexes:
            positions.append((position, min(indexes), max(indexes)))

    for event, owner in ROUTE_EVENT_OWNERS[route].items():
        indexes = matching_indexes(prefix, event)
        if indexes and any(trace[index].get("owner") != owner for index in indexes):
            if route == "single_risky":
                return SINGLE_RISKY_OWNER_REASONS[event]
            return f"{route.replace('_', '-')} route prefix has wrong {event} owner"

    if route == "parallel":
        reached_task_events = [
            event
            for event in stages
            if event in TASK_CORRELATION_EVENTS and has_event(prefix, event)
        ]
        if reached_task_events:
            worktrees = route_task_index_map(prefix, "worktree_created")
            if worktrees is None or len(worktrees) < 2:
                return "parallel route requires at least two isolated task worktrees with stable task_id"
            task_ids = set(worktrees)
            for event in reached_task_events:
                indexes = route_task_index_map(prefix, event)
                failure_stage = (
                    event == trace[failure_index].get("event")
                    and result_failed(trace[failure_index])
                )
                correlated_ids = set(indexes or {})
                if indexes is None or (
                    failure_stage
                    and (not correlated_ids or not correlated_ids.issubset(task_ids))
                ) or (not failure_stage and correlated_ids != task_ids):
                    return "parallel task work, verification, gate, and merge evidence must correlate by task_id"

    if route == "single_risky":
        task_ids = [
            trace[index].get("task_id")
            for event in TASK_CORRELATION_EVENTS
            for index in matching_indexes(prefix, event)
        ]
        if task_ids and (any(not task_id for task_id in task_ids) or len(set(task_ids)) != 1):
            return "single-risky per-task events must correlate by task_id"
        verification = matching_indexes(prefix, "task_verification")
        precondition = matching_indexes(prefix, "merge_precondition")
        merged = matching_indexes(prefix, "task_merged")
        if verification and merged and merged[0] < verification[0]:
            return "single-risky verification must precede merge"
        if (
            "merge_precondition" in stages
            and precondition
            and merged
            and merged[0] < precondition[0]
        ):
            return "single-risky merge precondition must precede merge"
    if positions:
        highest_position = positions[-1][0]
        if [position for position, _, _ in positions] != list(range(highest_position + 1)):
            return f"{route.replace('_', '-')} route prefix skips a required stage"
        if route_index >= positions[0][1] or any(
            left[2] >= right[1] for left, right in zip(positions, positions[1:])
        ):
            return f"{route.replace('_', '-')} route prefix is out of order"
    owner_requirements = {
        "task_implementation": "orchestrator" if route == "direct" else "implementer",
        "external_base_pin": "implementer",
        "external_action": "implementer",
        "independent_commit_proof": "orchestrator",
    }
    for event, owner in owner_requirements.items():
        for index in matching_indexes(prefix, event):
            if trace[index].get("owner") != owner:
                return f"{route.replace('_', '-')} route prefix has wrong {event} owner"
    for index, occurrence in enumerate(prefix):
        if occurrence.get("event") in RESULT_EVENTS and occurrence.get("event") in stages:
            if index != failure_index and occurrence.get("outcome") not in {"green", "clear"}:
                return f"{route.replace('_', '-')} route prefix contains a failed result"
    if route == "external" and has_event(prefix, "conditional_base_commit"):
        return "external base commit must not be conditional"
    return None


def validate_route_topology(trace):
    selected = matching_indexes(trace, "route_selected")
    if not selected:
        if any(
            item.get("event") in ROUTE_SPECIFIC_EVENTS.union(REMEDIAL_EVENTS)
            for item in trace
        ):
            return "route-specific events require exactly one selected route"
        return None
    if len(selected) != 1:
        return "a success route must be selected exactly once"
    route = trace[selected[0]].get("route")
    if route not in ROUTE_ALLOWED_EVENTS:
        return "selected route is outside the closed route vocabulary"
    remedial_reason = validate_direct_remedial_topology(trace, selected[0])
    if remedial_reason is not None:
        return remedial_reason
    if route == "direct":
        direct_owner_reasons = {
            "task_implementation": "direct implementation must be orchestrator-owned",
            "evidence_captured": "direct evidence must be orchestrator-owned",
            "base_commit": "direct base commit must be orchestrator-owned",
        }
        for event, reason in direct_owner_reasons.items():
            indexes = matching_indexes(trace, event)
            if indexes and any(trace[index].get("owner") != "orchestrator" for index in indexes):
                return reason
    for occurrence in trace:
        event = occurrence.get("event")
        if event in ROUTE_SPECIFIC_EVENTS and event not in ROUTE_ALLOWED_EVENTS[route]:
            return f"{route.replace('_', '-')} route forbids route-specific event {event}"
    failure_index = first_failed_result_index(trace)
    route_contract_reason = validate_route_event_contract(
        trace,
        route,
        failure_index if failure_index is not None else len(trace) - 1,
    )
    if route_contract_reason is not None:
        return route_contract_reason
    if failure_index is not None:
        return validate_reached_route_prefix(trace, route, selected[0], failure_index)
    if route == "direct":
        checks = (
            (owner_is(trace, "task_implementation", "orchestrator"), "direct implementation must be orchestrator-owned"),
            (len(matching_indexes(trace, "evidence_captured")) == 1, "direct route requires captured evidence"),
            (len(matching_indexes(trace, "base_commit")) == 1, "direct route requires one base commit"),
            (not has_event(trace, "worktree_created"), "direct route forbids a task worktree"),
            (not has_event(trace, "integration_gate"), "direct route has no wave integration gate"),
        )
        for passed, reason in checks:
            if not passed:
                return reason
        if not ordered(trace, "route_selected", "task_implementation"):
            return "direct implementation must follow route selection"
        if not ordered(trace, "task_implementation", "evidence_captured"):
            return "direct implementation must precede captured evidence"
        if not ordered(trace, "evidence_captured", "base_commit"):
            return "direct evidence must precede base commit"
        return None
    if route == "single_risky":
        structural_trace = (
            trace if failure_index is None else trace[: failure_index + 1]
        )
        for event in ROUTE_STAGE_ORDER["single_risky"]:
            indexes = matching_indexes(structural_trace, event)
            if len(indexes) > 1:
                return f"single-risky route requires exactly one {event}"
            if (
                indexes
                and structural_trace[indexes[0]].get("owner")
                != ROUTE_EVENT_OWNERS[route][event]
            ):
                return SINGLE_RISKY_OWNER_REASONS[event]
        checks = (
            (len(matching_indexes(trace, "worktree_created")) == 1, "single-risky route requires one task worktree"),
            (owner_is(trace, "task_implementation", "implementer"), "single-risky implementation must be implementer-owned"),
            (len(matching_indexes(trace, "evidence_captured")) == 1, "single-risky route requires captured implementer evidence"),
        )
        for passed, reason in checks:
            if not passed:
                return reason
        verification = matching_indexes(trace, "task_verification")
        if len(verification) != 1:
            return "single-risky route requires green task verification"
        if not ordered(structural_trace, "route_selected", "worktree_created"):
            return "single-risky worktree must follow route selection"
        if not ordered(structural_trace, "worktree_created", "task_implementation"):
            return "single-risky worktree must precede implementation"
        if not ordered(structural_trace, "task_implementation", "evidence_captured"):
            return "single-risky implementation must precede captured evidence"
        if not ordered(structural_trace, "evidence_captured", "task_verification"):
            return "single-risky captured evidence must precede verification"
        implementation_prefix = [
            index
            for index in matching_indexes(trace, "task_implementation")
            if index < verification[0]
        ]
        if len(implementation_prefix) != 1:
            return "single-risky implementation must precede verification"
        if has_event(trace, "task_merged") and not ordered(trace, "task_verification", "task_merged"):
            return "single-risky verification must precede merge"
        if result_failed(trace[verification[0]]):
            if any(
                has_event(trace, event)
                for event in ("merge_precondition", "merge_gate", "task_merged")
            ):
                return "single-risky route cannot advance after a failed result"
            return None
        if trace[verification[0]].get("outcome") != "green":
            return "single-risky route requires green task verification"

        preconditions = matching_indexes(trace, "merge_precondition")
        if len(preconditions) != 1:
            return "single-risky route requires a green merge precondition"
        if not ordered(trace, "task_verification", "merge_precondition"):
            return "single-risky verification must precede merge precondition"
        if result_failed(trace[preconditions[0]]):
            if any(has_event(trace, event) for event in ("merge_gate", "task_merged")):
                return "single-risky route cannot advance after a failed result"
            return None
        if trace[preconditions[0]].get("outcome") != "green":
            return "single-risky route requires a green merge precondition"
        if has_event(trace, "task_merged") and not ordered(
            trace, "merge_precondition", "task_merged"
        ):
            return "single-risky merge precondition must precede merge"

        gates = matching_indexes(trace, "merge_gate")
        if len(gates) != 1:
            return "single-risky route requires a green merge gate"
        if not ordered(trace, "merge_precondition", "merge_gate"):
            return "single-risky merge precondition must precede merge gate"
        if result_failed(trace[gates[0]]):
            if has_event(trace, "task_merged"):
                return "single-risky route cannot advance after a failed result"
            return None
        if trace[gates[0]].get("outcome") != "green":
            return "single-risky route requires a green merge gate"
        if len(matching_indexes(trace, "task_merged")) != 1:
            return "single-risky route requires exactly one task_merged"
        if not ordered(trace, "merge_precondition", "task_merged"):
            return "single-risky merge precondition must precede merge"
        if not ordered(trace, "merge_gate", "task_merged"):
            return "single-risky merge gate must precede merge"
        return None
    if route == "parallel":
        isolation = matching_indexes(trace, "isolated_task_worktrees")
        if len(isolation) != 1:
            return "parallel route requires isolated task worktrees"
        if trace[isolation[0]].get("owner") != "orchestrator":
            return "parallel isolation must be orchestrator-owned"
        if not ordered(trace, "route_selected", "isolated_task_worktrees"):
            return "parallel isolation must follow route selection"

        def task_index_map(event):
            indexes = matching_indexes(trace, event)
            result = {}
            for index in indexes:
                task_id = trace[index].get("task_id")
                if not task_id or task_id in result:
                    return None
                result[task_id] = index
            return result

        worktrees = task_index_map("worktree_created")
        implementations = task_index_map("task_implementation")
        verifications = task_index_map("task_verification")
        if worktrees is None or len(worktrees) < 2:
            return "parallel route requires at least two isolated task worktrees with stable task_id"
        task_ids = set(worktrees)
        if implementations is None or verifications is None or any(
            set(indexes) != task_ids for indexes in (implementations, verifications)
        ):
            return "parallel task work, verification, gate, and merge evidence must correlate by task_id"
        owner_requirements = {
            "worktree_created": "orchestrator",
            "task_implementation": "implementer",
            "task_verification": "implementer",
        }
        for event, owner in owner_requirements.items():
            if not owner_is(trace, event, owner):
                return f"parallel {event} must be {owner}-owned"
        for task_id in task_ids:
            if not (
                isolation[0]
                < worktrees[task_id]
                < implementations[task_id]
                < verifications[task_id]
            ):
                return "parallel per-task worktree, implementation, and verification are out of order"

        failed_verifications = [
            index for index in verifications.values() if result_failed(trace[index])
        ]
        if failed_verifications:
            first_failure = min(failed_verifications)
            if any(
                index > first_failure
                and occurrence.get("event")
                in {
                    "task_verifications_complete",
                    "merge_gate",
                    "merge_gates_complete",
                    "serial_merge",
                    "task_merged",
                    "regeneration",
                    "wiring",
                    "integration_gate",
                }
                for index, occurrence in enumerate(trace)
            ):
                return "parallel route cannot advance after a failed result"
            return None
        if any(trace[index].get("outcome") != "green" for index in verifications.values()):
            return "parallel route requires green per-task verification"

        results = matching_indexes(trace, "task_verifications_complete")
        if len(results) != 1:
            return "parallel route requires green task verification"
        if max(verifications.values()) >= results[0]:
            return "parallel task verification must precede aggregate verification result"
        if result_failed(trace[results[0]]):
            if any(
                index > results[0]
                and occurrence.get("event")
                in {
                    "merge_gate",
                    "merge_gates_complete",
                    "serial_merge",
                    "task_merged",
                    "regeneration",
                    "wiring",
                    "integration_gate",
                }
                for index, occurrence in enumerate(trace)
            ):
                return "parallel route cannot advance after a failed result"
            return None
        if trace[results[0]].get("outcome") != "green":
            return "parallel route requires green task verification"

        gates = task_index_map("merge_gate")
        if gates is None or set(gates) != task_ids:
            return "parallel task work, verification, gate, and merge evidence must correlate by task_id"
        if not owner_is(trace, "merge_gate", "orchestrator"):
            return "parallel merge gates must be orchestrator-owned"
        for task_id in task_ids:
            if not results[0] < gates[task_id]:
                return "parallel aggregate verification must precede every branch gate"
        failed_gates = [index for index in gates.values() if result_failed(trace[index])]
        if failed_gates:
            first_failure = min(failed_gates)
            if any(
                index > first_failure
                and occurrence.get("event")
                in {
                    "merge_gates_complete",
                    "serial_merge",
                    "task_merged",
                    "regeneration",
                    "wiring",
                    "integration_gate",
                }
                for index, occurrence in enumerate(trace)
            ):
                return "parallel route cannot advance after a failed result"
            return None
        if any(trace[index].get("outcome") != "green" for index in gates.values()):
            return "parallel route requires green per-task merge gates"

        merge_results = matching_indexes(trace, "merge_gates_complete")
        if len(merge_results) != 1:
            return "parallel route requires green merge gates"
        if max(gates.values()) >= merge_results[0]:
            return "parallel branch gates must precede aggregate merge-gates result"
        if result_failed(trace[merge_results[0]]):
            if any(
                index > merge_results[0]
                and occurrence.get("event")
                in {"serial_merge", "task_merged", "regeneration", "wiring", "integration_gate"}
                for index, occurrence in enumerate(trace)
            ):
                return "parallel route cannot advance after a failed result"
            return None
        if trace[merge_results[0]].get("outcome") != "green":
            return "parallel route requires green merge gates"

        serial_merges = matching_indexes(trace, "serial_merge")
        if len(serial_merges) != 1:
            return "parallel route requires serial merge"
        if merge_results[0] >= serial_merges[0]:
            return "parallel merge gates must precede serial merge"
        merged = task_index_map("task_merged")
        if merged is None or set(merged) != task_ids:
            return "parallel task work, verification, gate, and merge evidence must correlate by task_id"
        if not owner_is(trace, "task_merged", "orchestrator"):
            return "parallel task merges must be orchestrator-owned"
        if any(serial_merges[0] >= index for index in merged.values()):
            return "parallel serial merge must precede every correlated task merge"

        regeneration = matching_indexes(trace, "regeneration")
        if len(regeneration) != 1:
            return "parallel route requires green regeneration"
        if max(merged.values()) >= regeneration[0]:
            return "parallel task merges must precede regeneration"
        if result_failed(trace[regeneration[0]]):
            if any(has_event(trace, event) for event in ("wiring", "integration_gate")):
                return "parallel route cannot advance after a failed result"
            return None
        if trace[regeneration[0]].get("outcome") != "green":
            return "parallel route requires green regeneration"

        wiring = matching_indexes(trace, "wiring")
        if len(wiring) != 1:
            return "parallel route requires green wiring"
        if regeneration[0] >= wiring[0]:
            return "parallel regeneration must precede wiring"
        if result_failed(trace[wiring[0]]):
            if has_event(trace, "integration_gate"):
                return "parallel route cannot advance after a failed result"
            return None
        if trace[wiring[0]].get("outcome") != "green":
            return "parallel route requires green wiring"

        integration = matching_indexes(trace, "integration_gate")
        if len(integration) != 1:
            return "parallel route requires one green integration gate"
        if wiring[0] >= integration[0]:
            return "parallel wiring must precede integration gate"
        if result_failed(trace[integration[0]]):
            return None
        if trace[integration[0]].get("outcome") != "green":
            return "parallel route requires one green integration gate"
        return None
    if route == "external":
        checks = (
            (owner_is(trace, "external_action", "implementer"), "external action must be implementer-owned"),
            (not has_event(trace, "worktree_created"), "external route forbids a task worktree"),
            (not has_event(trace, "isolated_task_worktrees"), "external route forbids isolated task worktrees"),
        )
        for passed, reason in checks:
            if not passed:
                return reason
        return None
    return "selected route is outside the closed route vocabulary"


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
    failure_index = first_failed_result_index(trace)
    if (
        failure_index is not None
        and trace[failure_index].get("event") != "external_evidence"
    ):
        prefix = trace[: failure_index + 1]
        if has_event(prefix, "selected_base") and has_event(prefix, "external_base_pin"):
            if not same_single_value(prefix, "selected_base", "external_base_pin"):
                return "external base pin must match the selected base"
        return None
    selected_bases = matching_indexes(trace, "selected_base")
    if len(selected_bases) != 1:
        return "external route requires one selected base"
    if not trace[selected_bases[0]].get("value"):
        return "external selected base requires a non-empty scalar value"
    pins = matching_indexes(trace, "external_base_pin")
    if len(pins) != 1:
        return "external implementer must be pinned to the selected base before action"
    if not trace[pins[0]].get("value"):
        return "external base pin requires a non-empty scalar value"
    if not same_single_value(trace, "selected_base", "external_base_pin"):
        return "external base pin must match the selected base"
    if not ordered(trace, "route_selected", "selected_base"):
        return "external selected base must follow route selection"
    if not owner_is(trace, "external_base_pin", "implementer") or not ordered(
        trace, "selected_base", "external_base_pin"
    ) or not ordered(trace, "external_base_pin", "external_action"):
        return "external implementer must be pinned to the selected base before action"
    if not owner_is(trace, "external_action", "implementer"):
        return "external action must be implementer-owned"

    evidence = matching_indexes(trace, "external_evidence")
    if len(evidence) != 1:
        return "external route requires captured green external evidence"
    if not ordered(trace, "external_action", "external_evidence"):
        return "external action must precede captured evidence"
    if result_failed(trace[evidence[0]]):
        if any(
            has_event(trace, event)
            for event in ("conditional_base_commit", "base_commit", "independent_commit_proof")
        ):
            return "external route cannot advance after a failed result"
        return None
    if trace[evidence[0]].get("outcome") != "green":
        return "external route requires captured green external evidence"

    checks = (
        (len(matching_indexes(trace, "base_commit")) == 1, "external route requires an unconditional base commit"),
        (not has_event(trace, "conditional_base_commit"), "external base commit must not be conditional"),
        (owner_is(trace, "base_commit", "implementer"), "external base commit must be implementer-owned"),
        (len(matching_indexes(trace, "independent_commit_proof")) == 1, "external route requires independent commit proof"),
        (owner_is(trace, "independent_commit_proof", "orchestrator"), "external commit proof must be independently owned"),
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
        "regeneration": "regeneration result",
        "wiring": "wiring result",
        "integration_gate": "integration result",
        "external_evidence": "external evidence",
        "completion_gate": "completion result",
        "completion_full_verify": "completion full verify result",
        "runtime_smoke": "runtime smoke result",
        "conditional_spec_review": "conditional spec review result",
        "final_full_diff_review": "final review result",
        "review_verdict": "review verdict",
    }
    continuations = set(CONTINUATION_EVENTS)
    for result_index, occurrence in enumerate(trace):
        event = occurrence.get("event")
        outcome = occurrence.get("outcome")
        promoted_failure = (
            event == "concern_disposition"
            and occurrence.get("disposition") == "promoted_to_failure"
        )
        if not promoted_failure and (
            event not in phases or outcome not in FAILURE_OUTCOMES
        ):
            continue
        overlays = [
            index
            for index in matching_indexes(trace, "failure_overlay_entered", overlay="failure")
            if index > result_index
        ]
        owned_overlays = [
            index
            for index in overlays
            if trace[index].get("owner") == "runtime_failure_overlay"
        ]
        if not owned_overlays:
            if overlays:
                return "failure overlay must be runtime-failure-overlay-owned"
            if promoted_failure:
                return "promoted concern requires failure overlay"
            return f"{outcome} {phases[event]} must enter failure overlay"
        for continuation_index, later in enumerate(trace):
            if continuation_index <= result_index or later.get("event") not in continuations:
                continue
            if not any(result_index < overlay_index < continuation_index for overlay_index in owned_overlays):
                return "failure overlay must precede any present continuation"
    return None


def non_empty_single_value(trace, event):
    indexes = matching_indexes(trace, event)
    return len(indexes) == 1 and bool(trace[indexes[0]].get("value"))


def validate_completion_reuse(trace):
    reuse_indexes = matching_indexes(trace, "completion_reused")
    reuse = bool(reuse_indexes)
    full_verify = has_event(trace, "completion_full_verify")
    evidence_events = {
        "prior_integration",
        "prior_verify_set",
        "completion_verify_set",
        "prior_gate_base_tip",
        "current_base_tip",
    }
    fact_events = {
        *evidence_events,
        "completion_reused",
    }
    has_fact_context = any(item.get("event") in fact_events for item in trace)
    review_indexes = matching_indexes(trace, "final_full_diff_review")
    review_verdict_indexes = matching_indexes(trace, "review_verdict")
    if len(reuse_indexes) == 1:
        decision_index = reuse_indexes[0]
        evidence_indexes = [
            index
            for index, item in enumerate(trace)
            if item.get("event") in evidence_events
        ]
        if any(index >= decision_index for index in evidence_indexes):
            return "all completion reuse evidence facts must precede the reuse decision"
        review_chain = (
            review_indexes
            + review_verdict_indexes
            + matching_indexes(trace, "completion")
            + matching_indexes(trace, "user_gate")
        )
        if review_chain and decision_index >= min(review_chain):
            return (
                "completion reuse decision must precede final review, verdict, "
                "and endpoint"
            )
    review_and_endpoints = (
        review_indexes
        + review_verdict_indexes
        + matching_indexes(trace, "completion")
        + matching_indexes(trace, "user_gate")
    )
    if review_and_endpoints:
        first_review_or_endpoint = min(review_and_endpoints)
        reuse_fact_indexes = [
            index
            for index, item in enumerate(trace)
            if item.get("event") in fact_events
        ]
        if any(index > first_review_or_endpoint for index in reuse_fact_indexes):
            return (
                "completion reuse facts and decision must precede final review "
                "and endpoint"
            )
    if review_indexes and any(
        index > min(review_indexes)
        for index in matching_indexes(trace, "completion_full_verify")
    ):
        return "completion full verify must precede final review and endpoint"
    if len(reuse_indexes) > 1:
        return "completion reuse decision must occur exactly once"
    unique_fact_reasons = {
        "prior_integration": "completion reuse requires exactly one prior integration result",
        "prior_verify_set": "completion reuse requires exactly one prior verify set",
        "completion_verify_set": "completion reuse requires exactly one completion verify set",
        "prior_gate_base_tip": "completion reuse requires exactly one prior gate base-tip SHA",
        "current_base_tip": "completion reuse requires exactly one current base-tip SHA",
    }
    for event, reason in unique_fact_reasons.items():
        if len(matching_indexes(trace, event)) > 1:
            return reason
    if reuse:
        checks = (
            (len(matching_indexes(trace, "prior_integration", outcome="green")) == 1, "completion reuse requires prior green integration"),
            (non_empty_single_value(trace, "prior_verify_set"), "completion reuse requires the prior verify set"),
            (non_empty_single_value(trace, "completion_verify_set"), "completion reuse requires the completion verify set"),
            (same_single_value(trace, "prior_verify_set", "completion_verify_set"), "completion reuse requires an identical verify set"),
            (non_empty_single_value(trace, "prior_gate_base_tip"), "completion reuse requires the prior gate base-tip SHA"),
            (non_empty_single_value(trace, "current_base_tip"), "completion reuse requires the current base-tip SHA"),
            (same_single_value(trace, "prior_gate_base_tip", "current_base_tip"), "completion reuse requires the same gate and current base-tip SHA"),
            (not full_verify, "matching completion evidence avoids a redundant full verify"),
        )
        for passed, reason in checks:
            if not passed:
                return reason
        return None
    endpoints = sorted(
        matching_indexes(trace, "completion") + matching_indexes(trace, "user_gate")
    )
    if full_verify:
        for endpoint_index in endpoints:
            applicable_verifies = [
                index
                for index in matching_indexes(trace, "completion_full_verify")
                if index < endpoint_index
            ]
            if (
                not applicable_verifies
                or trace[applicable_verifies[-1]].get("outcome") != "green"
            ):
                return (
                    "completion or user gate requires the latest preceding full verify "
                    "to be green"
                )
        return None
    if endpoints:
        if not has_fact_context:
            return "completion endpoint without reusable facts requires full verify"
    if has_fact_context:
        return "incomplete or changed completion facts require full verify"
    return None


def validate_concern_disposition(trace):
    concern_events = {
        "concern_recorded",
        "user_owned_requirement_concern",
        "user_owned_compatibility_concern",
        "user_owned_safety_concern",
    }
    concern_indexes = [
        index for index, item in enumerate(trace) if item.get("event") in concern_events
    ]
    dispositions = matching_indexes(trace, "concern_disposition")
    if not concern_indexes and not dispositions:
        return None
    if not dispositions:
        return "concern must have a closed disposition"
    for disposition_index in dispositions:
        matching_concerns = [
            concern_index
            for concern_index in concern_indexes
            if trace[concern_index].get("value")
            == trace[disposition_index].get("value")
        ]
        if (
            len(matching_concerns) == 1
            and disposition_index < matching_concerns[0]
        ):
            return "recorded concern must precede its correlated disposition"
    for index in dispositions:
        disposition = trace[index].get("disposition")
        if not disposition:
            return "concern disposition requires a non-empty closed value"
        if disposition not in EXPECTED_VOCABULARY["disposition"]:
            return "concern disposition is outside the closed vocabulary"
        if not trace[index].get("value"):
            return "concern disposition must correlate to exactly one recorded concern"
        if disposition == "user_accepted" and trace[index].get("owner") != "user":
            return "user acceptance must be user-owned"

    concern_values = []
    disposition_by_concern = {}
    for index in concern_indexes:
        concern_value = trace[index].get("value")
        if not concern_value or concern_value in concern_values:
            return "concern record requires a unique non-empty correlation value"
        concern_values.append(concern_value)
        matches = [
            disposition_index
            for disposition_index in dispositions
            if trace[disposition_index].get("value") == concern_value
        ]
        if len(matches) != 1:
            return "concern must have exactly one correlated disposition"
        disposition_by_concern[index] = matches[0]
    if any(trace[index].get("value") not in concern_values for index in dispositions):
        return "concern disposition must correlate to exactly one recorded concern"

    endpoints = matching_indexes(trace, "completion") + matching_indexes(trace, "user_gate")
    if endpoints and any(
        not (concern_index < disposition_index < endpoint_index)
        for concern_index, disposition_index in disposition_by_concern.items()
        for endpoint_index in endpoints
    ):
        return "concern record and disposition must precede completion or user gate"

    for index in dispositions:
        disposition = trace[index]["disposition"]
        if disposition == "pending":
            if any(
                endpoint_index > index
                for endpoint_index in matching_indexes(trace, "completion")
            ):
                return "pending concern blocks completion"
            if any(
                endpoint_index > index
                for endpoint_index in matching_indexes(trace, "user_gate")
            ):
                return "pending concern blocks user gate"
        if disposition == "promoted_to_failure":
            later_owned_overlays = [
                overlay_index
                for overlay_index in matching_indexes(
                    trace,
                    "failure_overlay_entered",
                    overlay="failure",
                    owner="runtime_failure_overlay",
                )
                if overlay_index > index
            ]
            if not later_owned_overlays:
                return "promoted concern requires failure overlay"
            if any(
                endpoint_index > index
                for endpoint_index in matching_indexes(trace, "completion")
            ):
                return "failure overlay blocks completion"
            if any(
                endpoint_index > index
                for endpoint_index in matching_indexes(trace, "user_gate")
            ):
                return "failure overlay blocks user gate"

    user_concerns = {
        "user_owned_requirement_concern": "requirement",
        "user_owned_compatibility_concern": "compatibility",
        "user_owned_safety_concern": "safety",
    }
    for event, label in user_concerns.items():
        for concern_index in matching_indexes(trace, event):
            concern_value = trace[concern_index].get("value")
            disposition_index = next(
                index
                for index in dispositions
                if trace[index].get("value") == concern_value
            )
            disposition = trace[disposition_index].get("disposition")
            if disposition in {"pending", "promoted_to_failure"}:
                continue
            if trace[disposition_index].get("owner") != "user":
                return (
                    f"user-owned {label} concern requires user acceptance "
                    "for terminal disposition"
                )
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
    context_events = (
        "risky_task",
        "non_risky_task",
        "downstream_cascade_risk",
        "no_downstream_cascade_risk",
    )
    context_by_event = {}
    for event in context_events:
        task_ids = [trace[index].get("task_id") for index in matching_indexes(trace, event)]
        if any(not task_id for task_id in task_ids):
            return "conditional review facts and result require a non-empty task_id"
        if len(task_ids) != len(set(task_ids)):
            return "review context facts must be unique per task_id"
        context_by_event[event] = set(task_ids)
    risky_ids = context_by_event["risky_task"]
    non_risky_ids = context_by_event["non_risky_task"]
    cascade_ids = context_by_event["downstream_cascade_risk"]
    no_cascade_ids = context_by_event["no_downstream_cascade_risk"]
    if risky_ids.intersection(non_risky_ids):
        return "review risk facts must not contradict for one task_id"
    if cascade_ids.intersection(no_cascade_ids):
        return "review cascade facts must not contradict for one task_id"
    review_facts = any(context_by_event.values())
    conditional_indexes = matching_indexes(trace, "conditional_spec_review")
    final_indexes = matching_indexes(trace, "final_full_diff_review")
    verdict_indexes = matching_indexes(trace, "review_verdict")
    clear_verdicts = matching_indexes(trace, "review_verdict", outcome="clear")
    final_review = bool(final_indexes)

    conditional_by_task = {}
    for index in conditional_indexes:
        occurrence = trace[index]
        task_id = occurrence.get("task_id")
        if not task_id:
            return "conditional review facts and result require a non-empty task_id"
        if task_id in conditional_by_task:
            return "conditional spec review must occur exactly once per task_id"
        conditional_by_task[task_id] = index
        if occurrence.get("owner") != "reviewer":
            return "conditional spec review must be fresh-reviewer-owned"
        if occurrence.get("outcome") not in RESULT_OUTCOMES["conditional_spec_review"]:
            return "conditional spec review requires an actual result"
        if task_id not in risky_ids or task_id not in cascade_ids:
            if risky_ids and cascade_ids:
                return "conditional review facts and result must correlate by task_id"
            return "conditional review applies only to risky downstream cascade"

    triggered_ids = risky_ids.intersection(cascade_ids)
    if any(task_id not in conditional_by_task for task_id in triggered_ids):
        return "risky downstream cascade requires conditional spec review"

    conditional_failed = any(
        result_failed(trace[index]) for index in conditional_indexes
    )
    endpoints = matching_indexes(trace, "completion") + matching_indexes(trace, "user_gate")
    terminal_failure_after_clear = bool(conditional_indexes) and not endpoints and any(
        result_index > conditional_index
        and result_failed(trace[result_index])
        and any(
            overlay_index > result_index
            and trace[overlay_index].get("owner") == "runtime_failure_overlay"
            for overlay_index in matching_indexes(
                trace,
                "failure_overlay_entered",
                overlay="failure",
            )
        )
        for conditional_index in conditional_indexes
        if trace[conditional_index].get("outcome") == "clear"
        for result_index, occurrence in enumerate(trace)
        if occurrence.get("event") in RESULT_EVENTS
    )
    if conditional_failed and clear_verdicts:
        return "failed conditional review cannot have a clear verdict"
    if triggered_ids and not conditional_failed:
        if not final_review and not terminal_failure_after_clear:
            return "conditional review never replaces final full-diff review"
        if has_event(trace, "downstream_dispatch") and not ordered(
            trace, "conditional_spec_review", "downstream_dispatch"
        ):
            return "conditional review must precede downstream dispatch"
        if final_review and not ordered(
            trace, "conditional_spec_review", "final_full_diff_review"
        ):
            return "conditional review must precede final full-diff review"
    if (
        review_facts
        and not final_review
        and not conditional_failed
        and not terminal_failure_after_clear
    ):
        return "final full-diff review is required"

    if len(final_indexes) > 1:
        return "final full-diff review must occur exactly once"
    if len(verdict_indexes) > 1:
        return "review verdict must occur exactly once"
    if verdict_indexes and len(final_indexes) != 1:
        return "review verdict requires one applicable final full-diff review"
    if final_review:
        final_outcome = trace[final_indexes[0]].get("outcome")
        if final_outcome not in RESULT_OUTCOMES["final_full_diff_review"]:
            return "final full-diff review requires an actual result"
        if final_outcome in FAILURE_OUTCOMES and has_event(
            trace, "review_verdict", outcome="clear"
        ):
            return "blocking final review cannot have a clear verdict"
        if has_event(trace, "review_verdict", outcome="blocking"):
            if final_outcome == "green":
                return "blocking review verdict cannot follow a green final full-diff review"
            if final_outcome != "blocking":
                return (
                    "blocking review verdict requires one blocking final full-diff review"
                )
            if not ordered(trace, "final_full_diff_review", "review_verdict"):
                return "final full-diff review must precede blocking review verdict"
    if clear_verdicts:
        if len(clear_verdicts) != 1 or len(final_indexes) != 1:
            return "clear review verdict requires one successful final full-diff review"
        if trace[final_indexes[0]].get("outcome") != "green":
            return "clear review verdict requires one green final full-diff review"
        if not ordered(trace, "final_full_diff_review", "review_verdict"):
            return "successful final full-diff review must precede clear verdict"

    if endpoints:
        if len(final_indexes) != 1:
            return "successful completion or user gate requires final full-diff review"
        if trace[final_indexes[0]].get("outcome") != "green":
            return "successful completion or user gate requires green final full-diff review"
        if len(verdict_indexes) != 1 or len(clear_verdicts) != 1:
            return "successful completion or user gate requires a clear review verdict"
        if any(clear_verdicts[0] >= endpoint for endpoint in endpoints):
            return "clear review verdict must precede completion or user gate"
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
    validate_trace_shape(trace, contract["vocabulary"], "trace")
    metadata_failure = validate_required_metadata(trace, contract["vocabulary"])
    if metadata_failure is not None:
        invariant_id, reason = metadata_failure
        return {
            "valid": False,
            "outcome": "rejected",
            "contract_id": invariant_id,
            "reason": reason,
        }
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



def repair_known_opposite(mutant_id, trace):
    """Apply one explicit independent repair for each hand-authored mutant."""
    repaired = copy.deepcopy(trace)

    def occurrence(event, index=0):
        return [item for item in repaired if item["event"] == event][index]

    def add_failure_overlay(index=None):
        overlay = {
            "event": "failure_overlay_entered",
            "overlay": "failure",
            "owner": "runtime_failure_overlay",
        }
        if index is None:
            repaired.append(overlay)
        else:
            repaired.insert(index, overlay)

    if mutant_id == "external-conditional-base-commit":
        occurrence("conditional_base_commit")["event"] = "base_commit"
    elif mutant_id == "external-missing-independent-proof":
        repaired.append({"event": "independent_commit_proof", "owner": "orchestrator"})
    elif mutant_id == "external-mismatched-base-pin":
        occurrence("external_base_pin")["value"] = "sha-A"
    elif mutant_id == "single-risky-merge-before-verification":
        merged = occurrence("task_merged")
        repaired.remove(merged)
        repaired.append(merged)
    elif mutant_id == "single-risky-merge-before-precondition":
        precondition = occurrence("merge_precondition")
        repaired.remove(precondition)
        gate_index = next(
            index for index, item in enumerate(repaired) if item["event"] == "merge_gate"
        )
        repaired.insert(gate_index, precondition)
    elif mutant_id == "parallel-missing-integration-gate":
        repaired.append(
            {
                "event": "integration_gate",
                "outcome": "green",
                "owner": "orchestrator",
            }
        )
    elif mutant_id == "completion-reuse-missing-sha":
        repaired.insert(-1, {"event": "current_base_tip", "value": "sha-A"})
    elif mutant_id == "completion-reuse-missing-verify-set":
        repaired.insert(
            -1,
            {"event": "completion_verify_set", "value": "build,test,lint"},
        )
    elif mutant_id in {
        "unevaluable-verification-treated-as-green",
        "merge-precondition-labeled-lifecycle-only",
    }:
        progress_index = next(
            index for index, item in enumerate(repaired) if item["event"] == "progress"
        )
        add_failure_overlay(progress_index)
    elif mutant_id == "startup-wrong-owner":
        occurrence("startup")["owner"] = "harness_lifecycle"
    elif mutant_id == "pending-concern-completes":
        repaired = [item for item in repaired if item["event"] != "completion"]
    elif mutant_id == "user-safety-non-user-acceptance":
        occurrence("concern_disposition")["owner"] = "user"
    elif mutant_id == "conditional-review-replaces-final":
        repaired.extend(
            [
                {
                    "event": "final_full_diff_review",
                    "outcome": "green",
                    "owner": "reviewer",
                },
                {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
            ]
        )
    elif mutant_id == "routine-progress-narration":
        repaired = [
            item for item in repaired if item["event"] != "user_output_routine_progress"
        ]
    elif mutant_id == "external-missing-base-pin-value":
        occurrence("external_base_pin")["value"] = "sha-A"
    elif mutant_id in {
        "completion-skip-full-verify-missing-green",
        "completion-skip-full-verify-mismatched-set",
        "completion-skip-full-verify-mismatched-sha",
    }:
        repaired.append(
            {
                "event": "completion_full_verify",
                "outcome": "green",
                "owner": "orchestrator",
            }
        )
    elif mutant_id in {
        "failure-external-evidence-no-overlay",
        "failure-completion-full-verify-no-overlay",
        "failure-conditional-review-no-overlay",
    }:
        add_failure_overlay()
    elif mutant_id == "failure-final-review-blocking-verdict-no-overlay":
        verdict_index = next(
            index for index, item in enumerate(repaired) if item["event"] == "review_verdict"
        )
        add_failure_overlay(verdict_index)
        add_failure_overlay()
    elif mutant_id == "failure-overlay-wrong-owner":
        occurrence("failure_overlay_entered")["owner"] = "runtime_failure_overlay"
    elif mutant_id == "concern-missing-disposition-value":
        occurrence("concern_disposition")["disposition"] = "resolved"
    elif mutant_id == "concern-unknown-disposition-value":
        occurrence("concern_disposition")["disposition"] = "resolved"
    elif mutant_id == "conditional-review-without-cascade":
        repaired.insert(
            1,
            {
                "event": "downstream_cascade_risk",
                "task_id": occurrence("risky_task")["task_id"],
                "owner": "orchestrator",
            },
        )
    elif mutant_id == "direct-parallel-action-mixing":
        repaired = [item for item in repaired if item["event"] != "serial_merge"]
    elif mutant_id == "single-risky-work-after-failed-verification-before-overlay":
        verification_index = next(
            index
            for index, item in enumerate(repaired)
            if item["event"] == "task_verification"
        )
        later_implementation = next(
            index
            for index, item in enumerate(repaired)
            if index > verification_index and item["event"] == "task_implementation"
        )
        del repaired[later_implementation]
    elif mutant_id == "completion-reuse-conflicting-prior-integration":
        conflicting = [
            item for item in repaired if item["event"] == "prior_integration"
        ][1]
        repaired.remove(conflicting)
    elif mutant_id in {
        "direct-completion-without-final-review",
        "direct-user-gate-without-final-review",
    }:
        endpoint_index = next(
            index
            for index, item in enumerate(repaired)
            if item["event"] in {"completion", "user_gate"}
        )
        repaired[endpoint_index:endpoint_index] = [
            {
                "event": "final_full_diff_review",
                "outcome": "green",
                "owner": "reviewer",
            },
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
        ]
    elif mutant_id == "blocking-conditional-review-clear-verdict":
        repaired = [item for item in repaired if item["event"] != "review_verdict"]
    elif mutant_id == "clear-verdict-without-green-final-review":
        repaired.insert(
            0,
            {
                "event": "final_full_diff_review",
                "outcome": "green",
                "owner": "reviewer",
            },
        )
    elif mutant_id == "task-verification-missing-outcome":
        occurrence("task_verification")["outcome"] = "green"
    elif mutant_id == "failure-overlay-missing-overlay":
        occurrence("failure_overlay_entered")["overlay"] = "failure"
    elif mutant_id == "failure-overlay-missing-owner":
        occurrence("failure_overlay_entered")["owner"] = "runtime_failure_overlay"
    elif mutant_id == "route-omitted-direct-events":
        repaired.insert(
            0,
            {
                "event": "route_selected",
                "route": "direct",
                "owner": "orchestrator",
            },
        )
    elif mutant_id == "route-omitted-complete-single-risky":
        repaired.insert(
            0,
            {
                "event": "route_selected",
                "route": "single_risky",
                "owner": "orchestrator",
            },
        )
    elif mutant_id.startswith("failure-routine-"):
        overlay = occurrence("failure_overlay_entered")
        repaired.remove(overlay)
        repaired.insert(1, overlay)
    elif mutant_id == "final-review-clear-success":
        occurrence("final_full_diff_review")["outcome"] = "green"
    elif mutant_id == "review-verdict-blocking-no-overlay":
        add_failure_overlay()
    elif mutant_id == "review-verdict-conflicting-completion":
        repaired = [
            item
            for item in repaired
            if not (
                item["event"] == "review_verdict"
                and item.get("outcome") == "blocking"
            )
            and item["event"] != "failure_overlay_entered"
        ]
    elif mutant_id == "completion-endpoint-without-reuse-or-full-verify":
        repaired.insert(
            0,
            {
                "event": "completion_full_verify",
                "outcome": "green",
                "owner": "orchestrator",
            },
        )
    elif mutant_id == "blocking-verdict-without-review":
        repaired.insert(
            0,
            {
                "event": "final_full_diff_review",
                "outcome": "blocking",
                "owner": "reviewer",
            },
        )
        add_failure_overlay(1)
    elif mutant_id == "green-review-blocking-verdict":
        occurrence("review_verdict")["outcome"] = "clear"
        repaired = [
            item for item in repaired if item["event"] != "failure_overlay_entered"
        ]
    elif mutant_id == "external-base-commit-wrong-owner":
        occurrence("base_commit")["owner"] = "implementer"
    elif mutant_id == "concern-disposition-before-record":
        repaired.reverse()
    else:
        raise AssertionError(f"missing independent repair oracle for {mutant_id}")
    return repaired

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


def protected_block_mismatches(contract, markdown_blobs):
    markdown_files = tuple(markdown_blobs.values())
    expected_ids = {invariant["id"] for invariant in contract["invariants"]}
    marker_ids = {
        match.decode("ascii")
        for raw in markdown_files
        for match in re.findall(
            rb"<!-- leanforge:run-semantic:([^:]+):(?:start|end) -->",
            raw,
        )
    }
    mismatches = expected_ids.symmetric_difference(marker_ids)
    for invariant in contract["invariants"]:
        invariant_id = invariant["id"]
        encoded_id = invariant_id.encode("ascii")
        escaped_id = re.escape(encoded_id)
        marker = re.compile(
            rb"(?ms)<!-- leanforge:run-semantic:"
            + escaped_id
            + rb":start -->.*?<!-- leanforge:run-semantic:"
            + escaped_id
            + rb":end -->"
        )
        blocks = [block for raw in markdown_files for block in marker.findall(raw)]
        start_marker = b"<!-- leanforge:run-semantic:" + encoded_id + b":start -->"
        end_marker = b"<!-- leanforge:run-semantic:" + encoded_id + b":end -->"
        start_count = sum(raw.count(start_marker) for raw in markdown_files)
        end_count = sum(raw.count(end_marker) for raw in markdown_files)
        expected = render_protected_block(invariant).encode("utf-8")
        if (
            start_count != 1
            or end_count != 1
            or len(blocks) != 1
            or blocks[0] != expected
        ):
            mismatches.add(invariant_id)
    return mismatches


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
                self.assertEqual(
                    evaluate_assertions(scenario["trace"], scenario["assertions"]),
                    [],
                )
                result = validate_semantics(self.contract, scenario["trace"])
                self.assertEqual(result["valid"], scenario["expected_valid"])
                self.assertEqual(result["outcome"], scenario["expected_outcome"])
                self.assertIsNone(result["contract_id"])
                self.assertIsNone(result["reason"])

    def test_known_opposite_mutants_fail_with_exact_reason(self):
        survivors = []
        for mutant in self.fixture["mutants"]:
            with self.subTest(mutant=mutant["id"]):
                self.assertEqual(
                    evaluate_assertions(mutant["trace"], mutant["assertions"]),
                    [],
                )
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
        self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
        self.assertEqual(result["reason"], "external base commit must be implementer-owned")

    def test_validator_derives_failure_overlay_despite_lifecycle_facts(self):
        trace = [
            {"event": "startup", "owner": "harness_lifecycle"},
            {"event": "route_selected", "route": "single_risky", "owner": "orchestrator"},
            {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "task_implementation", "task_id": "task-a", "owner": "implementer"},
            {"event": "evidence_captured", "task_id": "task-a", "owner": "implementer"},
            {"event": "task_verification", "task_id": "task-a", "outcome": "green", "owner": "implementer"},
            {"event": "merge_precondition", "task_id": "task-a", "outcome": "unevaluable", "owner": "orchestrator"},
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
            {"event": "route_selected", "route": "single_risky", "owner": "orchestrator"},
            {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "task_implementation", "task_id": "task-a", "owner": "implementer"},
            {"event": "evidence_captured", "task_id": "task-a", "owner": "implementer"},
            {"event": "task_verification", "task_id": "task-a", "outcome": "non_green", "owner": "implementer"},
            {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

    def test_external_base_facts_require_non_empty_closed_scalar_values(self):
        cases = (
            (
                [
                    {"event": "route_selected", "route": "external", "owner": "orchestrator"},
                    {"event": "selected_base", "owner": "orchestrator"},
                    {"event": "external_base_pin", "value": "sha-A", "owner": "implementer"},
                    {"event": "external_action", "owner": "implementer"},
                ],
                "external selected base requires a non-empty scalar value",
            ),
            (
                [
                    {"event": "route_selected", "route": "external", "owner": "orchestrator"},
                    {"event": "selected_base", "value": "sha-A", "owner": "orchestrator"},
                    {"event": "external_base_pin", "owner": "implementer"},
                    {"event": "external_action", "owner": "implementer"},
                ],
                "external base pin requires a non-empty scalar value",
            ),
            (
                [
                    {"event": "route_selected", "route": "external", "owner": "orchestrator"},
                    {"event": "selected_base", "value": "", "owner": "orchestrator"},
                    {"event": "external_base_pin", "value": "", "owner": "implementer"},
                    {"event": "external_action", "owner": "implementer"},
                ],
                "external selected base requires a non-empty scalar value",
            ),
        )
        for trace, reason in cases:
            with self.subTest(reason=reason):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-EXTERNAL-PROOF")
                self.assertEqual(result["reason"], reason)
        invalid_scalar = [
            {"event": "route_selected", "route": "external", "owner": "orchestrator"},
            {"event": "selected_base", "value": ["sha-A"], "owner": "orchestrator"},
        ]
        with self.assertRaises(ValueError):
            validate_semantics(self.contract, invalid_scalar)

    def test_external_base_commit_is_implementer_owned_and_precedes_proof(self):
        trace = [
            {"event": "route_selected", "route": "external", "owner": "orchestrator"},
            {"event": "selected_base", "value": "sha-A", "owner": "orchestrator"},
            {"event": "external_base_pin", "value": "sha-A", "owner": "implementer"},
            {"event": "external_action", "owner": "implementer"},
            {"event": "external_evidence", "outcome": "green", "owner": "implementer"},
            {"event": "base_commit", "owner": "orchestrator"},
            {"event": "independent_commit_proof", "owner": "orchestrator"},
        ]
        self.assertEqual(
            validate_external_proof(trace),
            "external base commit must be implementer-owned",
        )

    def test_completion_reuse_is_derived_from_actual_facts(self):
        reuse = [
            {"event": "prior_integration", "outcome": "green"},
            {"event": "prior_verify_set", "value": "build,test,lint"},
            {"event": "completion_verify_set", "value": "build,test,lint"},
            {"event": "prior_gate_base_tip", "value": "sha-A"},
            {"event": "current_base_tip", "value": "sha-A"},
            {"event": "completion_reused", "owner": "orchestrator"},
        ]
        forced_rerun = reuse[:-1] + [
            {"event": "completion_full_verify", "outcome": "green", "owner": "orchestrator"}
        ]
        self.assertTrue(validate_semantics(self.contract, reuse)["valid"])
        self.assertTrue(validate_semantics(self.contract, forced_rerun)["valid"])

        invalid_without_full_verify = (
            reuse[1:-1],
            [
                {"event": "prior_integration", "outcome": "green"},
                {"event": "prior_verify_set", "value": "build,test"},
                {"event": "completion_verify_set", "value": "build,test,lint"},
                {"event": "prior_gate_base_tip", "value": "sha-A"},
                {"event": "current_base_tip", "value": "sha-A"},
            ],
            [
                {"event": "prior_integration", "outcome": "green"},
                {"event": "prior_verify_set", "value": "build,test,lint"},
                {"event": "completion_verify_set", "value": "build,test,lint"},
                {"event": "prior_gate_base_tip", "value": "sha-A"},
                {"event": "current_base_tip", "value": "sha-B"},
            ],
        )
        for trace in invalid_without_full_verify:
            with self.subTest(trace=trace):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-COMPLETION-REUSE")
                self.assertEqual(
                    result["reason"],
                    "incomplete or changed completion facts require full verify",
                )

    def test_completion_endpoint_without_reuse_facts_requires_full_verify(self):
        self.assertEqual(
            validate_completion_reuse(
                [{"event": "completion", "owner": "orchestrator"}]
            ),
            "completion endpoint without reusable facts requires full verify",
        )

    def test_completion_decisions_precede_final_review_and_endpoint(self):
        reuse_reason = (
            "completion reuse decision must precede final review, verdict, and endpoint"
        )
        full_verify_reason = (
            "completion full verify must precede final review and endpoint"
        )
        for endpoint in ("completion", "user_gate"):
            reuse_after_endpoint = [
                {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                {"event": endpoint, "owner": "orchestrator"},
                {"event": "prior_integration", "outcome": "green"},
                {"event": "prior_verify_set", "value": "build,test,lint"},
                {"event": "completion_verify_set", "value": "build,test,lint"},
                {"event": "prior_gate_base_tip", "value": "sha-A"},
                {"event": "current_base_tip", "value": "sha-A"},
                {"event": "completion_reused", "owner": "orchestrator"},
            ]
            full_verify_after_review = [
                {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                {"event": "completion_full_verify", "outcome": "green", "owner": "orchestrator"},
                {"event": endpoint, "owner": "orchestrator"},
            ]
            with self.subTest(endpoint=endpoint, decision="reuse"):
                result = validate_semantics(self.contract, reuse_after_endpoint)
                self.assertEqual(result["contract_id"], "RUN-COMPLETION-REUSE")
                self.assertEqual(result["reason"], reuse_reason)
            with self.subTest(endpoint=endpoint, decision="full_verify"):
                result = validate_semantics(self.contract, full_verify_after_review)
                self.assertEqual(result["contract_id"], "RUN-COMPLETION-REUSE")
                self.assertEqual(result["reason"], full_verify_reason)

    def test_completion_reuse_facts_remain_unique_green_and_equal(self):
        cases = (
            (
                [
                    {"event": "prior_integration", "outcome": "green"},
                    {"event": "prior_integration", "outcome": "green"},
                    {"event": "completion_reused"},
                ],
                "completion reuse requires exactly one prior integration result",
            ),
            (
                [
                    {"event": "prior_integration", "outcome": "non_green"},
                    {"event": "prior_verify_set", "value": "full"},
                    {"event": "completion_verify_set", "value": "full"},
                    {"event": "prior_gate_base_tip", "value": "sha-A"},
                    {"event": "current_base_tip", "value": "sha-A"},
                    {"event": "completion_reused"},
                ],
                "completion reuse requires prior green integration",
            ),
            (
                [
                    {"event": "prior_integration", "outcome": "green"},
                    {"event": "prior_verify_set", "value": "full"},
                    {"event": "completion_verify_set", "value": "changed"},
                    {"event": "prior_gate_base_tip", "value": "sha-A"},
                    {"event": "current_base_tip", "value": "sha-A"},
                    {"event": "completion_reused"},
                ],
                "completion reuse requires an identical verify set",
            ),
            (
                [
                    {"event": "prior_integration", "outcome": "green"},
                    {"event": "prior_verify_set", "value": "full"},
                    {"event": "completion_verify_set", "value": "full"},
                    {"event": "prior_gate_base_tip", "value": "sha-A"},
                    {"event": "current_base_tip", "value": "sha-B"},
                    {"event": "completion_reused"},
                ],
                "completion reuse requires the same gate and current base-tip SHA",
            ),
        )
        for trace, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(validate_completion_reuse(trace), reason)

    def test_failure_overlay_composes_with_route_prefix_and_all_results(self):
        terminal_single_risky = [
            {"event": "route_selected", "route": "single_risky", "owner": "orchestrator"},
            {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "task_implementation", "task_id": "task-a", "owner": "implementer"},
            {"event": "evidence_captured", "task_id": "task-a", "owner": "implementer"},
            {"event": "task_verification", "task_id": "task-a", "outcome": "non_green", "owner": "implementer"},
            {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
        ]
        self.assertTrue(validate_semantics(self.contract, terminal_single_risky)["valid"])

        failures = (
            (
                [
                    {"event": "route_selected", "route": "external", "owner": "orchestrator"},
                    {"event": "selected_base", "value": "sha-A", "owner": "orchestrator"},
                    {"event": "external_base_pin", "value": "sha-A", "owner": "implementer"},
                    {"event": "external_action", "owner": "implementer"},
                    {"event": "external_evidence", "outcome": "non_green", "owner": "implementer"},
                ],
                "non_green external evidence must enter failure overlay",
            ),
            (
                [{"event": "completion_full_verify", "outcome": "non_green", "owner": "orchestrator"}],
                "non_green completion full verify result must enter failure overlay",
            ),
            (
                [
                    {"event": "risky_task", "task_id": "task-review", "owner": "orchestrator"},
                    {"event": "downstream_cascade_risk", "task_id": "task-review", "owner": "orchestrator"},
                    {"event": "conditional_spec_review", "task_id": "task-review", "outcome": "non_green", "owner": "reviewer"},
                ],
                "non_green conditional spec review result must enter failure overlay",
            ),
            (
                [
                    {"event": "final_full_diff_review", "outcome": "blocking", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                ],
                "blocking final review result must enter failure overlay",
            ),
        )
        for trace, reason in failures:
            with self.subTest(reason=reason):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-FAIL-CLOSED")
                self.assertEqual(result["reason"], reason)

        wrong_owner = [
            {"event": "task_verification", "task_id": "task-a", "outcome": "non_green", "owner": "implementer"},
            {"event": "failure_overlay_entered", "overlay": "failure", "owner": "orchestrator"},
        ]
        result = validate_semantics(self.contract, wrong_owner)
        self.assertEqual(result["contract_id"], "RUN-FAIL-CLOSED")
        self.assertEqual(
            result["reason"],
            "failure overlay must be runtime-failure-overlay-owned",
        )

    def test_route_prefix_stops_at_first_failure_without_requiring_later_success(self):
        traces = (
            [
                {"event": "route_selected", "route": "direct", "owner": "orchestrator"},
                {"event": "completion_gate", "outcome": "non_green", "owner": "orchestrator"},
                {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
            ],
            [
                {"event": "route_selected", "route": "single_risky", "owner": "orchestrator"},
                {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
                {"event": "task_implementation", "task_id": "task-a", "owner": "implementer"},
                {"event": "completion_gate", "outcome": "unevaluable", "owner": "orchestrator"},
                {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
            ],
            [
                {"event": "route_selected", "route": "external", "owner": "orchestrator"},
                {"event": "selected_base", "value": "sha-A", "owner": "orchestrator"},
                {"event": "completion_gate", "outcome": "non_green", "owner": "orchestrator"},
                {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
            ],
        )
        for trace in traces:
            with self.subTest(route=trace[0]["route"]):
                self.assertTrue(validate_semantics(self.contract, trace)["valid"])

    def test_concern_dispositions_are_correlated_and_closed(self):
        cases = (
            (
                [
                    {"event": "concern_recorded", "value": "C-1", "owner": "orchestrator"},
                    {"event": "concern_disposition", "value": "C-1", "owner": "orchestrator"},
                ],
                "concern disposition requires a non-empty closed value",
            ),
            (
                [
                    {"event": "concern_recorded", "value": "C-1", "owner": "orchestrator"},
                    {"event": "concern_disposition", "value": "C-1", "disposition": "ignored", "owner": "orchestrator"},
                ],
                "concern disposition is outside the closed vocabulary",
            ),
        )
        for trace, reason in cases:
            with self.subTest(reason=reason):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-CONCERN-DISPOSITION")
                self.assertEqual(result["reason"], reason)

    def test_user_owned_pending_and_promoted_concerns_do_not_require_acceptance(self):
        user_concerns = (
            "user_owned_requirement_concern",
            "user_owned_compatibility_concern",
            "user_owned_safety_concern",
        )
        for event in user_concerns:
            pending = [
                {"event": event, "value": "C-1", "owner": "user"},
                {
                    "event": "concern_disposition",
                    "value": "C-1",
                    "disposition": "pending",
                    "owner": "orchestrator",
                },
            ]
            promoted = [
                {"event": event, "value": "C-1", "owner": "user"},
                {
                    "event": "concern_disposition",
                    "value": "C-1",
                    "disposition": "promoted_to_failure",
                    "owner": "orchestrator",
                },
                {
                    "event": "failure_overlay_entered",
                    "overlay": "failure",
                    "owner": "runtime_failure_overlay",
                },
            ]
            with self.subTest(event=event, disposition="pending"):
                self.assertIsNone(validate_concern_disposition(pending))
            with self.subTest(event=event, disposition="promoted_to_failure"):
                self.assertIsNone(validate_concern_disposition(promoted))

    def test_user_owned_terminal_concern_requires_user_acceptance(self):
        for disposition in ("resolved", "explicitly_accepted"):
            trace = [
                {
                    "event": "user_owned_requirement_concern",
                    "value": "C-1",
                    "owner": "user",
                },
                {
                    "event": "concern_disposition",
                    "value": "C-1",
                    "disposition": disposition,
                    "owner": "orchestrator",
                },
            ]
            with self.subTest(disposition=disposition):
                self.assertEqual(
                    validate_concern_disposition(trace),
                    "user-owned requirement concern requires user acceptance for terminal disposition",
                )

    def test_review_topology_is_bidirectional_and_result_bearing(self):
        conditional_without_cascade = [
            {"event": "risky_task", "task_id": "task-review", "owner": "orchestrator"},
            {"event": "conditional_spec_review", "task_id": "task-review", "outcome": "clear", "owner": "reviewer"},
            {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
        ]
        result = validate_semantics(self.contract, conditional_without_cascade)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "conditional review applies only to risky downstream cascade",
        )

        missing_result = [
            {"event": "risky_task", "task_id": "task-review", "owner": "orchestrator"},
            {"event": "downstream_cascade_risk", "task_id": "task-review", "owner": "orchestrator"},
            {"event": "conditional_spec_review", "task_id": "task-review", "owner": "reviewer"},
            {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
        ]
        result = validate_semantics(self.contract, missing_result)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "conditional spec review requires an actual result",
        )

        blocking_with_overlay_and_clear_verdict = [
            {"event": "final_full_diff_review", "outcome": "blocking", "owner": "reviewer"},
            {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
        ]
        result = validate_semantics(self.contract, blocking_with_overlay_and_clear_verdict)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "blocking final review cannot have a clear verdict",
        )

        successful_completion = [
            {"event": "route_selected", "route": "direct", "owner": "orchestrator"},
            {"event": "task_implementation", "owner": "orchestrator"},
            {"event": "evidence_captured", "owner": "orchestrator"},
            {"event": "base_commit", "owner": "orchestrator"},
            {"event": "completion_full_verify", "outcome": "green", "owner": "orchestrator"},
            {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
            {"event": "completion", "owner": "orchestrator"},
            {"event": "user_gate", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, successful_completion)["valid"])

    def test_blocking_review_verdict_requires_matching_review_topology(self):
        self.assertEqual(
            validate_review_topology(
                [{"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"}]
            ),
            "review verdict requires one applicable final full-diff review",
        )
        self.assertEqual(
            validate_review_topology(
                [
                    {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
                    {
                        "event": "failure_overlay_entered",
                        "overlay": "failure",
                        "owner": "runtime_failure_overlay",
                    },
                ]
            ),
            "blocking review verdict cannot follow a green final full-diff review",
        )

    def test_route_selection_is_orchestrator_owned_on_every_route(self):
        self.assertEqual(
            EVENT_METADATA_SCHEMA["route_selected"]["required"],
            {"event", "route", "owner"},
        )
        successes = {
            route: next(
                item["trace"]
                for item in self.fixture["scenarios"]
                if item["id"] == scenario_id
            )
            for route, scenario_id in {
                "direct": "direct-success",
                "single_risky": "single-risky-success",
                "parallel": "parallel-success",
                "external": "external-success",
            }.items()
        }
        for route, trace in successes.items():
            self.assertEqual(ROUTE_EVENT_OWNERS[route]["route_selected"], "orchestrator")
            for owner in (None, "user"):
                mutation = copy.deepcopy(trace)
                selection = next(
                    item for item in mutation if item["event"] == "route_selected"
                )
                if owner is None:
                    selection.pop("owner")
                else:
                    selection["owner"] = owner
                with self.subTest(route=route, owner=owner):
                    reason = "route selection must be orchestrator-owned"
                    self.assertEqual(validate_route_topology(mutation), reason)
                    result = validate_semantics(self.contract, mutation)
                    self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                    self.assertEqual(result["reason"], reason)

    def test_missing_route_selection_mutants_are_one_dimensional(self):
        mutants = {item["id"]: item for item in self.fixture["mutants"]}
        self.assertNotIn("route-omitted-complete-mixed-routes", mutants)
        direct_assertion = {
            "op": "forbid",
            "event": "route_selected",
            "filter": {},
        }
        cases = {
            "route-omitted-direct-events": "direct-success",
            "route-omitted-complete-single-risky": "single-risky-success",
        }
        for mutant_id, scenario_id in cases.items():
            mutant = mutants[mutant_id]
            complete_trace = next(
                item["trace"]
                for item in self.fixture["scenarios"]
                if item["id"] == scenario_id
            )
            with self.subTest(mutant=mutant_id):
                self.assertEqual(mutant["trace"], complete_trace[1:])
                self.assertEqual(mutant["assertions"][0], direct_assertion)
                repaired = repair_known_opposite(mutant_id, mutant["trace"])
                self.assertEqual(repaired, complete_trace)
                self.assertEqual(
                    evaluate_assertions(repaired, mutant["assertions"]),
                    ["assertions[0] forbid failed"],
                )

        self.assertEqual(
            mutants["route-omitted-complete-single-risky"]["assertions"],
            [direct_assertion],
        )

    def test_route_specific_events_require_one_compatible_selected_route(self):
        missing_route_reason = "route-specific events require exactly one selected route"
        for event in sorted(ROUTE_SPECIFIC_EVENTS):
            with self.subTest(event=event, route="omitted"):
                self.assertEqual(
                    validate_route_topology([{"event": event}]),
                    missing_route_reason,
                )

        for route, allowed_events in ROUTE_ALLOWED_EVENTS.items():
            for event in sorted(ROUTE_SPECIFIC_EVENTS - allowed_events):
                with self.subTest(event=event, route=route):
                    self.assertEqual(
                        validate_route_topology(
                            [
                                {
                                    "event": "route_selected",
                                    "route": route,
                                    "owner": "orchestrator",
                                },
                                {"event": event},
                            ]
                        ),
                        f"{route.replace('_', '-')} route forbids route-specific event {event}",
                    )

    def test_promoted_failure_only_orders_later_continuations(self):
        trace = [
            {"event": "routine_read", "owner": "orchestrator"},
            {"event": "progress", "owner": "orchestrator"},
            {
                "event": "concern_recorded",
                "value": "concern-indexed-precedence",
                "owner": "orchestrator",
            },
            {
                "event": "concern_disposition",
                "value": "concern-indexed-precedence",
                "disposition": "promoted_to_failure",
                "owner": "orchestrator",
            },
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
            {"event": "routine_write", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

        mutation = copy.deepcopy(trace)
        mutation[-2], mutation[-1] = mutation[-1], mutation[-2]
        result = validate_semantics(self.contract, mutation)
        self.assertEqual(result["contract_id"], "RUN-FAIL-CLOSED")
        self.assertEqual(
            result["reason"],
            "failure overlay must precede any present continuation",
        )

    def test_final_review_and_verdict_use_fresh_reviewer_ownership(self):
        self.assertIn("reviewer", self.contract["vocabulary"]["owner"])
        trace = [
            {
                "event": "completion_full_verify",
                "outcome": "green",
                "owner": "orchestrator",
            },
            {
                "event": "final_full_diff_review",
                "outcome": "green",
                "owner": "reviewer",
            },
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
            {"event": "completion", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

        owner_reasons = {
            "final_full_diff_review": "final full-diff review must be fresh-reviewer-owned",
            "review_verdict": "review verdict must be fresh-reviewer-owned",
        }
        for event, reason in owner_reasons.items():
            mutation = copy.deepcopy(trace)
            next(item for item in mutation if item["event"] == event)["owner"] = "implementer"
            with self.subTest(event=event):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
                self.assertEqual(result["reason"], reason)

        mutation = copy.deepcopy(trace)
        mutation[-1]["owner"] = "implementer"
        result = validate_semantics(self.contract, mutation)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "completion and user gate must be orchestrator-owned",
        )

    def test_parallel_success_has_two_correlated_task_proofs(self):
        scenario = next(
            item for item in self.fixture["scenarios"] if item["id"] == "parallel-success"
        )
        expected_task_ids = {"task-a", "task-b"}
        for event in (
            "worktree_created",
            "task_implementation",
            "task_verification",
            "merge_gate",
            "task_merged",
        ):
            task_ids = {
                item.get("task_id")
                for item in scenario["trace"]
                if item["event"] == event
            }
            with self.subTest(event=event):
                self.assertEqual(task_ids, expected_task_ids)
                self.assertEqual(
                    sum(item["event"] == event for item in scenario["trace"]),
                    2,
                )
        self.assertTrue(validate_semantics(self.contract, scenario["trace"])["valid"])

        mutation = copy.deepcopy(scenario["trace"])
        next(
            item
            for item in mutation
            if item["event"] == "task_verification" and item["task_id"] == "task-b"
        ).pop("task_id")
        result = validate_semantics(self.contract, mutation)
        self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "parallel task work, verification, gate, and merge evidence must correlate by task_id",
        )

    def test_failure_result_matrix_covers_every_declared_failure_outcome(self):
        expected = {
            (event, outcome)
            for event in self.contract["vocabulary"]["result_event"]
            for outcome in RESULT_OUTCOMES[event].intersection(FAILURE_OUTCOMES)
        }
        matrix = {
            (scenario["failure_case"]["event"], scenario["failure_case"]["outcome"]): scenario
            for scenario in self.fixture["scenarios"]
            if "failure_case" in scenario
        }
        self.assertEqual(set(matrix), expected)

        for (event, outcome), scenario in matrix.items():
            case = scenario["failure_case"]
            trace = scenario["trace"]
            target_indexes = matching_indexes(trace, event, outcome=outcome)
            self.assertEqual(len(target_indexes), 1, scenario["id"])
            target_index = target_indexes[0]
            overlay_indexes = [
                index
                for index in matching_indexes(
                    trace,
                    "failure_overlay_entered",
                    overlay="failure",
                    owner="runtime_failure_overlay",
                )
                if index > target_index
            ]
            continuation_indexes = [
                index
                for index, occurrence in enumerate(trace)
                if index > target_index
                and occurrence["event"] in CONTINUATION_EVENTS
            ]
            self.assertTrue(overlay_indexes, scenario["id"])
            self.assertTrue(continuation_indexes, scenario["id"])
            self.assertLess(min(overlay_indexes), min(continuation_indexes), scenario["id"])
            self.assertIn(
                {
                    "op": "count",
                    "event": event,
                    "filter": {"outcome": outcome},
                    "expected": 1,
                },
                scenario["assertions"],
                scenario["id"],
            )

            mutation = copy.deepcopy(trace)
            del mutation[overlay_indexes[0]]
            result = validate_semantics(self.contract, mutation)
            with self.subTest(event=event, outcome=outcome):
                self.assertEqual(result["contract_id"], case["expected_contract_id"])
                self.assertEqual(result["reason"], case["expected_reason"])


    def test_promoted_failure_uses_closed_failure_continuation_precedence(self):
        reason = "failure overlay must precede any present continuation"
        for event in sorted(CONTINUATION_EVENTS):
            trace = [
                {"event": "concern_recorded", "value": "C-1", "owner": "orchestrator"},
                {
                    "event": "concern_disposition",
                    "value": "C-1",
                    "disposition": "promoted_to_failure",
                    "owner": "orchestrator",
                },
                {"event": event},
                {
                    "event": "failure_overlay_entered",
                    "overlay": "failure",
                    "owner": "runtime_failure_overlay",
                },
            ]
            with self.subTest(continuation=event):
                self.assertEqual(validate_failure_overlay(trace), reason)

        promoted_retry = [
            {"event": "concern_recorded", "value": "C-1", "owner": "orchestrator"},
            {
                "event": "concern_disposition",
                "value": "C-1",
                "disposition": "promoted_to_failure",
                "owner": "orchestrator",
            },
            {"event": "retry", "owner": "orchestrator"},
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
        ]
        result = validate_semantics(self.contract, promoted_retry)
        self.assertEqual(result["contract_id"], "RUN-FAIL-CLOSED")
        self.assertEqual(result["reason"], reason)

        pending_retry = [
            {"event": "concern_recorded", "value": "C-1", "owner": "orchestrator"},
            {
                "event": "concern_disposition",
                "value": "C-1",
                "disposition": "pending",
                "owner": "orchestrator",
            },
            {"event": "retry", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, pending_retry)["valid"])

    def test_failure_overlay_precedes_every_closed_continuation_category(self):
        categories = {
            "route_work": ROUTE_SPECIFIC_EVENTS,
            "routine_work": {
                "routine_write",
                "routine_dispatch",
                "routine_merge",
                "routine_gate",
                "routine_cleanup",
            },
            "dispatch": {"downstream_dispatch", "routine_dispatch"},
            "merge": {"task_merged", "serial_merge", "routine_merge"},
            "gate": {
                "merge_precondition",
                "merge_gate",
                "merge_gates_complete",
                "integration_gate",
                "completion_gate",
                "routine_gate",
            },
            "cleanup": {"cleanup", "routine_cleanup"},
            "progress": {"progress"},
        }
        closed_continuations = set(self.contract["vocabulary"]["continuation_event"])
        for category, events in categories.items():
            with self.subTest(category=category):
                self.assertTrue(events.issubset(closed_continuations))

        for event in sorted(closed_continuations):
            trace = [
                {"event": "completion_gate", "outcome": "non_green"},
                {"event": event},
                {
                    "event": "failure_overlay_entered",
                    "overlay": "failure",
                    "owner": "runtime_failure_overlay",
                },
            ]
            with self.subTest(continuation=event):
                self.assertEqual(
                    validate_failure_overlay(trace),
                    "failure overlay must precede any present continuation",
                )

    def test_every_routine_event_is_a_failure_continuation(self):
        routine_events = {
            event
            for event in self.contract["vocabulary"]["event"]
            if event.startswith("routine_")
        }
        self.assertTrue(
            routine_events.issubset(
                set(self.contract["vocabulary"]["continuation_event"])
            )
        )
        for event in sorted(routine_events):
            trace = [
                {"event": "completion_gate", "outcome": "non_green"},
                {"event": event},
                {
                    "event": "failure_overlay_entered",
                    "overlay": "failure",
                    "owner": "runtime_failure_overlay",
                },
            ]
            with self.subTest(event=event):
                self.assertEqual(
                    validate_failure_overlay(trace),
                    "failure overlay must precede any present continuation",
                )

    def test_direct_failure_can_enter_distinct_remedial_worktree_topology(self):
        trace = [
            {"event": "route_selected", "route": "direct", "owner": "orchestrator"},
            {"event": "task_implementation", "owner": "orchestrator"},
            {"event": "evidence_captured", "owner": "orchestrator"},
            {"event": "base_commit", "owner": "orchestrator"},
            {"event": "completion_gate", "outcome": "non_green", "owner": "orchestrator"},
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
            {"event": "remedial_worktree_created", "owner": "orchestrator"},
            {"event": "remedial_implementer_continuation", "owner": "implementer"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

    def test_final_review_success_and_verdict_are_exact_and_cardinal(self):
        for endpoint in ("completion", "user_gate"):
            trace = [
                {"event": "final_full_diff_review", "outcome": "clear", "owner": "reviewer"},
                {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                {"event": endpoint, "owner": "orchestrator"},
            ]
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    validate_review_topology(trace),
                    "final full-diff review requires an actual result",
                )

        conflicting_verdicts = [
            {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
            {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
            {"event": "completion", "owner": "orchestrator"},
        ]
        self.assertEqual(
            validate_review_topology(conflicting_verdicts),
            "review verdict must occur exactly once",
        )

    def test_completion_endpoint_requires_latest_preceding_full_verify_green(self):
        reason = "completion or user gate requires the latest preceding full verify to be green"
        for outcome, endpoint in (
            ("non_green", "completion"),
            ("unevaluable", "user_gate"),
        ):
            trace = [
                {"event": "completion_full_verify", "outcome": "green", "owner": "orchestrator"},
                {"event": "completion_full_verify", "outcome": outcome, "owner": "orchestrator"},
                {
                    "event": "failure_overlay_entered",
                    "overlay": "failure",
                    "owner": "runtime_failure_overlay",
                },
                {"event": endpoint, "owner": "orchestrator"},
            ]
            with self.subTest(outcome=outcome, endpoint=endpoint):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-COMPLETION-REUSE")
                self.assertEqual(result["reason"], reason)

        recovered = [
            {"event": "completion_full_verify", "outcome": "non_green", "owner": "orchestrator"},
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
            {"event": "completion_full_verify", "outcome": "green", "owner": "orchestrator"},
            {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
            {"event": "completion", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, recovered)["valid"])
        self.assertEqual(
            validate_completion_reuse(
                [
                    {"event": "completion", "owner": "orchestrator"},
                    {
                        "event": "completion_full_verify",
                        "outcome": "green",
                        "owner": "orchestrator",
                    },
                ]
            ),
            reason,
        )

    def test_direct_route_owns_implementation_evidence_and_base_commit(self):
        direct = [
            {"event": "route_selected", "route": "direct", "owner": "orchestrator"},
            {"event": "task_implementation", "owner": "orchestrator"},
            {"event": "evidence_captured", "owner": "orchestrator"},
            {"event": "base_commit", "owner": "orchestrator"},
        ]
        wrong_owner_reasons = {
            "task_implementation": "direct implementation must be orchestrator-owned",
            "evidence_captured": "direct evidence must be orchestrator-owned",
            "base_commit": "direct base commit must be orchestrator-owned",
        }
        for event, reason in wrong_owner_reasons.items():
            mutation = copy.deepcopy(direct)
            next(item for item in mutation if item["event"] == event)["owner"] = "implementer"
            with self.subTest(event=event):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertEqual(result["reason"], reason)

        external = [
            {"event": "route_selected", "route": "external", "owner": "orchestrator"},
            {"event": "selected_base", "value": "sha-A", "owner": "orchestrator"},
            {"event": "external_base_pin", "value": "sha-A", "owner": "implementer"},
            {"event": "external_action", "owner": "implementer"},
            {"event": "external_evidence", "outcome": "green", "owner": "implementer"},
            {"event": "base_commit", "owner": "implementer"},
            {"event": "independent_commit_proof", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, external)["valid"])

    def test_review_outcome_and_verdict_pairs_are_exact_and_cardinal(self):
        reason = "final full-diff review requires an actual result"
        for final_outcome in ("clear", "non_green", "unevaluable"):
            trace = [
                {"event": "final_full_diff_review", "outcome": final_outcome, "owner": "reviewer"},
                {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
            ]
            with self.subTest(final_outcome=final_outcome):
                self.assertEqual(validate_review_topology(trace), reason)

        self.assertIsNone(
            validate_review_topology(
                [
                    {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                ]
            )
        )
        self.assertIsNone(
            validate_review_topology(
                [
                    {"event": "final_full_diff_review", "outcome": "blocking", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
                ]
            )
        )
        blocking_with_overlays = [
            {"event": "final_full_diff_review", "outcome": "blocking", "owner": "reviewer"},
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
            {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
        ]
        self.assertTrue(validate_semantics(self.contract, blocking_with_overlays)["valid"])
        without_overlays = [
            item for item in blocking_with_overlays if item["event"] != "failure_overlay_entered"
        ]
        self.assertEqual(
            validate_semantics(self.contract, without_overlays)["contract_id"],
            "RUN-FAIL-CLOSED",
        )
        self.assertEqual(
            validate_review_topology(
                [
                    {"event": "final_full_diff_review", "outcome": "blocking", "owner": "reviewer"},
                    {"event": "final_full_diff_review", "outcome": "blocking", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
                ]
            ),
            "final full-diff review must occur exactly once",
        )
        self.assertEqual(
            validate_review_topology(
                [
                    {"event": "final_full_diff_review", "outcome": "blocking", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "blocking", "owner": "reviewer"},
                ]
            ),
            "review verdict must occur exactly once",
        )

    def test_protected_block_must_be_wholly_present_in_one_markdown_file(self):
        invariant = self.contract["invariants"][0]
        expected = render_protected_block(invariant).encode("utf-8")
        left, right = expected.split(b"\n", 1)
        single_invariant_contract = {
            **self.contract,
            "invariants": [invariant],
        }
        split_blobs = {
            Path("first.md"): left,
            Path("second.md"): right,
        }
        self.assertEqual(
            protected_block_mismatches(single_invariant_contract, split_blobs),
            {invariant["id"]},
        )

    def test_trace_metadata_is_event_specific(self):
        with self.assertRaises(ValueError):
            validate_semantics(
                self.contract,
                [{"event": "route_selected", "route": "direct", "outcome": "green"}],
            )

    def test_event_metadata_schema_is_closed_required_and_typed(self):
        self.assertEqual(set(EVENT_METADATA_SCHEMA), set(EXPECTED_VOCABULARY["event"]))
        for event, schema in EVENT_METADATA_SCHEMA.items():
            with self.subTest(event=event):
                self.assertEqual(set(schema), {"allowed", "required", "types"})
                self.assertIn("event", schema["required"])
                self.assertTrue(schema["required"].issubset(schema["allowed"]))
                self.assertEqual(set(schema["types"]), schema["allowed"])
        for event in RESULT_EVENTS:
            with self.subTest(result_event=event):
                self.assertIn("outcome", EVENT_METADATA_SCHEMA[event]["required"])
        self.assertEqual(
            EVENT_METADATA_SCHEMA["failure_overlay_entered"]["required"],
            {"event", "overlay", "owner"},
        )
        for event in TASK_CORRELATION_EVENTS:
            with self.subTest(task_correlation_event=event):
                self.assertIn("task_id", EVENT_METADATA_SCHEMA[event]["allowed"])
        for event in ("final_full_diff_review", "review_verdict", "completion", "user_gate"):
            with self.subTest(owned_event=event):
                self.assertIn("owner", EVENT_METADATA_SCHEMA[event]["required"])

    def test_required_metadata_empty_values_fail_closed_with_exact_reasons(self):
        cases = (
            (
                [{"event": "task_verification", "outcome": "", "owner": "implementer"}],
                "RUN-FAIL-CLOSED",
                "task verification requires a non-empty closed outcome",
            ),
            (
                [
                    {"event": "task_verification", "outcome": "non_green", "owner": "implementer"},
                    {"event": "failure_overlay_entered", "overlay": "", "owner": "runtime_failure_overlay"},
                ],
                "RUN-FAIL-CLOSED",
                "failure overlay requires explicit failure identity",
            ),
            (
                [
                    {"event": "task_verification", "outcome": "non_green", "owner": "implementer"},
                    {"event": "failure_overlay_entered", "overlay": "failure", "owner": ""},
                ],
                "RUN-FAIL-CLOSED",
                "failure overlay must be runtime-failure-overlay-owned",
            ),
        )
        for trace, contract_id, reason in cases:
            with self.subTest(reason=reason):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], contract_id)
                self.assertEqual(result["reason"], reason)

    def test_routine_operation_may_precede_actual_result_output(self):
        trace = [
            {"event": "routine_read", "owner": "orchestrator"},
            {"event": "user_output_actual_blocker", "owner": "orchestrator"},
            {"event": "user_output_final_result", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

    def test_fixture_is_an_independent_oracle_without_rule_selection(self):
        serialized = json.dumps(self.fixture, ensure_ascii=False)
        for forbidden_key in ('"contracts"', '"contract_id"'):
            with self.subTest(forbidden_key=forbidden_key):
                self.assertNotIn(forbidden_key, serialized)
        for collection_name in ("scenarios", "mutants"):
            for item in self.fixture[collection_name]:
                with self.subTest(collection=collection_name, item=item["id"]):
                    self.assertIn("expected_valid", item)
                    self.assertIn("expected_outcome", item)

    def test_fixture_declares_closed_assertion_language_and_literal_assertions(self):
        self.assertEqual(
            self.fixture.get("assertion_language"),
            ["count", "forbid", "before", "same", "owner"],
        )
        for collection_name in ("scenarios", "mutants"):
            for item in self.fixture[collection_name]:
                with self.subTest(collection=collection_name, item=item["id"]):
                    self.assertIsInstance(item.get("assertions"), list)
                    self.assertTrue(item["assertions"])

    def test_each_assertion_operator_catches_a_targeted_trace_mutation(self):
        scenarios = {item["id"]: item for item in self.fixture["scenarios"]}
        direct = scenarios["direct-success"]
        external = scenarios["external-success"]
        mutations = {}

        mutations["count"] = copy.deepcopy(direct["trace"])
        mutations["count"].insert(0, copy.deepcopy(mutations["count"][0]))
        mutations["forbid"] = copy.deepcopy(direct["trace"])
        mutations["forbid"].append(
            {"event": "worktree_created", "owner": "orchestrator"}
        )
        mutations["before"] = copy.deepcopy(direct["trace"])
        mutations["before"][0], mutations["before"][1] = (
            mutations["before"][1],
            mutations["before"][0],
        )
        mutations["same"] = copy.deepcopy(external["trace"])
        next(
            occurrence
            for occurrence in mutations["same"]
            if occurrence["event"] == "external_base_pin"
        )["value"] = "sha-B"
        mutations["owner"] = copy.deepcopy(direct["trace"])
        next(
            occurrence
            for occurrence in mutations["owner"]
            if occurrence["event"] == "task_implementation"
        )["owner"] = "implementer"

        operator_sources = {
            "count": direct,
            "forbid": direct,
            "before": direct,
            "same": external,
            "owner": direct,
        }
        for operator in ASSERTION_OPERATORS:
            assertion = next(
                assertion
                for assertion in operator_sources[operator]["assertions"]
                if assertion["op"] == operator
            )
            with self.subTest(operator=operator):
                self.assertEqual(
                    evaluate_assertions(mutations[operator], [assertion]),
                    [f"assertions[0] {operator} failed"],
                )

    def test_protected_block_comparison_rejects_crlf_byte_drift(self):
        markdown_blobs = {path: path.read_bytes() for path in MARKDOWN_PATHS}
        self.assertEqual(protected_block_mismatches(self.contract, markdown_blobs), set())
        invariant = self.contract["invariants"][0]
        expected = render_protected_block(invariant).encode("utf-8")
        drifted = expected.replace(b"\n", b"\r\n")
        mutated_blobs = dict(markdown_blobs)
        containing_path = next(
            path for path, raw in markdown_blobs.items() if expected in raw
        )
        mutated_blobs[containing_path] = mutated_blobs[containing_path].replace(
            expected, drifted, 1
        )
        self.assertEqual(
            protected_block_mismatches(self.contract, mutated_blobs),
            {invariant["id"]},
        )

    def test_exactly_one_deterministic_protected_block_per_invariant(self):
        markdown_blobs = {path: path.read_bytes() for path in MARKDOWN_PATHS}
        self.assertEqual(
            protected_block_mismatches(self.contract, markdown_blobs),
            set(),
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
        mutations.append(("empty fixture assertion program", assertion_program))
        unknown_assertion = copy.deepcopy(self.fixture)
        unknown_assertion["scenarios"][0]["assertions"][0]["op"] = "select_rule"
        mutations.append(("unknown fixture assertion", unknown_assertion))
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

    def test_later_non_route_failure_does_not_bypass_selected_route_structure(self):
        cases = (
            (
                [
                    {"event": "route_selected", "route": "single_risky", "owner": "orchestrator"},
                    {"event": "worktree_created", "owner": "implementer"},
                    {"event": "completion_gate", "outcome": "non_green", "owner": "orchestrator"},
                    {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
                ],
                "single-risky worktree must be orchestrator-owned",
            ),
            (
                [
                    {"event": "route_selected", "route": "parallel", "owner": "orchestrator"},
                    {"event": "isolated_task_worktrees", "owner": "orchestrator"},
                    {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "completion_gate", "outcome": "unevaluable", "owner": "orchestrator"},
                    {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
                ],
                "parallel route requires at least two isolated task worktrees with stable task_id",
            ),
            (
                [
                    {"event": "route_selected", "route": "parallel", "owner": "orchestrator"},
                    {"event": "isolated_task_worktrees", "owner": "orchestrator"},
                    {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "worktree_created", "task_id": "task-b", "owner": "orchestrator"},
                    {"event": "task_implementation", "task_id": "task-a", "owner": "implementer"},
                    {"event": "task_implementation", "task_id": "task-c", "owner": "implementer"},
                    {"event": "completion_gate", "outcome": "non_green", "owner": "orchestrator"},
                    {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
                ],
                "parallel task work, verification, gate, and merge evidence must correlate by task_id",
            ),
        )
        for trace, reason in cases:
            with self.subTest(reason=reason):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertEqual(result["reason"], reason)

    def test_single_risky_route_is_exactly_owned_cardinal_and_ordered(self):
        trace = [
            {"event": "route_selected", "route": "single_risky", "owner": "orchestrator"},
            {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "task_implementation", "task_id": "task-a", "owner": "implementer"},
            {"event": "evidence_captured", "task_id": "task-a", "owner": "implementer"},
            {"event": "task_verification", "task_id": "task-a", "outcome": "green", "owner": "implementer"},
            {"event": "merge_precondition", "task_id": "task-a", "outcome": "green", "owner": "orchestrator"},
            {"event": "merge_gate", "task_id": "task-a", "outcome": "green", "owner": "orchestrator"},
            {"event": "task_merged", "task_id": "task-a", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

        owner_reasons = {
            "worktree_created": "single-risky worktree must be orchestrator-owned",
            "task_implementation": "single-risky implementation must be implementer-owned",
            "evidence_captured": "single-risky evidence must be implementer-owned",
            "task_verification": "single-risky verification must be implementer-owned",
            "merge_precondition": "single-risky merge precondition must be orchestrator-owned",
            "merge_gate": "single-risky merge gate must be orchestrator-owned",
            "task_merged": "single-risky merge must be orchestrator-owned",
        }
        for event, reason in owner_reasons.items():
            mutation = copy.deepcopy(trace)
            occurrence = next(item for item in mutation if item["event"] == event)
            occurrence["owner"] = (
                "implementer" if occurrence["owner"] == "orchestrator" else "orchestrator"
            )
            with self.subTest(event=event, mutation="owner"):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertEqual(result["reason"], reason)

        for event in ROUTE_STAGE_ORDER["single_risky"]:
            mutation = copy.deepcopy(trace)
            occurrence = next(item for item in mutation if item["event"] == event)
            mutation.insert(mutation.index(occurrence), copy.deepcopy(occurrence))
            with self.subTest(event=event, mutation="duplicate"):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertEqual(
                    result["reason"],
                    f"single-risky route requires exactly one {event}",
                )

        for left, right in zip(
            ROUTE_STAGE_ORDER["single_risky"],
            ROUTE_STAGE_ORDER["single_risky"][1:],
        ):
            mutation = copy.deepcopy(trace)
            left_index = next(
                index for index, item in enumerate(mutation) if item["event"] == left
            )
            right_index = next(
                index for index, item in enumerate(mutation) if item["event"] == right
            )
            mutation[left_index], mutation[right_index] = (
                mutation[right_index],
                mutation[left_index],
            )
            with self.subTest(left=left, right=right, mutation="order"):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertFalse(result["valid"])

    def test_parallel_reached_prefix_keeps_every_task_correlation_stage_closed(self):
        success = next(
            item
            for item in self.fixture["scenarios"]
            if item["id"] == "parallel-success"
        )["trace"]
        correlated_stages = (
            "task_implementation",
            "task_verification",
            "merge_gate",
            "task_merged",
        )
        for stage in correlated_stages:
            stage_end = max(matching_indexes(success, stage))
            trace = copy.deepcopy(success[: stage_end + 1])
            trace.extend(
                [
                    {"event": "completion_gate", "outcome": "non_green", "owner": "orchestrator"},
                    {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
                ]
            )
            with self.subTest(stage=stage, mutation="baseline"):
                self.assertTrue(validate_semantics(self.contract, trace)["valid"])

            mutation = copy.deepcopy(trace)
            next(
                item
                for item in mutation
                if item["event"] == stage and item.get("task_id") == "task-b"
            )["task_id"] = "task-c"
            with self.subTest(stage=stage, mutation="mixed-task-id"):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertEqual(
                    result["reason"],
                    "parallel task work, verification, gate, and merge evidence must correlate by task_id",
                )

    def test_completion_reuse_evidence_precedes_decision_and_review_chain(self):
        facts = [
            {"event": "prior_integration", "outcome": "green"},
            {"event": "prior_verify_set", "value": "full"},
            {"event": "completion_verify_set", "value": "full"},
            {"event": "prior_gate_base_tip", "value": "sha-A"},
            {"event": "current_base_tip", "value": "sha-A"},
        ]
        decision_before_facts = [
            {"event": "completion_reused", "owner": "orchestrator"},
            *facts,
        ]
        result = validate_semantics(self.contract, decision_before_facts)
        self.assertEqual(result["contract_id"], "RUN-COMPLETION-REUSE")
        self.assertEqual(
            result["reason"],
            "all completion reuse evidence facts must precede the reuse decision",
        )

        decision_after_verdict = [
            *facts,
            {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
            {"event": "completion_reused", "owner": "orchestrator"},
        ]
        result = validate_semantics(self.contract, decision_after_verdict)
        self.assertEqual(result["contract_id"], "RUN-COMPLETION-REUSE")
        self.assertEqual(
            result["reason"],
            "completion reuse decision must precede final review, verdict, and endpoint",
        )

    def test_conditional_review_is_fresh_reviewer_owned_and_task_correlated(self):
        valid = [
            {"event": "risky_task", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "downstream_cascade_risk", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "conditional_spec_review", "task_id": "task-a", "outcome": "clear", "owner": "reviewer"},
            {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
        ]
        self.assertTrue(validate_semantics(self.contract, valid)["valid"])

        cases = (
            (
                [
                    {"event": "risky_task", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "downstream_cascade_risk", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "conditional_spec_review", "task_id": "task-a", "outcome": "clear", "owner": "orchestrator"},
                    {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                ],
                "conditional spec review must be fresh-reviewer-owned",
            ),
            (
                [
                    {"event": "risky_task", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "downstream_cascade_risk", "task_id": "task-b", "owner": "orchestrator"},
                    {"event": "conditional_spec_review", "task_id": "task-a", "outcome": "clear", "owner": "reviewer"},
                    {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                ],
                "conditional review facts and result must correlate by task_id",
            ),
            (
                [
                    {"event": "risky_task", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "non_risky_task", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "downstream_cascade_risk", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "conditional_spec_review", "task_id": "task-a", "outcome": "clear", "owner": "reviewer"},
                    {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                ],
                "review risk facts must not contradict for one task_id",
            ),
            (
                [
                    {"event": "risky_task", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "downstream_cascade_risk", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "no_downstream_cascade_risk", "task_id": "task-a", "owner": "orchestrator"},
                    {"event": "conditional_spec_review", "task_id": "task-a", "outcome": "clear", "owner": "reviewer"},
                    {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                ],
                "review cascade facts must not contradict for one task_id",
            ),
        )
        for trace, reason in cases:
            with self.subTest(reason=reason):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
                self.assertEqual(result["reason"], reason)

        missing_task_id = copy.deepcopy(valid)
        missing_task_id[0].pop("task_id")
        result = validate_semantics(self.contract, missing_task_id)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "conditional review facts and result require a non-empty task_id",
        )

    def test_recorded_concern_precedes_every_correlated_disposition(self):
        for disposition in EXPECTED_VOCABULARY["disposition"]:
            trace = [
                {
                    "event": "concern_disposition",
                    "value": "C-1",
                    "disposition": disposition,
                    "owner": "orchestrator",
                },
                {"event": "concern_recorded", "value": "C-1", "owner": "orchestrator"},
            ]
            if disposition == "promoted_to_failure":
                trace.append(
                    {
                        "event": "failure_overlay_entered",
                        "overlay": "failure",
                        "owner": "runtime_failure_overlay",
                    }
                )
            with self.subTest(disposition=disposition):
                result = validate_semantics(self.contract, trace)
                self.assertEqual(result["contract_id"], "RUN-CONCERN-DISPOSITION")
                self.assertEqual(
                    result["reason"],
                    "recorded concern must precede its correlated disposition",
                )

    def test_merge_before_precondition_known_opposite_has_independent_order_oracle(self):
        mutant = next(
            item
            for item in self.fixture["mutants"]
            if item["id"] == "single-risky-merge-before-precondition"
        )
        trace = mutant["trace"]
        opposite_assertion = next(
            assertion
            for assertion in mutant["assertions"]
            if assertion == {
                "op": "before",
                "event_a": "task_merged",
                "event_b": "merge_precondition",
            }
        )
        self.assertEqual(evaluate_assertions(trace, [opposite_assertion]), [])
        result = validate_semantics(self.contract, trace)
        self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "single-risky merge precondition must precede merge",
        )

        order_without_precondition = [
            event
            for event in ROUTE_STAGE_ORDER["single_risky"]
            if event != "merge_precondition"
        ]
        self.assertIsNone(
            validate_reached_route_prefix(
                trace,
                "single_risky",
                0,
                len(trace) - 1,
                stage_order=order_without_precondition,
            )
        )

        repaired = copy.deepcopy(trace)
        precondition = next(
            item for item in repaired if item["event"] == "merge_precondition"
        )
        repaired.remove(precondition)
        gate_index = next(
            index
            for index, item in enumerate(repaired)
            if item["event"] == "merge_gate"
        )
        repaired.insert(gate_index, precondition)
        self.assertEqual(
            evaluate_assertions(repaired, [opposite_assertion]),
            ["assertions[0] before failed"],
        )


    def test_success_route_events_use_one_owner_cardinality_and_correlation_path(self):
        successes = {
            route: next(
                item["trace"]
                for item in self.fixture["scenarios"]
                if item["id"] == scenario_id
            )
            for route, scenario_id in {
                "direct": "direct-success",
                "single_risky": "single-risky-success",
                "parallel": "parallel-success",
                "external": "external-success",
            }.items()
        }
        for route, trace in successes.items():
            for event, expected_owner in ROUTE_EVENT_OWNERS[route].items():
                mutation = copy.deepcopy(trace)
                next(item for item in mutation if item["event"] == event)["owner"] = (
                    "implementer" if expected_owner == "orchestrator" else "orchestrator"
                )
                with self.subTest(route=route, event=event, mutation="owner"):
                    result = validate_semantics(self.contract, mutation)
                    self.assertFalse(result["valid"])
                    self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")

            for event in ROUTE_STAGE_ORDER[route]:
                mutation = copy.deepcopy(trace)
                occurrence = next(item for item in mutation if item["event"] == event)
                mutation.insert(mutation.index(occurrence), copy.deepcopy(occurrence))
                with self.subTest(route=route, event=event, mutation="duplicate"):
                    result = validate_semantics(self.contract, mutation)
                    self.assertFalse(result["valid"])
                    self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")

        single_risky = successes["single_risky"]
        task_ids = {
            occurrence.get("task_id")
            for occurrence in single_risky
            if occurrence["event"] in TASK_CORRELATION_EVENTS
        }
        self.assertEqual(task_ids, {"task-a"})
        for event in TASK_CORRELATION_EVENTS:
            mutation = copy.deepcopy(single_risky)
            next(item for item in mutation if item["event"] == event)["task_id"] = "task-b"
            with self.subTest(route="single_risky", event=event, mutation="task_id"):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertEqual(
                    result["reason"],
                    "single-risky per-task events must correlate by task_id",
                )

    def test_all_concern_dispositions_precede_every_completion_endpoint(self):
        for disposition in EXPECTED_VOCABULARY["disposition"]:
            for endpoint in ("completion", "user_gate"):
                owner = "user" if disposition == "user_accepted" else "orchestrator"
                trace = [
                    {"event": "completion_full_verify", "outcome": "green", "owner": "orchestrator"},
                    {"event": "final_full_diff_review", "outcome": "green", "owner": "reviewer"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
                    {"event": endpoint, "owner": "orchestrator"},
                    {"event": "concern_recorded", "value": "C-1", "owner": "orchestrator"},
                    {
                        "event": "concern_disposition",
                        "value": "C-1",
                        "disposition": disposition,
                        "owner": owner,
                    },
                ]
                if disposition == "promoted_to_failure":
                    trace.append(
                        {
                            "event": "failure_overlay_entered",
                            "overlay": "failure",
                            "owner": "runtime_failure_overlay",
                        }
                    )
                with self.subTest(disposition=disposition, endpoint=endpoint):
                    result = validate_semantics(self.contract, trace)
                    self.assertEqual(result["contract_id"], "RUN-CONCERN-DISPOSITION")
                    self.assertEqual(
                        result["reason"],
                        "concern record and disposition must precede completion or user gate",
                    )

    def test_clear_conditional_review_may_end_in_terminal_failure_without_final_review(self):
        trace = [
            {"event": "risky_task", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "downstream_cascade_risk", "task_id": "task-a", "owner": "orchestrator"},
            {
                "event": "conditional_spec_review",
                "task_id": "task-a",
                "outcome": "clear",
                "owner": "reviewer",
            },
            {"event": "completion_gate", "outcome": "non_green", "owner": "orchestrator"},
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

        continued = trace[:3] + [{"event": "downstream_dispatch", "owner": "orchestrator"}]
        result = validate_semantics(self.contract, continued)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "conditional review never replaces final full-diff review",
        )

    def test_parallel_terminal_failure_validates_only_the_completed_prefix(self):
        trace = [
            {"event": "route_selected", "route": "parallel", "owner": "orchestrator"},
            {"event": "isolated_task_worktrees", "owner": "orchestrator"},
            {"event": "worktree_created", "task_id": "task-a", "owner": "orchestrator"},
            {"event": "worktree_created", "task_id": "task-b", "owner": "orchestrator"},
            {"event": "task_implementation", "task_id": "task-a", "owner": "implementer"},
            {"event": "task_implementation", "task_id": "task-b", "owner": "implementer"},
            {
                "event": "task_verification",
                "task_id": "task-a",
                "outcome": "non_green",
                "owner": "implementer",
            },
            {
                "event": "failure_overlay_entered",
                "overlay": "failure",
                "owner": "runtime_failure_overlay",
            },
        ]
        self.assertTrue(validate_semantics(self.contract, trace)["valid"])

        malformed = copy.deepcopy(trace)
        malformed.pop(5)
        result = validate_semantics(self.contract, malformed)
        self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "parallel task work, verification, gate, and merge evidence must correlate by task_id",
        )

    def test_single_risky_correlation_includes_evidence_and_merge_precondition(self):
        trace = next(
            item["trace"]
            for item in self.fixture["scenarios"]
            if item["id"] == "single-risky-success"
        )
        for event in ("evidence_captured", "merge_precondition"):
            with self.subTest(event=event, phase="literal"):
                occurrence = next(item for item in trace if item["event"] == event)
                self.assertEqual(occurrence.get("task_id"), "task-a")

            mutation = copy.deepcopy(trace)
            next(item for item in mutation if item["event"] == event)["task_id"] = "task-b"
            with self.subTest(event=event, phase="mismatch"):
                result = validate_semantics(self.contract, mutation)
                self.assertEqual(result["contract_id"], "RUN-ROUTE-TOPOLOGY")
                self.assertEqual(
                    result["reason"],
                    "single-risky per-task events must correlate by task_id",
                )

    def test_final_full_diff_review_rejects_verdict_only_clear_outcome(self):
        trace = [
            {"event": "final_full_diff_review", "outcome": "clear", "owner": "reviewer"},
            {"event": "review_verdict", "outcome": "clear", "owner": "reviewer"},
        ]
        result = validate_semantics(self.contract, trace)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(result["reason"], "final full-diff review requires an actual result")

    def test_all_known_opposites_have_independent_repair_oracles(self):
        mutants = {item["id"]: item for item in self.fixture["mutants"]}
        self.assertEqual(len(EXPECTED_MUTANT_IDS), 53)
        self.assertEqual(set(mutants), EXPECTED_MUTANT_IDS)

        for mutant_id in sorted(EXPECTED_MUTANT_IDS):
            mutant = mutants[mutant_id]
            with self.subTest(mutant=mutant_id, phase="fixture-literal"):
                self.assertEqual(
                    evaluate_assertions(mutant["trace"], mutant["assertions"]),
                    [],
                )
                result = validate_semantics(self.contract, mutant["trace"])
                self.assertEqual(result["contract_id"], mutant["expected_contract_id"])
                self.assertEqual(result["reason"], mutant["expected_reason"])

            repaired = repair_known_opposite(mutant_id, mutant["trace"])
            with self.subTest(mutant=mutant_id, phase="independent-repair"):
                self.assertNotEqual(
                    evaluate_assertions(repaired, mutant["assertions"]),
                    [],
                )
                self.assertTrue(
                    validate_semantics(self.contract, repaired)["valid"],
                    mutant_id,
                )


if __name__ == "__main__":
    unittest.main()
