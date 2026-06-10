#!/usr/bin/env python3
"""Validate the dryforge-ops skill structure."""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class ValidationError(Exception):
    pass


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValidationError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValidationError("SKILL.md frontmatter is not closed")
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValidationError(f"invalid frontmatter line: {line}")
        data[key.strip()] = value.strip().strip('"')
    return data


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("missing SKILL.md")
    else:
        try:
            data = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            if data.get("name") != skill_dir.name:
                errors.append(f"frontmatter name must match directory name: {skill_dir.name}")
            if not data.get("description") or "TODO" in data.get("description", ""):
                errors.append("frontmatter description must be trigger-focused and non-placeholder")
        except ValidationError as exc:
            errors.append(str(exc))

    required = [
        "scripts/dryforge_ops.py",
        "scripts/validate_dryforge_ops.py",
        "references/dryforge-ops-contract.md",
        "references/task-log-event-schema.md",
        "references/evidence-json-schema.md",
        "references/harness-upgrade-policy.md",
        "references/operations-summary-section.md",
        "references/dryforge-hook-guide.md",
    ]
    for relative in required:
        if not (skill_dir / relative).exists():
            errors.append(f"missing {relative}")

    for script in (skill_dir / "scripts" / "dryforge_ops.py", skill_dir / "scripts" / "validate_dryforge_ops.py"):
        if script.exists():
            try:
                py_compile.compile(str(script), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"py_compile failed for {script.name}: {exc.msg}")
    return errors


def validate_install(repo: Path) -> list[str]:
    errors: list[str] = []
    src_skill = repo / "src" / "skills" / "dryforge-ops"
    src_script = src_skill / "scripts" / "dryforge_ops.py"
    platform_openai = repo / "platform" / "codex" / "skills" / "dryforge-ops" / "agents" / "openai.yaml"
    if not src_skill.exists():
        errors.append("missing canonical src/skills/dryforge-ops")
    else:
        errors.extend(f"src: {error}" for error in validate_skill(src_skill))
    generated = (
        ("codex", repo / "codex" / "plugin" / "skills" / "dryforge-ops", "codex/plugin/skills/dryforge-ops"),
        ("claude", repo / "claude" / "skills" / "dryforge-ops", "claude/skills/dryforge-ops"),
    )
    for label, skill_dir, rel in generated:
        if not skill_dir.exists():
            errors.append(f"missing generated {rel}; run bash build/build.sh")
            continue
        errors.extend(f"{label}: {error}" for error in validate_skill(skill_dir))
        generated_script = skill_dir / "scripts" / "dryforge_ops.py"
        if src_script.exists() and generated_script.exists() and src_script.read_text(encoding="utf-8") != generated_script.read_text(encoding="utf-8"):
            errors.append(f"generated {label} dryforge_ops.py differs from canonical src script")
    if not platform_openai.exists():
        errors.append("missing platform/codex dryforge-ops agents/openai.yaml overlay")
    return errors


def run_cli(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def init_ops(repo: Path) -> None:
    ops = repo / ".agents" / "ops"
    ops.mkdir(parents=True)
    (ops / "operations.md").write_text("# 운영 요약\n", encoding="utf-8")
    (ops / "task-log.jsonl").write_text("", encoding="utf-8")


def init_ready(repo: Path) -> None:
    dry = repo / ".dryforge"
    dry.mkdir(exist_ok=True)
    for name in ("handoff.md", "spec.md", "plan.md"):
        (dry / name).write_text(f"# {name}\n", encoding="utf-8")


def init_archive(repo: Path, evidence: dict | None = None) -> None:
    archive = repo / ".dryforge" / "001"
    archive.mkdir(parents=True)
    (archive / "spec.md").write_text("# spec\n", encoding="utf-8")
    (archive / "plan.md").write_text("# plan\n", encoding="utf-8")
    (archive / "result.md").write_text("# result\n", encoding="utf-8")
    (repo / ".dryforge" / "status.json").write_text(json.dumps({"initialized": True}), encoding="utf-8")
    if evidence is not None:
        (archive / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")


def read_events(repo: Path) -> list[dict]:
    log = repo / ".agents" / "ops" / "task-log.jsonl"
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_benchmark(fixtures_dir: Path) -> list[str]:
    errors: list[str] = []
    if not (fixtures_dir / "benchmark_cases.json").exists():
        errors.append("missing fixtures/benchmark_cases.json")
        return errors
    script = fixtures_dir.parent / "scripts" / "dryforge_ops.py"
    with tempfile.TemporaryDirectory(prefix="dryforge-ops-bench-") as tmp:
        root = Path(tmp)

        repo = root / "false-completed"
        repo.mkdir()
        init_ops(repo)
        init_archive(repo)
        proc = run_cli(script, "after-go", "--date", "2026-06-10", str(repo))
        events = read_events(repo)
        if proc.returncode != 0 or events[-1].get("event") == "completed" or events[-1].get("status") == "completed":
            errors.append("false-completed prevention failed")

        repo = root / "idempotency"
        repo.mkdir()
        init_ops(repo)
        init_archive(repo, {"commands": [{"command": "python -m unittest", "exit_code": 0}]})
        first = run_cli(script, "after-go", "--date", "2026-06-10", str(repo))
        second = run_cli(script, "after-go", "--date", "2026-06-10", str(repo))
        if first.returncode != 0 or second.returncode != 0 or len(read_events(repo)) != 1:
            errors.append("idempotency benchmark failed")
        index = repo / ".agents" / "ops" / "ledger.json"
        evidence = repo / ".agents" / "ops" / "evidence" / "task-2026-06-10-dryforge-go.evidence.json"
        if not index.exists() or not evidence.exists():
            errors.append("ledger/evidence generation benchmark failed")

        repo = root / "corrupt-jsonl"
        repo.mkdir()
        init_ops(repo)
        init_ready(repo)
        (repo / ".agents" / "ops" / "task-log.jsonl").write_text("{bad json\n", encoding="utf-8")
        proc = run_cli(script, "after-ready", str(repo))
        if proc.returncode != 2:
            errors.append("corrupt JSONL protection failed")

        repo = root / "unsafe-path"
        repo.mkdir()
        init_ops(repo)
        proc = run_cli(script, "handoff", "../outside.md", str(repo))
        if proc.returncode == 0:
            errors.append("unsafe path rejection failed")

        repo = root / "workflow"
        repo.mkdir()
        init_ops(repo)
        log = repo / ".agents" / "ops" / "task-log.jsonl"
        events = [
            {"task_id": f"task-qa-{idx}", "event": "completed", "status": "completed", "date": "2026-06-10", "type": "qa", "summary": "테스트"}
            for idx in range(3)
        ]
        log.write_text("".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events), encoding="utf-8")
        suggest = run_cli(script, "workflow", "suggest", str(repo))
        if suggest.returncode != 0 or "workflow_candidate=qa" not in suggest.stdout or "task-qa-0" not in suggest.stdout:
            errors.append("workflow suggest benchmark failed")
        if "delegate_to=harness skill" not in suggest.stdout:
            errors.append("workflow suggest benchmark missing harness delegation signal")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate dryforge-ops skill files.")
    parser.add_argument("skill_dir", nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--install-check", metavar="REPO")
    parser.add_argument("--benchmark", metavar="FIXTURES_DIR")
    args = parser.parse_args(argv)
    if args.install_check:
        errors = validate_install(Path(args.install_check).resolve())
    elif args.benchmark:
        errors = run_benchmark(Path(args.benchmark).resolve())
    else:
        errors = validate_skill(Path(args.skill_dir).resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    target = args.install_check or args.benchmark or args.skill_dir
    print(f"OK: {Path(target).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

