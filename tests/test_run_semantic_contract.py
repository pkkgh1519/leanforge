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
    "review_verdict",
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
    "clear",
    "blocking",
    "non_green",
    "unevaluable",
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
    add("failure_overlay_entered", "overlay", required=True)
    schema["failure_overlay_entered"]["required"].add("owner")
    for event in RESULT_EVENTS:
        add(event, "outcome", required=True)
    add("prior_integration", "outcome", required=True)
    add("review_verdict", "outcome", required=True)
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
    "single-risky-terminal-failure",
    "failure-external-evidence-non-green",
    "failure-completion-full-verify-non-green",
    "failure-conditional-review-non-green",
    "failure-final-review-blocking",
    "completion-forced-rerun",
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
    "external-missing-base-pin-value",
    "completion-skip-full-verify-missing-green",
    "completion-skip-full-verify-mismatched-set",
    "completion-skip-full-verify-mismatched-sha",
    "failure-external-evidence-no-overlay",
    "failure-completion-full-verify-no-overlay",
    "failure-conditional-review-no-overlay",
    "failure-final-review-clear-verdict-no-overlay",
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
        if event in RESULT_OUTCOMES and "outcome" in occurrence:
            if occurrence["outcome"] not in RESULT_OUTCOMES[event]:
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
    }
    completion_value_reasons = {
        "prior_verify_set": "completion reuse requires the prior verify set",
        "completion_verify_set": "completion reuse requires the completion verify set",
        "prior_gate_base_tip": "completion reuse requires the prior gate base-tip SHA",
        "current_base_tip": "completion reuse requires the current base-tip SHA",
    }
    for occurrence in trace:
        event = occurrence["event"]
        if event == "route_selected" and occurrence.get("route") not in vocabulary["route"]:
            return "RUN-ROUTE-TOPOLOGY", "selected route is outside the closed route vocabulary"
        if event in RESULT_OUTCOMES and occurrence.get("outcome") not in RESULT_OUTCOMES[event]:
            invariant_id = (
                "RUN-REVIEW-TOPOLOGY"
                if event in {"conditional_spec_review", "final_full_diff_review"}
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
        "task_verification",
        "merge_precondition",
        "merge_gate",
        "task_merged",
    },
    "parallel": {
        "isolated_task_worktrees",
        "task_implementation",
        "task_verifications_complete",
        "merge_gates_complete",
        "serial_merge",
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
        "task_verification",
        "merge_precondition",
        "merge_gate",
        "task_merged",
    ],
    "parallel": [
        "isolated_task_worktrees",
        "task_implementation",
        "task_verifications_complete",
        "merge_gates_complete",
        "serial_merge",
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


def validate_reached_route_prefix(trace, route, route_index, failure_index):
    stages = ROUTE_STAGE_ORDER[route]
    if any(
        index > failure_index and occurrence.get("event") in ROUTE_ALLOWED_EVENTS[route]
        for index, occurrence in enumerate(trace)
    ):
        return f"{route.replace('_', '-')} route cannot advance after a failed result"
    prefix = trace[: failure_index + 1]
    positions = []
    for position, event in enumerate(stages):
        indexes = matching_indexes(prefix, event)
        if len(indexes) > 1:
            return f"{route.replace('_', '-')} route prefix contains duplicate {event}"
        if indexes:
            positions.append((position, indexes[0]))
    if positions:
        highest_position = positions[-1][0]
        if [position for position, _ in positions] != list(range(highest_position + 1)):
            return f"{route.replace('_', '-')} route prefix skips a required stage"
        indexes = [index for _, index in positions]
        if indexes != sorted(indexes) or route_index >= indexes[0]:
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
    for occurrence in prefix:
        if occurrence.get("event") in RESULT_EVENTS and occurrence.get("event") in stages:
            if occurrence.get("outcome") not in {"green", "clear"}:
                return f"{route.replace('_', '-')} route prefix contains a failed result"
    if route == "external" and has_event(prefix, "conditional_base_commit"):
        return "external base commit must not be conditional"
    return None


def validate_route_topology(trace):
    selected = matching_indexes(trace, "route_selected")
    if not selected:
        return None
    if len(selected) != 1:
        return "a success route must be selected exactly once"
    route = trace[selected[0]].get("route")
    if route not in ROUTE_ALLOWED_EVENTS:
        return "selected route is outside the closed route vocabulary"
    for occurrence in trace:
        event = occurrence.get("event")
        if event in ROUTE_SPECIFIC_EVENTS and event not in ROUTE_ALLOWED_EVENTS[route]:
            return f"{route.replace('_', '-')} route forbids route-specific event {event}"
    failure_index = first_failed_result_index(trace)
    route_result_events = ROUTE_ALLOWED_EVENTS[route].intersection(RESULT_EVENTS)
    if (
        failure_index is not None
        and trace[failure_index].get("event") not in route_result_events
    ):
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
        checks = (
            (len(matching_indexes(trace, "worktree_created")) == 1, "single-risky route requires one task worktree"),
            (owner_is(trace, "task_implementation", "implementer"), "single-risky implementation must be implementer-owned"),
        )
        for passed, reason in checks:
            if not passed:
                return reason
        verification = matching_indexes(trace, "task_verification")
        if len(verification) != 1:
            return "single-risky route requires green task verification"
        if not ordered(trace, "route_selected", "worktree_created"):
            return "single-risky worktree must follow route selection"
        if not ordered(trace, "worktree_created", "task_implementation"):
            return "single-risky worktree must precede implementation"
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
        if not ordered(trace, "merge_gate", "task_merged"):
            return "single-risky merge gate must precede merge"
        return None
    if route == "parallel":
        checks = (
            (len(matching_indexes(trace, "isolated_task_worktrees")) == 1, "parallel route requires isolated task worktrees"),
            (owner_is(trace, "task_implementation", "implementer"), "parallel implementation must be implementer-owned"),
        )
        for passed, reason in checks:
            if not passed:
                return reason
        results = matching_indexes(trace, "task_verifications_complete")
        if len(results) != 1:
            return "parallel route requires green task verification"
        if not ordered(trace, "route_selected", "isolated_task_worktrees"):
            return "parallel isolation must follow route selection"
        if not ordered(trace, "isolated_task_worktrees", "task_implementation"):
            return "parallel isolation must precede implementation"
        if not ordered(trace, "task_implementation", "task_verifications_complete"):
            return "parallel implementation must precede task verification"
        if result_failed(trace[results[0]]):
            if any(
                has_event(trace, event)
                for event in (
                    "merge_gates_complete",
                    "serial_merge",
                    "regeneration",
                    "wiring",
                    "integration_gate",
                )
            ):
                return "parallel route cannot advance after a failed result"
            return None
        if trace[results[0]].get("outcome") != "green":
            return "parallel route requires green task verification"

        merge_results = matching_indexes(trace, "merge_gates_complete")
        if len(merge_results) != 1:
            return "parallel route requires green merge gates"
        if not ordered(trace, "task_verifications_complete", "merge_gates_complete"):
            return "parallel task verification must precede merge gates"
        if result_failed(trace[merge_results[0]]):
            if any(
                has_event(trace, event)
                for event in ("serial_merge", "regeneration", "wiring", "integration_gate")
            ):
                return "parallel route cannot advance after a failed result"
            return None
        if trace[merge_results[0]].get("outcome") != "green":
            return "parallel route requires green merge gates"
        if len(matching_indexes(trace, "serial_merge")) != 1:
            return "parallel route requires serial merge"
        if not ordered(trace, "merge_gates_complete", "serial_merge"):
            return "parallel merge gates must precede serial merge"

        regeneration = matching_indexes(trace, "regeneration")
        if len(regeneration) != 1:
            return "parallel route requires green regeneration"
        if not ordered(trace, "serial_merge", "regeneration"):
            return "parallel serial merge must precede regeneration"
        if result_failed(trace[regeneration[0]]):
            if any(has_event(trace, event) for event in ("wiring", "integration_gate")):
                return "parallel route cannot advance after a failed result"
            return None
        if trace[regeneration[0]].get("outcome") != "green":
            return "parallel route requires green regeneration"

        wiring = matching_indexes(trace, "wiring")
        if len(wiring) != 1:
            return "parallel route requires green wiring"
        if not ordered(trace, "regeneration", "wiring"):
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
        if not ordered(trace, "wiring", "integration_gate"):
            return "parallel wiring must precede integration gate"
        if result_failed(trace[integration[0]]):
            return None
        if trace[integration[0]].get("outcome") != "green":
            return "parallel route requires one green integration gate"
        if not ordered(trace, "isolated_task_worktrees", "task_verifications_complete"):
            return "parallel isolation must precede task verification"
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
    }
    continuations = set(CONTINUATION_EVENTS)
    for result_index, occurrence in enumerate(trace):
        event = occurrence.get("event")
        outcome = occurrence.get("outcome")
        if event not in phases or outcome not in FAILURE_OUTCOMES:
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
    fact_events = {
        "prior_integration",
        "prior_verify_set",
        "completion_verify_set",
        "prior_gate_base_tip",
        "current_base_tip",
        "completion_reused",
    }
    has_fact_context = any(item.get("event") in fact_events for item in trace)
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
    if full_verify:
        return None
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
    if any(trace[index].get("value") not in concern_values for index in dispositions):
        return "concern disposition must correlate to exactly one recorded concern"

    for index in dispositions:
        disposition = trace[index]["disposition"]
        if disposition == "pending":
            if has_event(trace, "completion"):
                return "pending concern blocks completion"
            if has_event(trace, "user_gate"):
                return "pending concern blocks user gate"
        if disposition == "promoted_to_failure":
            if not has_event(
                trace,
                "failure_overlay_entered",
                overlay="failure",
                owner="runtime_failure_overlay",
            ):
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
        for concern_index in matching_indexes(trace, event):
            concern_value = trace[concern_index].get("value")
            if not any(
                trace[index].get("value") == concern_value
                and trace[index].get("disposition") == "user_accepted"
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
    conditional_indexes = matching_indexes(trace, "conditional_spec_review")
    final_indexes = matching_indexes(trace, "final_full_diff_review")
    clear_verdicts = matching_indexes(trace, "review_verdict", outcome="clear")
    conditional = bool(conditional_indexes)
    final_review = bool(final_indexes)

    if conditional and not (has_risky and has_cascade):
        return "conditional review applies only to risky downstream cascade"
    if len(conditional_indexes) > 1:
        return "conditional spec review must occur exactly once"
    if conditional and trace[conditional_indexes[0]].get("outcome") not in RESULT_OUTCOMES["conditional_spec_review"]:
        return "conditional spec review requires an actual result"
    if has_risky and has_cascade and not conditional:
        return "risky downstream cascade requires conditional spec review"

    conditional_failed = conditional and result_failed(trace[conditional_indexes[0]])
    if conditional_failed and clear_verdicts:
        return "failed conditional review cannot have a clear verdict"
    if has_risky and has_cascade and not conditional_failed:
        if not final_review:
            return "conditional review never replaces final full-diff review"
        if has_event(trace, "downstream_dispatch") and not ordered(
            trace, "conditional_spec_review", "downstream_dispatch"
        ):
            return "conditional review must precede downstream dispatch"
        if not ordered(trace, "conditional_spec_review", "final_full_diff_review"):
            return "conditional review must precede final full-diff review"
    if review_facts and not final_review and not conditional_failed:
        return "final full-diff review is required"

    if len(final_indexes) > 1:
        return "final full-diff review must occur exactly once"
    if final_review:
        final_outcome = trace[final_indexes[0]].get("outcome")
        if final_outcome not in RESULT_OUTCOMES["final_full_diff_review"]:
            return "final full-diff review requires an actual result"
        if final_outcome in FAILURE_OUTCOMES and has_event(
            trace, "review_verdict", outcome="clear"
        ):
            return "blocking final review cannot have a clear verdict"
    if clear_verdicts:
        if len(clear_verdicts) != 1 or len(final_indexes) != 1:
            return "clear review verdict requires one successful final full-diff review"
        if trace[final_indexes[0]].get("outcome") not in {"green", "clear"}:
            return "clear review verdict requires one successful final full-diff review"
        if not ordered(trace, "final_full_diff_review", "review_verdict"):
            return "successful final full-diff review must precede clear verdict"

    endpoints = matching_indexes(trace, "completion") + matching_indexes(trace, "user_gate")
    if endpoints:
        if len(final_indexes) != 1 or trace[final_indexes[0]].get("outcome") not in {
            "green",
            "clear",
        }:
            return "successful completion or user gate requires final full-diff review"
        if len(clear_verdicts) != 1:
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

    def test_failure_overlay_composes_with_route_prefix_and_all_results(self):
        terminal_single_risky = [
            {"event": "route_selected", "route": "single_risky", "owner": "orchestrator"},
            {"event": "worktree_created", "owner": "orchestrator"},
            {"event": "task_implementation", "owner": "implementer"},
            {"event": "task_verification", "outcome": "non_green", "owner": "implementer"},
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
                    {"event": "risky_task", "owner": "orchestrator"},
                    {"event": "downstream_cascade_risk", "owner": "orchestrator"},
                    {"event": "conditional_spec_review", "outcome": "non_green", "owner": "orchestrator"},
                ],
                "non_green conditional spec review result must enter failure overlay",
            ),
            (
                [
                    {"event": "final_full_diff_review", "outcome": "blocking", "owner": "orchestrator"},
                    {"event": "review_verdict", "outcome": "clear", "owner": "orchestrator"},
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
            {"event": "task_verification", "outcome": "non_green", "owner": "implementer"},
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
                {"event": "worktree_created", "owner": "orchestrator"},
                {"event": "task_implementation", "owner": "implementer"},
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

    def test_review_topology_is_bidirectional_and_result_bearing(self):
        conditional_without_cascade = [
            {"event": "risky_task", "owner": "orchestrator"},
            {"event": "conditional_spec_review", "outcome": "clear", "owner": "orchestrator"},
            {"event": "final_full_diff_review", "outcome": "clear", "owner": "orchestrator"},
        ]
        result = validate_semantics(self.contract, conditional_without_cascade)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "conditional review applies only to risky downstream cascade",
        )

        missing_result = [
            {"event": "risky_task", "owner": "orchestrator"},
            {"event": "downstream_cascade_risk", "owner": "orchestrator"},
            {"event": "conditional_spec_review", "owner": "orchestrator"},
            {"event": "final_full_diff_review", "outcome": "clear", "owner": "orchestrator"},
        ]
        result = validate_semantics(self.contract, missing_result)
        self.assertEqual(result["contract_id"], "RUN-REVIEW-TOPOLOGY")
        self.assertEqual(
            result["reason"],
            "conditional spec review requires an actual result",
        )

        blocking_with_overlay_and_clear_verdict = [
            {"event": "final_full_diff_review", "outcome": "blocking", "owner": "orchestrator"},
            {"event": "failure_overlay_entered", "overlay": "failure", "owner": "runtime_failure_overlay"},
            {"event": "review_verdict", "outcome": "clear", "owner": "orchestrator"},
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
            {"event": "final_full_diff_review", "outcome": "green", "owner": "orchestrator"},
            {"event": "review_verdict", "outcome": "clear", "owner": "orchestrator"},
            {"event": "completion", "owner": "orchestrator"},
            {"event": "user_gate", "owner": "orchestrator"},
        ]
        self.assertTrue(validate_semantics(self.contract, successful_completion)["valid"])

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
