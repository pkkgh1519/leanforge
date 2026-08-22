#!/usr/bin/env python3
"""Deterministic, shadow-only Adaptive Assurance router.

This module is a development oracle. It never changes Prime or Run control flow.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


class ContractError(ValueError):
    pass


CONTRACT_KEYS = {
    "schema_version",
    "contract_id",
    "shadow_only",
    "modes",
    "mode_order",
    "default_mode",
    "first_cycle_mode",
    "decision_reasons",
    "hard_assurance_triggers",
    "facts",
    "lite",
    "durable_change_triggers",
    "escalation_signals",
    "evidence_reuse",
}
CASE_KEYS = {"schema_version", "case_id", "cycle", "facts", "triggers"}
EVIDENCE_KEYS = {
    "outcome",
    "base_sha",
    "environment_fingerprint",
    "relevant_scope_hash",
    "verify_set",
}
SHADOW_KEYS = {
    "schema_version",
    "shadow_only",
    "cycle",
    "mode",
    "reasons",
    "hard_triggers",
    "missing_lite_required_true",
    "violated_lite_required_false",
    "harness_sync",
}
DECISION_REASONS = (
    "first_cycle",
    "hard_assurance_trigger",
    "lite_eligible",
    "standard_default",
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON {path}: {exc}") from exc


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
        or not all(isinstance(x, str) and x for x in value)
    ):
        raise ContractError(f"{where} must be a non-empty string list")
    if len(value) != len(set(value)):
        raise ContractError(f"{where} must not contain duplicates")
    return tuple(value)


def validate_contract(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("contract root must be an object")
    _exact_keys(value, CONTRACT_KEYS, "contract")
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["contract_id"] != "leanforge.adaptive-assurance"
    ):
        raise ContractError("unsupported contract identity")
    if value["shadow_only"] is not True:
        raise ContractError("phase 1 must remain shadow_only=true")

    modes = _unique_strings(value["modes"], "modes")
    mode_order = _unique_strings(value["mode_order"], "mode_order")
    if modes != ("lite", "standard", "assurance") or mode_order != modes:
        raise ContractError("mode order must be lite, standard, assurance")
    if value["default_mode"] != "standard" or value["first_cycle_mode"] != "assurance":
        raise ContractError("unexpected routing defaults")
    if _unique_strings(value["decision_reasons"], "decision_reasons") != DECISION_REASONS:
        raise ContractError("decision reason vocabulary is not the closed v1 set")

    facts = set(_unique_strings(value["facts"], "facts"))
    hard = set(
        _unique_strings(value["hard_assurance_triggers"], "hard_assurance_triggers")
    )
    if "unknown_material_risk" not in hard:
        raise ContractError("unknown material risk must fail closed to Assurance")
    lite = value["lite"]
    if not isinstance(lite, dict) or set(lite) != {"required_true", "required_false"}:
        raise ContractError("lite contract must be closed")
    required_true = set(_unique_strings(lite["required_true"], "lite.required_true"))
    required_false = set(_unique_strings(lite["required_false"], "lite.required_false"))
    if required_true & required_false or (required_true | required_false) != facts:
        raise ContractError("Lite fact sets must partition the closed fact vocabulary")

    durable = set(
        _unique_strings(value["durable_change_triggers"], "durable_change_triggers")
    )
    if not durable <= required_false:
        raise ContractError("durable changes must disqualify Lite")

    escalation = value["escalation_signals"]
    if not isinstance(escalation, dict) or set(escalation) != {
        "to_standard",
        "to_assurance",
    }:
        raise ContractError("escalation_signals must be closed")
    standard = set(
        _unique_strings(escalation["to_standard"], "escalation.to_standard")
    )
    assurance = set(
        _unique_strings(escalation["to_assurance"], "escalation.to_assurance")
    )
    if standard & assurance:
        raise ContractError("escalation sets must be disjoint")

    reuse = value["evidence_reuse"]
    if not isinstance(reuse, dict) or set(reuse) != {
        "required_prior_outcome",
        "required_equal",
    }:
        raise ContractError("evidence_reuse must be closed")
    if (
        reuse["required_prior_outcome"] != "green"
        or set(
            _unique_strings(
                reuse["required_equal"], "evidence_reuse.required_equal"
            )
        )
        != EVIDENCE_KEYS - {"outcome"}
    ):
        raise ContractError("invalid evidence reuse contract")
    return value


def validate_case(case: Any, contract: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise ContractError("case root must be an object")
    _exact_keys(case, CASE_KEYS, "case")
    if (
        type(case["schema_version"]) is not int
        or case["schema_version"] != 1
        or case["cycle"] not in {"first", "delta"}
    ):
        raise ContractError("invalid case identity")
    if not isinstance(case["case_id"], str) or not case["case_id"]:
        raise ContractError("case_id must be non-empty")

    facts = case["facts"]
    if not isinstance(facts, dict) or set(facts) != set(contract["facts"]):
        raise ContractError("case facts must match the closed vocabulary")
    if not all(type(v) is bool for v in facts.values()):
        raise ContractError("case facts must be booleans")

    triggers = case["triggers"]
    if not isinstance(triggers, list) or len(triggers) != len(set(triggers)):
        raise ContractError("triggers must be a unique list")
    unknown = set(triggers) - set(contract["hard_assurance_triggers"])
    if unknown:
        raise ContractError(f"unknown hard triggers: {sorted(unknown)}")
    return case


@dataclass(frozen=True)
class Decision:
    mode: str
    reasons: tuple[str, ...]
    hard_triggers: tuple[str, ...]
    lite_missing_true: tuple[str, ...]
    lite_violated_false: tuple[str, ...]
    shadow_only: bool = True

    def as_shadow_dict(self, cycle: str, harness_sync: bool) -> dict[str, Any]:
        payload = {
            "schema_version": 1,
            "shadow_only": self.shadow_only,
            "cycle": cycle,
            "mode": self.mode,
            "reasons": list(self.reasons),
            "hard_triggers": list(self.hard_triggers),
            "missing_lite_required_true": list(self.lite_missing_true),
            "violated_lite_required_false": list(self.lite_violated_false),
            "harness_sync": harness_sync,
        }
        _exact_keys(payload, SHADOW_KEYS, "shadow payload")
        return payload


def route_case(case: Any, contract: Any) -> Decision:
    contract = validate_contract(contract)
    case = validate_case(case, contract)
    triggers = tuple(sorted(case["triggers"]))
    if case["cycle"] == "first":
        return Decision("assurance", ("first_cycle",), triggers, (), ())
    if triggers:
        return Decision("assurance", ("hard_assurance_trigger",), triggers, (), ())

    facts = case["facts"]
    missing = tuple(
        sorted(k for k in contract["lite"]["required_true"] if not facts[k])
    )
    violated = tuple(
        sorted(k for k in contract["lite"]["required_false"] if facts[k])
    )
    if not missing and not violated:
        return Decision("lite", ("lite_eligible",), (), (), ())
    return Decision("standard", ("standard_default",), (), missing, violated)


def harness_sync_required(case: Any, contract: Any) -> bool:
    contract = validate_contract(contract)
    case = validate_case(case, contract)
    return case["cycle"] == "first" or any(
        case["facts"][k] for k in contract["durable_change_triggers"]
    )


def shadow_payload(case: Any, contract: Any) -> dict[str, Any]:
    contract = validate_contract(contract)
    case = validate_case(case, contract)
    decision = route_case(case, contract)
    if not set(decision.reasons) <= set(contract["decision_reasons"]):
        raise ContractError("decision emitted an undeclared reason")
    return decision.as_shadow_dict(
        case["cycle"], harness_sync_required(case, contract)
    )


def escalate_mode(current: str, signals: Sequence[str], contract: Any) -> str:
    contract = validate_contract(contract)
    order = tuple(contract["mode_order"])
    if current not in order or isinstance(signals, (str, bytes)):
        raise ContractError("invalid escalation input")
    standard = set(contract["escalation_signals"]["to_standard"])
    assurance = set(contract["escalation_signals"]["to_assurance"])
    seen = set(signals)
    if seen - standard - assurance:
        requested = "assurance"
    elif seen & assurance:
        requested = "assurance"
    elif seen & standard:
        requested = "standard"
    else:
        requested = current
    return order[max(order.index(current), order.index(requested))]


def can_reuse_evidence(prior: Any, current: Any, contract: Any) -> bool:
    contract = validate_contract(contract)
    for name, value in (("prior", prior), ("current", current)):
        if not isinstance(value, dict):
            raise ContractError(f"{name} evidence must be an object")
        _exact_keys(value, EVIDENCE_KEYS, f"{name} evidence")
        if not all(
            isinstance(value[k], str) and value[k] for k in EVIDENCE_KEYS
        ):
            raise ContractError(f"{name} evidence values must be non-empty strings")
    reuse = contract["evidence_reuse"]
    return prior["outcome"] == reuse["required_prior_outcome"] and all(
        prior[k] == current[k] for k in reuse["required_equal"]
    )
