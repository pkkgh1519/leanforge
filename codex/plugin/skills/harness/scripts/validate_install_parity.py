from __future__ import annotations

from pathlib import Path

from validate_core import Issue, is_safe_repo_dir, is_safe_repo_file, read_text, relpath, safe_files_under
from validate_frontmatter import parse_frontmatter, strip_frontmatter_fields


def compare_skill_dirs(
    root: Path,
    source_dir: Path,
    generated_dir: Path,
    label: str,
    allowed_extra_files: set[str] | None = None,
    overlay_dir: Path | None = None,
    frontmatter_injection: dict[str, str] | None = None,
) -> list[Issue]:
    issues: list[Issue] = []
    allowed_extra_files = allowed_extra_files or set()

    if not is_safe_repo_dir(generated_dir, root):
        return [
            Issue(
                "error",
                "harness-generated-missing",
                relpath(generated_dir, root),
                f"missing generated {label} harness skill directory",
            )
        ]

    source_files = safe_files_under(source_dir, root)
    generated_files = safe_files_under(generated_dir, root)
    source_keys = set(source_files)
    generated_keys = set(generated_files)

    issues.extend(_missing_generated_file_issues(root, generated_dir, label, source_keys - generated_keys))
    issues.extend(
        _extra_generated_file_issues(
            root,
            generated_files,
            label,
            generated_keys - source_keys,
            allowed_extra_files,
            overlay_dir,
        )
    )
    issues.extend(_frontmatter_injection_issues(root, generated_files, label, frontmatter_injection))
    issues.extend(
        _generated_drift_issues(
            root,
            source_files,
            generated_files,
            label,
            source_keys & generated_keys,
            frontmatter_injection,
        )
    )
    return issues


def _missing_generated_file_issues(root: Path, generated_dir: Path, label: str, missing: set[str]) -> list[Issue]:
    return [
        Issue(
            "error",
            "harness-generated-missing",
            relpath(generated_dir / relative, root),
            f"generated {label} harness is missing canonical file: {relative}",
        )
        for relative in sorted(missing)
    ]


def _extra_generated_file_issues(
    root: Path,
    generated_files: dict[str, Path],
    label: str,
    extra: set[str],
    allowed_extra_files: set[str],
    overlay_dir: Path | None,
) -> list[Issue]:
    issues: list[Issue] = []
    for relative in sorted(extra):
        if relative not in allowed_extra_files:
            issues.append(
                Issue(
                    "error",
                    "harness-generated-extra",
                    relpath(generated_files[relative], root),
                    f"generated {label} harness has unexpected extra file: {relative}",
                )
            )
            continue
        if overlay_dir is None:
            continue
        issues.extend(_overlay_file_issues(root, generated_files[relative], label, overlay_dir / relative, relative))
    return issues


def _overlay_file_issues(root: Path, generated_path: Path, label: str, overlay_path: Path, relative: str) -> list[Issue]:
    if not is_safe_repo_file(overlay_path, root):
        return [
            Issue(
                "error",
                "harness-overlay-missing",
                relpath(overlay_path, root),
                f"missing declared {label} overlay file: {relative}",
            )
        ]
    if generated_path.read_bytes() != overlay_path.read_bytes():
        return [
            Issue(
                "error",
                "harness-overlay-drift",
                relpath(generated_path, root),
                f"generated {label} overlay differs from declared platform overlay: {relative}",
            )
        ]
    return []


def _frontmatter_injection_issues(
    root: Path,
    generated_files: dict[str, Path],
    label: str,
    frontmatter_injection: dict[str, str] | None,
) -> list[Issue]:
    if not frontmatter_injection or "SKILL.md" not in generated_files:
        return []

    frontmatter, error = parse_frontmatter(read_text(generated_files["SKILL.md"]))
    if error:
        return [
            Issue(
                "error",
                "harness-generated-frontmatter-invalid",
                relpath(generated_files["SKILL.md"], root),
                f"generated {label} SKILL.md frontmatter could not be parsed",
            )
        ]

    return [
        Issue(
            "error",
            "harness-generated-frontmatter-drift",
            relpath(generated_files["SKILL.md"], root),
            f"generated {label} SKILL.md is missing expected frontmatter field: {key}",
        )
        for key, expected in frontmatter_injection.items()
        if frontmatter.get(key) != expected
    ]


def _generated_drift_issues(
    root: Path,
    source_files: dict[str, Path],
    generated_files: dict[str, Path],
    label: str,
    common: set[str],
    frontmatter_injection: dict[str, str] | None,
) -> list[Issue]:
    issues: list[Issue] = []
    for relative in sorted(common):
        if _generated_file_matches(source_files[relative], generated_files[relative], relative, frontmatter_injection):
            continue
        issues.append(
            Issue(
                "error",
                "harness-generated-drift",
                relpath(generated_files[relative], root),
                f"generated {label} harness differs from canonical file: {relative}",
            )
        )
    return issues


def _generated_file_matches(
    source_path: Path,
    generated_path: Path,
    relative: str,
    frontmatter_injection: dict[str, str] | None,
) -> bool:
    if frontmatter_injection and relative == "SKILL.md":
        source_text = read_text(source_path)
        generated_text = strip_frontmatter_fields(read_text(generated_path), set(frontmatter_injection))
        return source_text == generated_text
    return source_path.read_bytes() == generated_path.read_bytes()
