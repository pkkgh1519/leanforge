#!/usr/bin/env python3
"""Validate harness skill and generated harness artifacts.

This script is intentionally lightweight: it checks structural contracts,
frontmatter, link safety, optional custom-agent fields, and brittle runtime
assumptions. It does not score product quality or replace human review.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
COMMONMARK_BACKSLASH_ESCAPE_RE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~])")
REFERENCE_TARGET_RE = re.compile(r"references/[^\s]+")
ANGLE_REFERENCE_TARGET_RE = re.compile(r"<(references/[^\r\n<>]*)>")

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
    re.compile(r"\btask-log\.jsonl\b"),
    re.compile(r"\bdocs/operations\b"),
]

TEAM_SPEC_CONTRACTS = {
    "success criteria": ["success criteria", "success_criteria", "성공 기준", "완료 기준", "성공"],
    "validation": ["validation", "검증"],
    "handoff": ["handoff", "핸드오프", "인수인계"],
    "side-effect boundary": ["side-effect", "side effect", "부작용", "라이브", "live service"],
}

CUSTOM_AGENT_REQUIRED_FIELDS = {"name", "description", "developer_instructions"}
TRIGGERISH_DESCRIPTION_RE = re.compile(r"^(Use when|Use for|Use this when|Use this skill when)\b", re.IGNORECASE)
REFERENCE_DIRECTORY_TARGETS = {"references", "references/"}
TRAILING_REFERENCE_CHARS = (".", ",", ";", ":", "`", "\"", "'")
CANONICAL_HARNESS_DIR = Path("src") / "skills" / "harness"
CLAUDE_HARNESS_DIR = Path("claude") / "skills" / "harness"
CODEX_HARNESS_DIR = Path("codex") / "plugin" / "skills" / "harness"
CODEX_HARNESS_OVERLAY_DIR = Path("platform") / "codex" / "skills" / "harness"
CODEX_ALLOWED_EXTRA_FILES = {"agents/openai.yaml"}
CLAUDE_FRONTMATTER_INJECTION = {
    "disable-model-invocation": "true",
    "allowed-tools": "Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion",
}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def is_safe_repo_file(path: Path, root: Path) -> bool:
    if path.is_symlink():
        return False
    resolved = path.resolve(strict=False)
    return is_within(resolved, root) and resolved.is_file()


def is_safe_repo_dir(path: Path, root: Path) -> bool:
    if path.is_symlink():
        return False
    resolved = path.resolve(strict=False)
    return is_within(resolved, root) and resolved.is_dir()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing"
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            fields: dict[str, str] = {}
            frontmatter_lines = lines[1:index]
            line_index = 0
            while line_index < len(frontmatter_lines):
                raw_line = frontmatter_lines[line_index]
                if ":" not in raw_line or raw_line.lstrip().startswith("#"):
                    line_index += 1
                    continue
                key, value = raw_line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value in {">", "|", ">-", ">+", "|-", "|+"}:
                    block_lines: list[str] = []
                    line_index += 1
                    while line_index < len(frontmatter_lines):
                        block_line = frontmatter_lines[line_index]
                        if block_line.startswith((" ", "\t")) or not block_line.strip():
                            block_lines.append(block_line.strip())
                            line_index += 1
                            continue
                        break
                    if value.startswith(">"):
                        fields[key] = " ".join(part for part in block_lines if part).strip()
                    else:
                        fields[key] = "\n".join(block_lines).strip()
                    continue
                fields[key] = value.strip("\"'")
                line_index += 1
            return fields, None
    return {}, "unterminated"


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


def validate_skill_file(root: Path, path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = read_text(path)
    relative = relpath(path, root)
    frontmatter, error = parse_frontmatter(text)
    if error:
        code = "skill-frontmatter-missing" if error == "missing" else "skill-frontmatter-unterminated"
        return [Issue("error", code, relative, "SKILL.md must start with YAML frontmatter delimited by ---")]

    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()
    if not name:
        issues.append(Issue("error", "skill-frontmatter-field-missing", relative, "missing required frontmatter field: name"))
    elif not NAME_RE.match(name):
        issues.append(Issue("error", "skill-name-invalid", relative, "skill name must use lowercase letters, numbers, and hyphens"))

    if not description:
        issues.append(Issue("error", "skill-frontmatter-field-missing", relative, "missing required frontmatter field: description"))
    else:
        if not TRIGGERISH_DESCRIPTION_RE.search(description):
            issues.append(Issue("warning", "skill-description-trigger", relative, "description should be trigger-focused"))
        if len(description) > 500:
            issues.append(Issue("warning", "skill-description-long", relative, "description is longer than the recommended 500 characters"))

    issues.extend(validate_references_dir(root, path))
    issues.extend(validate_reference_links(root, path, text))
    return issues


def split_issues(issues: list[Issue]) -> tuple[list[Issue], list[Issue]]:
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    return errors, warnings


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


def validate_custom_agents(root: Path) -> list[Issue]:
    root = root.resolve(strict=False)
    agents_root = root / ".codex" / "agents"
    if not is_safe_repo_dir(agents_root, root):
        return []

    issues: list[Issue] = []
    for path in sorted(agents_root.glob("*.toml")):
        if not is_safe_repo_file(path, root):
            continue
        text = read_text(path)
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            issues.append(
                Issue(
                    "error",
                    "custom-agent-toml-invalid",
                    relpath(path, root),
                    f"custom agent TOML could not be parsed: {exc}",
                )
            )
            continue
        fields = set(data.keys())
        missing = sorted(CUSTOM_AGENT_REQUIRED_FIELDS - fields)
        if missing:
            issues.append(
                Issue(
                    "error",
                    "custom-agent-field-missing",
                    relpath(path, root),
                    "missing required custom-agent field(s): " + ", ".join(missing),
                )
            )
    return issues


def validate_team_specs(root: Path) -> list[Issue]:
    root = root.resolve(strict=False)
    harness_root = root / "docs" / "harness"
    if not is_safe_repo_dir(harness_root, root):
        return []

    issues: list[Issue] = []
    for path in sorted(harness_root.glob("**/team-spec.md")):
        if not is_safe_repo_file(path, root):
            continue
        text = read_text(path).lower()
        missing = [
            label
            for label, tokens in TEAM_SPEC_CONTRACTS.items()
            if not any(token.lower() in text for token in tokens)
        ]
        if missing:
            issues.append(
                Issue(
                    "error",
                    "team-spec-contract-missing",
                    relpath(path, root),
                    "team spec is missing contract section(s): " + ", ".join(missing),
                )
            )
    return issues


def safe_markdown_files_under(directory: Path, root: Path) -> Iterable[Path]:
    if not is_safe_repo_dir(directory, root):
        return
    for path in sorted(directory.glob("**/*.md")):
        if is_safe_repo_file(path, root):
            yield path


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


def validate_agents_md(root: Path) -> list[Issue]:
    root = root.resolve(strict=False)
    path = root / "AGENTS.md"
    if not is_safe_repo_file(path, root):
        return []
    line_count = len(read_text(path).splitlines())
    if line_count > 250:
        return [
            Issue(
                "warning",
                "agents-md-long",
                relpath(path, root),
                f"AGENTS.md has {line_count} lines; keep root guidance short and pointer-heavy",
            )
        ]
    return []


def safe_files_under(directory: Path, root: Path) -> dict[str, Path]:
    if not is_safe_repo_dir(directory, root):
        return {}
    files: dict[str, Path] = {}
    for path in sorted(directory.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if is_safe_repo_file(path, root):
            files[path.relative_to(directory).as_posix()] = path
    return files


def strip_frontmatter_fields(text: str, fields: set[str]) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() != "---":
            continue
        filtered = [lines[0]]
        for line in lines[1:index]:
            key = line.split(":", 1)[0].strip() if ":" in line else ""
            if key not in fields:
                filtered.append(line)
        filtered.extend(lines[index:])
        return "".join(filtered)
    return text


def validate_skill_dir(skill_dir: Path) -> tuple[list[Issue], list[Issue]]:
    skill_dir = skill_dir.resolve(strict=False)
    root = skill_dir
    issues: list[Issue] = []
    if not is_safe_repo_dir(skill_dir, root):
        issues.append(Issue("error", "skill-dir-missing", relpath(skill_dir, root), "skill directory does not exist"))
        return split_issues(issues)

    skill_file = skill_dir / "SKILL.md"
    if not is_safe_repo_file(skill_file, root):
        issues.append(Issue("error", "skill-file-missing", "SKILL.md", "skill directory is missing SKILL.md"))
    else:
        issues.extend(validate_skill_file(root, skill_file))

    scan_paths: list[Path] = []
    if is_safe_repo_file(skill_file, root):
        scan_paths.append(skill_file)
    scan_paths.extend(safe_markdown_files_under(skill_dir / "references", root))
    issues.extend(validate_banned_patterns_in_files(root, scan_paths))
    return split_issues(issues)


def validate_required_file(root: Path, path: Path, code: str, message: str) -> list[Issue]:
    if is_safe_repo_file(path, root):
        return []
    return [Issue("error", code, relpath(path, root), message)]


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

    for relative in sorted(source_keys - generated_keys):
        issues.append(
            Issue(
                "error",
                "harness-generated-missing",
                relpath(generated_dir / relative, root),
                f"generated {label} harness is missing canonical file: {relative}",
            )
        )

    for relative in sorted(generated_keys - source_keys):
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
        overlay_path = overlay_dir / relative
        if not is_safe_repo_file(overlay_path, root):
            issues.append(
                Issue(
                    "error",
                    "harness-overlay-missing",
                    relpath(overlay_path, root),
                    f"missing declared {label} overlay file: {relative}",
                )
            )
        elif generated_files[relative].read_bytes() != overlay_path.read_bytes():
            issues.append(
                Issue(
                    "error",
                    "harness-overlay-drift",
                    relpath(generated_files[relative], root),
                    f"generated {label} overlay differs from declared platform overlay: {relative}",
                )
            )

    if frontmatter_injection and "SKILL.md" in generated_files:
        frontmatter, error = parse_frontmatter(read_text(generated_files["SKILL.md"]))
        if error:
            issues.append(
                Issue(
                    "error",
                    "harness-generated-frontmatter-invalid",
                    relpath(generated_files["SKILL.md"], root),
                    f"generated {label} SKILL.md frontmatter could not be parsed",
                )
            )
        else:
            for key, expected in frontmatter_injection.items():
                if frontmatter.get(key) != expected:
                    issues.append(
                        Issue(
                            "error",
                            "harness-generated-frontmatter-drift",
                            relpath(generated_files["SKILL.md"], root),
                            f"generated {label} SKILL.md is missing expected frontmatter field: {key}",
                        )
                    )

    for relative in sorted(source_keys & generated_keys):
        if frontmatter_injection and relative == "SKILL.md":
            source_text = read_text(source_files[relative])
            generated_text = strip_frontmatter_fields(read_text(generated_files[relative]), set(frontmatter_injection))
            matches = source_text == generated_text
        else:
            matches = source_files[relative].read_bytes() == generated_files[relative].read_bytes()
        if not matches:
            issues.append(
                Issue(
                    "error",
                    "harness-generated-drift",
                    relpath(generated_files[relative], root),
                    f"generated {label} harness differs from canonical file: {relative}",
                )
            )
    return issues


def validate_harness_install(root: Path) -> tuple[list[Issue], list[Issue]]:
    root = root.resolve(strict=False)
    issues: list[Issue] = []
    if not root.exists() or not root.is_dir():
        issues.append(Issue("error", "repo-not-found", relpath(root, root), "target repository path does not exist"))
        return split_issues(issues)

    source_dir = root / CANONICAL_HARNESS_DIR
    if not is_safe_repo_dir(source_dir, root):
        issues.append(
            Issue(
                "error",
                "harness-source-missing",
                relpath(source_dir, root),
                "missing canonical src/skills/harness directory",
            )
        )
        return split_issues(issues)

    source_errors, source_warnings = validate_skill_dir(source_dir)
    issues.extend(Issue(issue.severity, issue.code, f"{CANONICAL_HARNESS_DIR.as_posix()}/{issue.path}", issue.message) for issue in source_errors)
    issues.extend(Issue(issue.severity, issue.code, f"{CANONICAL_HARNESS_DIR.as_posix()}/{issue.path}", issue.message) for issue in source_warnings)
    issues.extend(
        validate_required_file(
            root,
            source_dir / "scripts" / "validate_harness.py",
            "harness-validator-missing",
            "canonical harness skill is missing scripts/validate_harness.py",
        )
    )
    issues.extend(compare_skill_dirs(root, source_dir, root / CLAUDE_HARNESS_DIR, "Claude", frontmatter_injection=CLAUDE_FRONTMATTER_INJECTION))
    issues.extend(
        compare_skill_dirs(
            root,
            source_dir,
            root / CODEX_HARNESS_DIR,
            "Codex",
            allowed_extra_files=CODEX_ALLOWED_EXTRA_FILES,
            overlay_dir=root / CODEX_HARNESS_OVERLAY_DIR,
        )
    )
    return split_issues(issues)


def validate(root: Path) -> tuple[list[Issue], list[Issue]]:
    root = root.resolve()
    issues: list[Issue] = []

    if not root.exists() or not root.is_dir():
        issues.append(Issue("error", "repo-not-found", relpath(root, root), "target repository path does not exist"))
        return issues, []

    for skill_file in find_skill_files(root):
        issues.extend(validate_skill_file(root, skill_file))
    issues.extend(validate_custom_agents(root))
    issues.extend(validate_team_specs(root))
    issues.extend(validate_banned_patterns(root))
    issues.extend(validate_agents_md(root))

    return split_issues(issues)


def render_text(status: str, errors: list[Issue], warnings: list[Issue]) -> str:
    lines = [f"status={status}", f"errors={len(errors)} warnings={len(warnings)}"]
    for issue in [*errors, *warnings]:
        lines.append(f"{issue.severity.upper()} {issue.code} {issue.path}: {issue.message}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate harness skill and generated harness artifacts.")
    parser.add_argument("repo", nargs="?", type=Path, default=Path("."), help="Repository root containing generated harness artifacts.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--skill-dir", type=Path, help="Validate one standalone skill directory.")
    parser.add_argument("--install-check", action="store_true", help="Validate this plugin's canonical harness source and generated platform copies.")
    args = parser.parse_args(argv)

    if args.skill_dir and args.install_check:
        parser.error("--skill-dir and --install-check cannot be used together")

    if args.skill_dir:
        errors, warnings = validate_skill_dir(args.skill_dir)
    elif args.install_check:
        repo_errors, repo_warnings = validate(args.repo)
        install_errors, install_warnings = validate_harness_install(args.repo)
        errors = [*repo_errors, *install_errors]
        warnings = [*repo_warnings, *install_warnings]
    else:
        errors, warnings = validate(args.repo)
    status = "fail" if errors else "ok"

    if args.json:
        payload = {
            "status": status,
            "errors": [issue.as_dict() for issue in errors],
            "warnings": [issue.as_dict() for issue in warnings],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_text(status, errors, warnings))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
