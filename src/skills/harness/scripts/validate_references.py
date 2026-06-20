from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterable

from validate_core import Issue, is_safe_repo_dir, is_safe_repo_file, is_within, relpath


COMMONMARK_BACKSLASH_ESCAPE_RE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~])")
REFERENCE_TARGET_RE = re.compile(r"references/[^\s]+")
ANGLE_REFERENCE_TARGET_RE = re.compile(r"<(references/[^\r\n<>]*)>")
REFERENCE_DIRECTORY_TARGETS = {"references", "references/"}
TRAILING_REFERENCE_CHARS = (".", ",", ";", ":", "`", "\"", "'")


def validate_references_dir(root: Path, skill_path: Path) -> list[Issue]:
    references_dir = skill_path.parent / "references"
    if (references_dir.exists() or references_dir.is_symlink()) and not is_safe_repo_dir(references_dir, root):
        return [
            Issue(
                "error",
                "skill-reference-unsafe",
                relpath(skill_path, root),
                "references directory is unsafe",
            )
        ]
    return []


def normalize_reference_text(text: str) -> str:
    unescaped = COMMONMARK_BACKSLASH_ESCAPE_RE.sub(r"\1", text)
    return html.unescape(unescaped)


def normalize_reference_target(raw_target: str) -> str:
    target = normalize_reference_text(raw_target).strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    target = target.strip("`\"'")
    return target.split("#", 1)[0]


def reference_target_variants(raw_target: str) -> list[str]:
    variants: list[str] = []

    def add(value: str) -> None:
        value = value.strip()
        if value and value not in variants:
            variants.append(value)

    current = normalize_reference_target(raw_target)
    add(current)
    while current:
        changed = False
        if current.endswith(TRAILING_REFERENCE_CHARS):
            current = current[:-1]
            add(current)
            changed = True
        while current.endswith(")") and current.count(")") > current.count("("):
            current = current[:-1]
            add(current)
            changed = True
        if not changed:
            break
    return variants


def is_reference_directory_mention(target: str) -> bool:
    return target.strip().strip("`\"'.,;:") in REFERENCE_DIRECTORY_TARGETS


def iter_reference_targets(text: str) -> Iterable[str]:
    seen: set[str] = set()
    backslash_normalized_text = COMMONMARK_BACKSLASH_ESCAPE_RE.sub(r"\1", text)
    normalized_text = html.unescape(backslash_normalized_text)

    for source in (backslash_normalized_text, normalized_text):
        for pattern in (ANGLE_REFERENCE_TARGET_RE, REFERENCE_TARGET_RE):
            for match in pattern.finditer(source):
                target = normalize_reference_target(match.group(1) if pattern is ANGLE_REFERENCE_TARGET_RE else match.group(0))
                if target.startswith("references/") and target not in seen:
                    seen.add(target)
                    yield target


def validate_reference_links(root: Path, skill_path: Path, text: str) -> list[Issue]:
    issues: list[Issue] = []
    raw_references_root = skill_path.parent / "references"
    references_root = raw_references_root.resolve(strict=False)
    for reference_target in iter_reference_targets(text):
        variants = [
            variant
            for variant in reference_target_variants(reference_target)
            if not is_reference_directory_mention(variant)
        ]
        if not variants:
            continue
        if raw_references_root.exists() and not is_safe_repo_dir(raw_references_root, root):
            issues.append(
                Issue(
                    "error",
                    "skill-reference-unsafe",
                    relpath(skill_path, root),
                    f"references directory is unsafe: {reference_target}",
                )
            )
        elif any(
            not is_within((skill_path.parent / variant).resolve(strict=False), references_root)
            or not is_within((skill_path.parent / variant).resolve(strict=False), root)
            or (skill_path.parent / variant).is_symlink()
            for variant in variants
        ):
            issues.append(
                Issue(
                    "error",
                    "skill-reference-unsafe",
                    relpath(skill_path, root),
                    f"linked reference escapes references directory: {reference_target}",
                )
            )
        elif not any(is_safe_repo_file(skill_path.parent / variant, root) for variant in variants):
            issues.append(
                Issue(
                    "error",
                    "skill-reference-missing",
                    relpath(skill_path, root),
                    f"linked reference does not exist: {reference_target}",
                )
            )
    return issues
