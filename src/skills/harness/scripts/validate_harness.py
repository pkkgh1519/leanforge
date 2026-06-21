#!/usr/bin/env python3
"""Validate harness skill and generated harness artifacts.

This script is intentionally lightweight: it checks structural contracts,
frontmatter, link safety, optional custom-agent fields, and brittle runtime
assumptions. It does not score product quality or replace human review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_core import Issue, is_safe_repo_dir, is_safe_repo_file, read_text, relpath, safe_markdown_files_under, split_issues
from validate_frontmatter import parse_frontmatter
from validate_run_compat import validate_custom_agent_name, validate_run_compatible_skill
from validate_install_parity import compare_skill_dirs
from validate_pattern_scan import find_skill_files, validate_banned_patterns, validate_banned_patterns_in_files
from validate_references import validate_reference_links, validate_references_dir


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TEAM_SPEC_CONTRACTS = {
    "success criteria": ["success criteria", "success_criteria", "성공 기준", "완료 기준", "성공"],
    "validation": ["validation", "검증"],
    "handoff": ["handoff", "핸드오프", "인수인계"],
    "side-effect boundary": ["side-effect", "side effect", "부작용", "라이브", "live service"],
}
CUSTOM_AGENT_REQUIRED_FIELDS = {"name", "description", "developer_instructions"}
TRIGGERISH_DESCRIPTION_RE = re.compile(r"^(Use when|Use for|Use this when|Use this skill when)\b", re.IGNORECASE)
CANONICAL_HARNESS_DIR = Path("src") / "skills" / "harness"
CLAUDE_HARNESS_DIR = Path("claude") / "skills" / "harness"
CODEX_HARNESS_DIR = Path("codex") / "plugin" / "skills" / "harness"
CODEX_HARNESS_OVERLAY_DIR = Path("platform") / "codex" / "skills" / "harness"
CODEX_ALLOWED_EXTRA_FILES = {"agents/openai.yaml"}
CLAUDE_FRONTMATTER_INJECTION = {
    "disable-model-invocation": "true",
    "allowed-tools": "Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion",
}


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
    issues.extend(validate_run_compatible_skill(root, path, text, description, Issue, relpath))
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
        issues.extend(validate_custom_agent_name(root, path, data, Issue, relpath))
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
