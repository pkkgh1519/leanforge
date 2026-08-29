#!/usr/bin/env python3
"""Derive the default-off Strict Lite alpha profile from validated shadow evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping

from adaptive_assurance import ContractError, SHADOW_KEYS, load_json

PILOT_KEYS = {
    "schema_version",
    "contract_id",
    "activation",
    "activation_file",
    "profile_file",
    "eligibility_contract",
    "live_topology",
    "promotion_policy",
    "activation_request",
    "prime",
    "run",
    "promote_to_full_on",
}
ACTIVATION_KEYS = {"schema_version", "pilot", "enabled"}
PROFILE_KEYS = {
    "schema_version",
    "contract_id",
    "profile",
    "cycle",
    "reason",
    "harness_sync",
    "bounded_direct_execution",
}
PLAN_KEYS = {
    "task_count",
    "task_risk",
    "regeneration_barrier",
    "local_file_diff",
    "targeted_verification_sufficient",
}

_LITE_PLAN = {
    "route": "strict_lite",
    "profile_action": "keep",
    "intent_review": "skipped",
    "dependent_work": "allowed_after_approval",
    "approval": "required",
    "same_cycle_lite_reentry": "not_applicable",
}
_FULL_PLAN = {
    "route": "full_assurance",
    "profile_action": "remove",
    "intent_review": "required_before_3doc_gate",
    "dependent_work": "forbidden_before_approval",
    "approval": "required",
    "same_cycle_lite_reentry": "forbidden",
}
_RUNTIME_PROMOTION = {
    "route": "full_assurance",
    "profile_action": "remove",
    "run_action": "halt_and_preserve_state",
    "prime_action": "reenter_elicit_with_source_context",
    "intent_review": "required_before_spec",
    "three_doc_action": "regenerate_review_reapprove",
    "dependent_work": "forbidden_before_reapproval",
    "resume_profile": "full_assurance",
    "same_cycle_lite_reentry": "forbidden",
}
_RUNTIME_CONTEXT_BLOCKED = {
    "route": "full_assurance",
    "profile_action": "remove",
    "run_action": "halt_and_preserve_state",
    "prime_action": "await_original_prime_context_or_resupplied_source",
    "intent_review": "blocked_until_source_context",
    "three_doc_action": "forbid_reconstruction_from_approved_3doc",
    "dependent_work": "forbidden_before_reapproval",
    "resume_profile": "full_assurance_after_reapproval",
    "same_cycle_lite_reentry": "forbidden",
}


def _exact_keys(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ContractError(
            f"{where} keys must be closed; "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )


def _unique_strings(value: Any, where: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item for item in value)
        or len(value) != len(set(value))
    ):
        raise ContractError(f"{where} must be a non-empty unique string list")
    return tuple(value)


def validate_pilot_contract(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("pilot contract root must be an object")
    _exact_keys(value, PILOT_KEYS, "pilot contract")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["contract_id"] != "leanforge.adaptive-assurance-lite-pilot"
        or value["activation"] != "default_off"
        or value["activation_file"] != ".leanforge/adaptive-assurance-pilot.json"
        or value["profile_file"] != ".leanforge/assurance-profile.json"
        or value["eligibility_contract"] != "leanforge.adaptive-assurance#lite"
        or value["promotion_policy"] != "monotonic_to_full_assurance"
    ):
        raise ContractError("unsupported pilot identity")
    if _unique_strings(value["live_topology"], "live_topology") != (
        "strict_lite",
        "full_assurance",
    ):
        raise ContractError("live topology must be binary")
    request = value["activation_request"]
    if not isinstance(request, dict) or request != {
        "schema_version": 1,
        "pilot": "strict_lite_alpha",
    }:
        raise ContractError("activation request contract is not closed")
    prime = value["prime"]
    run = value["run"]
    if not isinstance(prime, dict) or not isinstance(run, dict):
        raise ContractError("pilot stage contracts must be objects")
    if prime.get("intent_completeness_review") != "skip":
        raise ContractError("alpha must remove exactly the Prime intent reviewer")
    if (
        prime.get("bounded_direct_execution")
        != "required_before_intent_review_skip"
        or prime.get("plan_task_risk") != "required_mechanical_or_none"
        or prime.get("promotion_backfill")
        != "return_to_prime_review_reapprove_before_full_resume"
    ):
        raise ContractError("alpha must bind Prime omission to bounded direct work")
    if prime.get("three_doc_gate") != "keep" or prime.get("user_approval") != "keep":
        raise ContractError("alpha must retain the Prime execution gate and approval")
    if run.get("execution") != "existing_direct_route" or run.get("worktree") != "existing_direct_route":
        raise ContractError("alpha must reuse the existing direct route")
    for key in (
        "git_preflight",
        "recovery_guard",
        "contract_validation",
        "final_diff_check",
        "user_integration_choice",
    ):
        if run.get(key) != "keep":
            raise ContractError(f"alpha must retain {key}")
    if run.get("completion_verification") != "full_once":
        raise ContractError("alpha must retain full completion verification")
    if (
        run.get("final_independent_review") != "keep_bounded_lite_scope"
        or run.get("final_review_scope")
        != "acceptance_diff_changed_paths_verification_promotion"
    ):
        raise ContractError("alpha must retain a bounded independent final review")
    if run.get("harness_sync") != "skip_when_no_durable_change":
        raise ContractError("alpha harness omission must be conditional")
    promotions = set(_unique_strings(value["promote_to_full_on"], "promote_to_full_on"))
    required = {
        "changed_scope_expanded",
        "multiple_write_areas_discovered",
        "verification_gap_discovered",
        "hard_trigger_discovered",
        "profile_invalid_or_stale",
        "user_intent_conflict_discovered",
    }
    if not required <= promotions:
        raise ContractError("pilot promotion vocabulary is incomplete")
    return value


def validate_activation(value: Any, pilot: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("activation root must be an object")
    _exact_keys(value, ACTIVATION_KEYS, "activation")
    expected = pilot["activation_request"]
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != expected["schema_version"]
        or value["pilot"] != expected["pilot"]
        or type(value["enabled"]) is not bool
    ):
        raise ContractError("invalid activation request")
    return value


def validate_shadow(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("shadow root must be an object")
    _exact_keys(value, SHADOW_KEYS, "shadow")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["shadow_only"] is not True
        or value["cycle"] not in {"first", "delta"}
        or value["mode"] not in {"lite", "standard", "assurance"}
        or not isinstance(value["reasons"], list)
        or not isinstance(value["hard_triggers"], list)
        or not isinstance(value["missing_lite_required_true"], list)
        or not isinstance(value["violated_lite_required_false"], list)
        or type(value["harness_sync"]) is not bool
        or type(value["bounded_direct_execution"]) is not bool
    ):
        raise ContractError("invalid shadow record")
    return value


def validate_live_profile(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("live profile root must be an object")
    _exact_keys(value, PROFILE_KEYS, "live profile")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["contract_id"] != "leanforge.adaptive-assurance-live-profile"
        or value["profile"] != "strict_lite_alpha"
        or value["cycle"] != "delta"
        or value["reason"] != "lite_eligible"
        or type(value["harness_sync"]) is not bool
        or value["harness_sync"] is not False
        or type(value["bounded_direct_execution"]) is not bool
        or value["bounded_direct_execution"] is not True
    ):
        raise ContractError("invalid live profile")
    return value


def evaluate_plan_profile(profile: Any, plan: Any) -> dict[str, str]:
    """Return the authoritative pre-approval route for an observed PLAN surface."""
    try:
        validate_live_profile(profile)
    except ContractError:
        return dict(_FULL_PLAN)
    eligible = (
        isinstance(plan, dict)
        and set(plan) == PLAN_KEYS
        and type(plan["task_count"]) is int
        and plan["task_count"] == 1
        and isinstance(plan["task_risk"], str)
        and plan["task_risk"] in {"MECHANICAL", "NONE"}
        and type(plan["regeneration_barrier"]) is bool
        and plan["regeneration_barrier"] is False
        and type(plan["local_file_diff"]) is bool
        and plan["local_file_diff"] is True
        and type(plan["targeted_verification_sufficient"]) is bool
        and plan["targeted_verification_sufficient"] is True
    )
    return dict(_LITE_PLAN if eligible else _FULL_PLAN)


def derive_runtime_promotion(
    pilot: Any,
    profile: Any,
    trigger: Any,
    *,
    source_context_available: Any = True,
) -> dict[str, str]:
    """Derive the one safe transition after Run discovers a promotion trigger."""
    validate_pilot_contract(pilot)
    try:
        validate_live_profile(profile)
    except ContractError:
        pass
    if source_context_available is not True:
        return dict(_RUNTIME_CONTEXT_BLOCKED)
    return dict(_RUNTIME_PROMOTION)


def derive_profile(pilot: Any, activation: Any, shadow: Any) -> dict[str, Any] | None:
    pilot = validate_pilot_contract(pilot)
    activation = validate_activation(activation, pilot)
    shadow = validate_shadow(shadow)
    if not activation["enabled"]:
        return None
    if not (
        shadow["cycle"] == "delta"
        and shadow["mode"] == "lite"
        and shadow["reasons"] == ["lite_eligible"]
        and shadow["hard_triggers"] == []
        and shadow["missing_lite_required_true"] == []
        and shadow["violated_lite_required_false"] == []
        and shadow["harness_sync"] is False
        and shadow["bounded_direct_execution"] is True
    ):
        return None
    profile = {
        "schema_version": 1,
        "contract_id": "leanforge.adaptive-assurance-live-profile",
        "profile": "strict_lite_alpha",
        "cycle": "delta",
        "reason": "lite_eligible",
        "harness_sync": False,
        "bounded_direct_execution": True,
    }
    return validate_live_profile(profile)


def _tmp(path: Path) -> Path:
    return path.with_name(path.name + ".tmp")


def discard(path: Path) -> None:
    path.unlink(missing_ok=True)
    _tmp(path).unlink(missing_ok=True)


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = _tmp(path)
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--activation", type=Path, required=True)
    parser.add_argument("--shadow", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    discard(args.output)
    if not args.activation.exists():
        return 0
    try:
        profile = derive_profile(
            load_json(args.pilot), load_json(args.activation), load_json(args.shadow)
        )
    except (ContractError, OSError) as exc:
        print(f"strict Lite disabled; using Full Assurance: {exc}")
        discard(args.output)
        return 0
    if profile is not None:
        write_atomic(args.output, profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
