from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from validate_core import Issue, is_safe_repo_dir, is_safe_repo_file, read_text, relpath, safe_markdown_files_under


FIXED_MODEL_PATTERNS = [
    re.compile(r"\bgpt-\d(?:[.\w-]*)?", re.IGNORECASE),
    re.compile(r"\bclaude-[\w.-]+", re.IGNORECASE),
    re.compile(r"\bgemini-[\w.-]+", re.IGNORECASE),
    re.compile(r"(?m)^\s*(?:model|reasoning_effort|service_tier)\s*="),
]

RUNTIME_PEER_PATTERNS = [
    re.compile(r"\b(?:send_message|followup_task|wait_agent)\b"),
    re.compile(r"\b(?:use|require|depend on|coordinate through|rely on)\s+peer-to-peer runtime messaging\b", re.IGNORECASE),
    re.compile(r"\bpeer updates between agents\b", re.IGNORECASE),
]

OPERATION_COUPLING_PATTERNS = [
    re.compile(r"\bOPERATIONS_SUMMARY\b"),
    re.compile(r"\bdocs/operations\b"),
]


def find_skill_files(root: Path) -> list[Path]:
    root = root.resolve(strict=False)
    skills_root = root / ".agents" / "skills"
    if not is_safe_repo_dir(skills_root, root):
        return []
    skill_files: list[Path] = []
    for skill_dir in sorted(skills_root.iterdir()):
        if not is_safe_repo_dir(skill_dir, root):
            continue
        skill_file = skill_dir / "SKILL.md"
        if is_safe_repo_file(skill_file, root):
            skill_files.append(skill_file)
    return skill_files


def files_to_scan(root: Path) -> Iterable[Path]:
    root = root.resolve(strict=False)
    candidates: list[Path] = []
    skill_files = find_skill_files(root)
    candidates.extend(skill_files)
    for skill_file in skill_files:
        candidates.extend(safe_markdown_files_under(skill_file.parent / "references", root))
    candidates.extend(safe_markdown_files_under(root / "docs" / "harness", root))
    agents_root = root / ".codex" / "agents"
    if is_safe_repo_dir(agents_root, root):
        candidates.extend(path for path in sorted(agents_root.glob("*.toml")) if is_safe_repo_file(path, root))
    for extra in [root / "AGENTS.md", root / ".codex" / "config.toml"]:
        if is_safe_repo_file(extra, root):
            candidates.append(extra)

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve(strict=False)
        if resolved not in seen and is_safe_repo_file(path, root):
            seen.add(resolved)
            yield path


def validate_banned_patterns(root: Path) -> list[Issue]:
    return validate_banned_patterns_in_files(root, files_to_scan(root))


def validate_banned_patterns_in_files(root: Path, paths: Iterable[Path]) -> list[Issue]:
    issues: list[Issue] = []
    for path in paths:
        text = read_text(path)
        relative = relpath(path, root)
        if any(pattern.search(text) for pattern in FIXED_MODEL_PATTERNS):
            issues.append(
                Issue(
                    "error",
                    "fixed-model-pin",
                    relative,
                    "harness artifacts must not depend on fixed model pins or runtime tuning fields",
                )
            )
        if any(pattern.search(text) for pattern in RUNTIME_PEER_PATTERNS):
            issues.append(
                Issue(
                    "error",
                    "runtime-peer-messaging",
                    relative,
                    "harness artifacts must not depend on peer-to-peer runtime messaging tools",
                )
            )
        if any(pattern.search(text) for pattern in OPERATION_COUPLING_PATTERNS):
            issues.append(
                Issue(
                    "warning",
                    "operation-artifact-coupling",
                    relative,
                    "operation artifact paths should be evidence, not a hard harness dependency",
                )
            )
    return issues
