"""Validation helpers for Leanforge Run-compatible repo-local harness artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

CUSTOM_AGENT_RESERVED_NAMES = {"default", "worker", "explorer", "reviewer"}
RUN_COMPATIBLE_USAGE_SECTION_RE = re.compile(r"(?im)^##\s+Leanforge Run usage\s*$")
RUN_COMPATIBLE_REQUIRED_TERMS = {
    "allowed phases": ["allowed phases", "final_review"],
    "never use for": ["never use for", "implementer replacement"],
    "inputs": ["inputs run must provide", "changed files"],
    "output": ["output", "blocking findings"],
}
RUN_COMPATIBLE_ACTIVE_DOC_RE = re.compile(
    r"\b(?:read|load|open|inspect)\s+`?\.dryforge/(?:handoff|spec|plan)\.md`?",
    re.IGNORECASE,
)
RUN_COMPATIBLE_IMPLEMENTER_TAKEOVER_RE = re.compile(
    r"\b(?:replace|instead of|take over|own)\s+(?:the\s+)?(?:leanforge\s+)?run\s+implementer\b",
    re.IGNORECASE,
)
RUN_COMPATIBLE_BROAD_TRIGGER_RE = re.compile(
    r"\b(?:all|any|every)\s+[\w -]{0,40}\bwork\b|\bordinary implementation tasks\b",
    re.IGNORECASE,
)


def is_run_compatible_skill(text: str, description: str) -> bool:
    return "leanforge run" in description.lower() or bool(RUN_COMPATIBLE_USAGE_SECTION_RE.search(text))


def validate_run_compatible_skill(
    root: Path,
    path: Path,
    text: str,
    description: str,
    issue: Callable[[str, str, str, str], Any],
    relpath: Callable[[Path, Path], str],
) -> list[Any]:
    if not is_run_compatible_skill(text, description):
        return []

    relative = relpath(path, root)
    issues: list[Any] = []
    lower_text = text.lower()
    missing = [label for label, terms in RUN_COMPATIBLE_REQUIRED_TERMS.items() if not all(term in lower_text for term in terms)]
    if not RUN_COMPATIBLE_USAGE_SECTION_RE.search(text) or missing:
        details = ", ".join(missing) if missing else "Leanforge Run usage"
        issues.append(issue("error", "run-compatible-skill-contract-missing", relative, "run-compatible repo skills must declare a Leanforge Run usage contract: " + details))
    if RUN_COMPATIBLE_ACTIVE_DOC_RE.search(text):
        issues.append(issue("error", "run-compatible-active-doc-dependency", relative, "run-compatible repo skills must receive current task context from Run, not read active .dryforge docs directly"))
    if RUN_COMPATIBLE_IMPLEMENTER_TAKEOVER_RE.search(text):
        issues.append(issue("error", "run-compatible-implementer-takeover", relative, "run-compatible repo skills may not replace the Leanforge Run implementer"))
    if RUN_COMPATIBLE_BROAD_TRIGGER_RE.search(description):
        issues.append(issue("warning", "run-compatible-skill-trigger-too-broad", relative, "run-compatible repo skill descriptions must avoid broad ordinary implementation triggers"))
    return issues


def validate_custom_agent_name(
    root: Path,
    path: Path,
    data: dict[str, Any],
    issue: Callable[[str, str, str, str], Any],
    relpath: Callable[[Path, Path], str],
) -> list[Any]:
    name = str(data.get("name", path.stem)).strip()
    if name not in CUSTOM_AGENT_RESERVED_NAMES:
        return []
    return [
        issue(
            "error",
            "custom-agent-name-reserved",
            relpath(path, root),
            f"custom agent name conflicts with a built-in role: {name}",
        )
    ]
