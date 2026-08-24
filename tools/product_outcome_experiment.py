#!/usr/bin/env python3
"""Evaluate whether Leanforge's public surfaces promise and show a trusted change."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


PLUGIN_DESCRIPTION = (
    "Turn a software goal into an approved change contract, then implement and "
    "verify the change with evidence, remaining risks, and a user-owned "
    "integration choice."
)
CODEX_SHORT_DESCRIPTION = "Turn a software goal into a verified change ready to integrate."
FINAL_RESULT_START = "<!-- leanforge:run-final-result-contract:start -->"
FINAL_RESULT_END = "<!-- leanforge:run-final-result-contract:end -->"
FINAL_RESULT_LABELS = ("Change", "Verification", "Remaining risk", "Integration")
PRIMARY_COPY_FORBIDDEN = ("3-doc", "grounded 3-doc", "any input")
UNSUPPORTED_PERFORMANCE_PATTERNS = (
    re.compile(r"\b(?:always|every task)\b.{0,30}\bfaster\b", re.IGNORECASE),
    re.compile(r"\bguarantee(?:s|d)?\b.{0,30}\b(?:faster|cheaper)\b", re.IGNORECASE),
    re.compile(r"모든 작업.{0,30}더 빠", re.IGNORECASE),
    re.compile(r"항상.{0,30}(?:시간|비용).{0,20}줄", re.IGNORECASE),
)


@dataclass(frozen=True)
class Check:
    id: str
    passed: bool
    detail: str


class RepositoryView:
    def __init__(self, root: Path, overrides: Mapping[str, str] | None = None) -> None:
        self.root = root
        self.overrides = dict(overrides or {})

    def text(self, relative: str) -> str:
        if relative in self.overrides:
            return self.overrides[relative]
        try:
            return (self.root / relative).read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def json(self, relative: str) -> dict:
        body = self.text(relative)
        if not body:
            return {}
        try:
            value = json.loads(body)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}


def _frontmatter(document: str) -> str:
    if not document.startswith("---\n"):
        return ""
    parts = document.split("---\n", 2)
    return parts[1] if len(parts) == 3 else ""


def _extract_between(document: str, start: str, end: str) -> str:
    if document.count(start) != 1 or document.count(end) != 1:
        return ""
    start_index = document.index(start) + len(start)
    end_index = document.index(end, start_index)
    return document[start_index:end_index]


def _contains_all(document: str, terms: Sequence[str]) -> bool:
    return all(term in document for term in terms)


def _head(document: str, lines: int = 35) -> str:
    return "\n".join(document.splitlines()[:lines])


def _check_readme_outcome(view: RepositoryView) -> Check:
    english = _head(view.text("README.md"))
    korean = _head(view.text("README_KO.md"))
    english_ok = _contains_all(
        english,
        ("reviewed, verified change ready to integrate", "actual", "evidence", "remaining risks", "integration choice"),
    )
    korean_ok = _contains_all(korean, ("검토·검증된", "변경", "검증 증거", "남은 위험", "통합 선택"))
    forbidden = [term for term in PRIMARY_COPY_FORBIDDEN if term.casefold() in english.casefold()]
    passed = english_ok and korean_ok and not forbidden
    return Check(
        "readme-outcome-promise",
        passed,
        "English and Korean introductions lead with the trusted-change outcome"
        if passed
        else f"english_ok={english_ok}, korean_ok={korean_ok}, forbidden={forbidden}",
    )


def _check_marketplace_outcome(view: RepositoryView) -> Check:
    claude = view.json("platform/claude/plugin.json")
    codex = view.json("platform/codex/plugin.json")
    generated_claude = view.json("claude/.claude-plugin/plugin.json")
    generated_codex = view.json("codex/plugin/.codex-plugin/plugin.json")
    marketplace = view.json(".claude-plugin/marketplace.json")
    interface = codex.get("interface", {}) if isinstance(codex.get("interface"), dict) else {}
    primary = "\n".join(str(value) for value in (
        marketplace.get("description", ""),
        claude.get("description", ""),
        codex.get("description", ""),
        interface.get("shortDescription", ""),
        interface.get("longDescription", ""),
    ))
    forbidden = [term for term in PRIMARY_COPY_FORBIDDEN if term.casefold() in primary.casefold()]
    descriptions = (
        claude.get("description"),
        codex.get("description"),
        generated_claude.get("description"),
        generated_codex.get("description"),
    )
    passed = (
        all(value == PLUGIN_DESCRIPTION for value in descriptions)
        and interface.get("shortDescription") == CODEX_SHORT_DESCRIPTION
        and "integration choice" in str(interface.get("longDescription", ""))
        and "verified change ready to integrate" in str(marketplace.get("description", ""))
        and not forbidden
    )
    return Check(
        "marketplace-outcome-promise",
        passed,
        "Claude and Codex marketplace surfaces are outcome-first and generated-parity clean"
        if passed
        else f"descriptions={descriptions}, forbidden={forbidden}",
    )


def _check_skill_outcomes(view: RepositoryView) -> Check:
    required = {
        "src/skills/prime/SKILL.md": ("approval-ready change contract", "user-owned decisions"),
        "src/skills/run/SKILL.md": ("actual change", "captured", "remaining risks", "user-owned integration choice"),
        "src/skills/set/SKILL.md": ("durable project context", "without rediscovering settled decisions"),
        "src/skills/run-tdd/SKILL.md": ("Implement and verify", "selective TDD"),
        "platform/codex/skills/prime/agents/openai.yaml": ("approval-ready change contract",),
        "platform/codex/skills/run/agents/openai.yaml": ("Implement and verify an approved Leanforge change",),
        "platform/codex/skills/set/agents/openai.yaml": ("durable project context",),
        "platform/codex/skills/run-tdd/agents/openai.yaml": ("Implement and verify an approved change with selective TDD",),
    }
    missing: dict[str, list[str]] = {}
    for relative, terms in required.items():
        body = view.text(relative)
        inspected = _frontmatter(body) if relative.endswith("SKILL.md") else body
        absent = [term for term in terms if term not in inspected]
        if absent:
            missing[relative] = absent
    passed = not missing
    return Check(
        "skill-outcome-descriptions",
        passed,
        "Every command description names its user outcome" if passed else f"missing={missing}",
    )


def _check_final_result_contract(view: RepositoryView) -> Check:
    run = view.text("src/skills/run/SKILL.md")
    section = _extract_between(run, FINAL_RESULT_START, FINAL_RESULT_END)
    labels_present = all(f"**{label}**" in section for label in FINAL_RESULT_LABELS)
    order = [section.find(f"**{label}**") for label in FINAL_RESULT_LABELS]
    ordered = all(index >= 0 for index in order) and order == sorted(order)
    boundary_terms = _contains_all(
        section,
        (
            "commands or observations",
            "exit codes",
            "unverified scope",
            "merge, PR/push, or feature-branch handoff",
            "authoritative readback",
            "terminal blocker",
            "completed or preserved state",
            "not integration-ready",
            "internal plumbing",
        ),
    )
    generated = (view.text("claude/skills/run/SKILL.md"), view.text("codex/plugin/skills/run/SKILL.md"))
    generated_match = all(_extract_between(body, FINAL_RESULT_START, FINAL_RESULT_END) == section for body in generated)
    passed = bool(section) and labels_present and ordered and boundary_terms and generated_match
    return Check(
        "run-final-result-contract",
        passed,
        "Run requires a four-part final result and both generated packages match"
        if passed
        else f"section={bool(section)}, labels={labels_present}, ordered={ordered}, boundary_terms={boundary_terms}, generated_match={generated_match}",
    )


def _check_consumer_contract(view: RepositoryView) -> Check:
    contracts = view.text("docs/contracts.md")
    installation = view.text("docs/installation.md")
    passed = _contains_all(contracts, ("**변경**", "**검증**", "**남은 위험**", "**통합**")) and _contains_all(
        installation, ("**Change**", "**Verification**", "**Remaining risk**", "**Integration**")
    )
    return Check(
        "consumer-contract-alignment",
        passed,
        "Consumer and installation docs expose the same four-part result" if passed else "consumer or installation result labels are missing",
    )


def _check_golden_cycle(view: RepositoryView) -> Check:
    readme = view.text("examples/trusted-change-package/README.md")
    contract = view.text("examples/trusted-change-package/contract.md")
    result = view.text("examples/trusted-change-package/result.md")
    headings = [result.find(f"## {label}") for label in FINAL_RESULT_LABELS]
    ordered = all(index >= 0 for index in headings) and headings == sorted(headings)
    passed = (
        _contains_all(readme, ("sanitized replay", "not installed-host execution evidence", "does not establish Time to Trusted Change"))
        and _contains_all(contract, ("## Goal", "## Scope", "## Non-goals", "## Acceptance"))
        and ordered
        and _contains_all(
            result,
            (
                "5ee31e6647f94f69dce6ad2e2b2ccd970746d0b3",
                "cbbb90758d28112a0918a1f999b841b9e8f7a7e6",
                "15/15",
                "279/279",
                "bash build/build.sh",
                "exit 0",
                "not merged",
            ),
        )
    )
    return Check(
        "golden-cycle-package",
        passed,
        "The completed example traces contract, change, evidence, risk, and integration"
        if passed
        else "the trusted-change example is incomplete or overclaims host evidence",
    )


def _check_no_unsupported_performance_claim(view: RepositoryView) -> Check:
    public_copy = "\n".join((
        _head(view.text("README.md"), 90),
        _head(view.text("README_KO.md"), 90),
        view.text("platform/claude/plugin.json"),
        view.text("platform/codex/plugin.json"),
        view.text(".claude-plugin/marketplace.json"),
    ))
    matches = [pattern.pattern for pattern in UNSUPPORTED_PERFORMANCE_PATTERNS if pattern.search(public_copy)]
    passed = not matches
    return Check(
        "unsupported-performance-claims-absent",
        passed,
        "Public copy does not claim unmeasured speed or cost improvement" if passed else f"unsupported patterns={matches}",
    )


def evaluate(root: Path, overrides: Mapping[str, str] | None = None) -> dict:
    view = RepositoryView(root.resolve(), overrides)
    checks = (
        _check_readme_outcome(view),
        _check_marketplace_outcome(view),
        _check_skill_outcomes(view),
        _check_final_result_contract(view),
        _check_consumer_contract(view),
        _check_golden_cycle(view),
        _check_no_unsupported_performance_claim(view),
    )
    passed_count = sum(check.passed for check in checks)
    return {
        "schema_version": 1,
        "experiment_id": "leanforge.product-outcome.minimum-v1",
        "root": str(root.resolve()),
        "passed": passed_count == len(checks),
        "score": {"passed": passed_count, "total": len(checks)},
        "checks": [asdict(check) for check in checks],
        "limitations": [
            "This deterministic surface experiment does not invoke Claude Code or Codex.",
            "It does not measure Time to Trusted Change, token cost, question count, or defect rate.",
            "Installed-host behavior still requires captured host traces and artifacts.",
        ],
    }


def render_text(result: Mapping[str, object]) -> str:
    score = result["score"]
    assert isinstance(score, Mapping)
    lines = [f"product outcome experiment: {score['passed']}/{score['total']}"]
    checks = result["checks"]
    assert isinstance(checks, list)
    for check in checks:
        assert isinstance(check, Mapping)
        mark = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- {mark} {check['id']}: {check['detail']}")
    limitations = result["limitations"]
    assert isinstance(limitations, list)
    for limitation in limitations:
        lines.append(f"- LIMITATION: {limitation}")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root to evaluate")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = evaluate(args.root)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else render_text(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
