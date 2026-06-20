"""Validation helpers for dryforge go-compatible repo-local harness artifacts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

CUSTOM_AGENT_RESERVED_NAMES = {"default", "worker", "explorer", "reviewer"}
GO_COMPATIBLE_USAGE_SECTION_RE = re.compile(r"(?im)^##\s+Dryforge go usage\s*$")
GO_COMPATIBLE_REQUIRED_TERMS = {
    "allowed phases": ["allowed phases", "final_review"],
    "never use for": ["never use for", "implementer replacement"],
    "inputs": ["inputs go must provide", "changed files"],
    "output": ["output", "blocking findings"],
}
GO_COMPATIBLE_ACTIVE_DOC_RE = re.compile(
    r"\b(?:read|load|open|inspect)\s+`?\.dryforge/(?:handoff|spec|plan)\.md`?",
    re.IGNORECASE,
)
GO_COMPATIBLE_IMPLEMENTER_TAKEOVER_RE = re.compile(
    r"\b(?:replace|instead of|take over|own)\s+(?:the\s+)?(?:dryforge\s+)?go\s+implementer\b",
    re.IGNORECASE,
)
GO_COMPATIBLE_BROAD_TRIGGER_RE = re.compile(
    r"\b(?:all|any|every)\s+[\w -]{0,40}\bwork\b|\bordinary implementation tasks\b",
    re.IGNORECASE,
)


def is_go_compatible_skill(text: str, description: str) -> bool:
    return "dryforge go" in description.lower() or bool(GO_COMPATIBLE_USAGE_SECTION_RE.search(text))


def validate_go_compatible_skill(
    root: Path,
    path: Path,
    text: str,
    description: str,
    issue: Callable[[str, str, str, str], Any],
    relpath: Callable[[Path, Path], str],
) -> list[Any]:
    if not is_go_compatible_skill(text, description):
        return []

    relative = relpath(path, root)
    issues: list[Any] = []
    lower_text = text.lower()
    missing = [label for label, terms in GO_COMPATIBLE_REQUIRED_TERMS.items() if not all(term in lower_text for term in terms)]
    if not GO_COMPATIBLE_USAGE_SECTION_RE.search(text) or missing:
        details = ", ".join(missing) if missing else "Dryforge go usage"
        issues.append(issue("error", "go-compatible-skill-contract-missing", relative, "go-compatible repo skills must declare a Dryforge go usage contract: " + details))
    if GO_COMPATIBLE_ACTIVE_DOC_RE.search(text):
        issues.append(issue("error", "go-compatible-active-doc-dependency", relative, "go-compatible repo skills must receive current task context from go, not read active .dryforge docs directly"))
    if GO_COMPATIBLE_IMPLEMENTER_TAKEOVER_RE.search(text):
        issues.append(issue("error", "go-compatible-implementer-takeover", relative, "go-compatible repo skills may not replace the dryforge go implementer"))
    if GO_COMPATIBLE_BROAD_TRIGGER_RE.search(description):
        issues.append(issue("warning", "go-compatible-skill-trigger-too-broad", relative, "go-compatible repo skill descriptions must avoid broad ordinary implementation triggers"))
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
