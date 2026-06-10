#!/usr/bin/env python3
"""Dryforge native ops control-plane.

The script does not run or reimplement dryforge. It reads `.dryforge/` as
evidence and writes guarded `.agents/ops` records plus repeatable workflow
artifacts under `.agents/workflows` and `.agents/skills`.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 2

ACTIVE_DOCS = ("handoff.md", "spec.md", "plan.md")
SUMMARY_START = "<!-- dryforge-ops:start -->"
SUMMARY_END = "<!-- dryforge-ops:end -->"
OPS_DIR_REL = Path(".agents") / "ops"
OPS_SUMMARY_REL = OPS_DIR_REL / "operations.md"
TASK_LOG_REL = OPS_DIR_REL / "task-log.jsonl"
LEDGER_REL = OPS_DIR_REL / "ledger.json"
EVIDENCE_DIR_REL = OPS_DIR_REL / "evidence"
DASHBOARD_REL = OPS_DIR_REL / "dashboard.html"
HANDOFF_DIR_REL = OPS_DIR_REL / "handoffs"
WORKFLOWS_DIR_REL = Path(".agents") / "workflows"
SKILLS_DIR_REL = Path(".agents") / "skills"
LEGACY_SUMMARY_RELS = (
    Path("docs") / "operations.md",
    Path("docs") / "operations" / "OPERATIONS_SUMMARY.md",
)
LEGACY_TASK_LOG_RELS = (Path("docs") / "operations" / "task-log.jsonl",)
LEGACY_HARNESS_DIR_REL = Path("docs") / "harness"
SECRET_KEY_RE = re.compile(
    r"(?i)(password|passwd|token|secret|api[_-]?key|authorization|cookie)([\s\"'=:-]+)([^\s\"',;]+)"
)
SENSITIVE_KEY_RE = re.compile(r"(?i)password|passwd|token|secret|api[_-]?key|authorization|cookie")
RUNTIME_RISK_RE = re.compile(
    r"(?i)\b(live|runtime|deploy|deployment|production|migration|database|external|infra)\b|배포|운영|라이브|마이그레이션|데이터베이스"
)
EVIDENCE_SCHEMA_VERSION = "dryforge-ops.evidence.v1"
LEDGER_SCHEMA_VERSION = "dryforge-ops.ledger.v1"
WORKFLOW_ADOPTED_EVENT = "workflow_adopted"
REQUIRED_EVENT_FIELDS = ("task_id", "event", "status", "date", "summary")


class BridgeError(Exception):
    def __init__(self, message: str, exit_code: int = EXIT_BLOCKED):
        super().__init__(message)
        self.exit_code = exit_code


class JsonlError(BridgeError):
    pass


@dataclasses.dataclass
class JsonlParseResult:
    path: str
    state: str
    events: list[dict[str, Any]]
    error: str | None = None


@dataclasses.dataclass
class DryforgeState:
    exists: bool
    active: bool
    active_docs: dict[str, str]
    missing_active_docs: list[str]
    archives: list[str]
    latest_archive: str | None
    status_json: dict[str, Any] | None
    status_error: str | None


@dataclasses.dataclass
class RepoBoundary:
    repo_root: str
    git_available: bool
    branch: str | None
    head: str | None
    status_short: str | None
    worktrees: list[dict[str, str | None]]
    live_state: str = "not_checked"


@dataclasses.dataclass
class RepoOpsState:
    summary: str
    task_log: JsonlParseResult
    ledger: str
    evidence_dir: str
    dashboard: str
    legacy_summaries: list[str]
    legacy_task_logs: list[JsonlParseResult]
    ledger_entries: list[dict[str, Any]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class HarnessState:
    workflows_dir: str
    agents_skills: str
    team_specs: list[str]
    skills: list[str]
    legacy_harness: str
    legacy_team_specs: list[str]


@dataclasses.dataclass
class WriteResult:
    path: str | None = None
    written: bool = False
    skipped: bool = False
    reason: str | None = None


@dataclasses.dataclass
class PreflightResult:
    status: str
    risks: list[dict[str, str]]
    recommended_next_action: str


def today_iso() -> str:
    return _dt.date.today().isoformat()


def normalize_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def is_within(child: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath([normalize_path(child), normalize_path(parent)]) == normalize_path(parent)
    except ValueError:
        return False


def resolve_repo(repo_arg: str | Path) -> Path:
    repo = Path(repo_arg).expanduser().resolve()
    if not repo.exists() or not repo.is_dir():
        raise BridgeError(f"repo path is not a directory: {repo}")
    return repo


def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_inside_repo(repo: Path, target: str | Path) -> Path:
    raw = Path(target).expanduser()
    candidate = raw if raw.is_absolute() else repo / raw
    existing = candidate
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    try:
        resolved_existing = existing.resolve()
    except OSError as exc:
        raise BridgeError(f"cannot resolve path: {existing}: {exc}") from exc
    if not is_within(resolved_existing, repo.resolve()):
        raise BridgeError(f"unsafe path escapes repo root: {candidate}")
    if candidate.exists():
        try:
            resolved_candidate = candidate.resolve()
        except OSError as exc:
            raise BridgeError(f"cannot resolve path: {candidate}: {exc}") from exc
        if not is_within(resolved_candidate, repo.resolve()):
            raise BridgeError(f"unsafe path escapes repo root: {candidate}")
    return candidate


def ensure_parent_for_write(repo: Path, target: str | Path) -> Path:
    candidate = resolve_inside_repo(repo, target)
    parent = candidate.parent
    if parent.exists() and not is_within(parent.resolve(), repo.resolve()):
        raise BridgeError(f"unsafe write parent escapes repo root: {parent}")
    return candidate


def redact_string(value: str) -> str:
    return SECRET_KEY_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", value)


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        redacted: dict[str, Any] = {}
        for key, value in obj.items():
            redacted[key] = "[REDACTED]" if SENSITIVE_KEY_RE.search(str(key)) else redact(value)
        return redacted
    if isinstance(obj, list):
        return [redact(item) for item in obj]
    if isinstance(obj, str):
        return redact_string(obj)
    return obj


def run_git(repo: Path, args: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def parse_worktrees(porcelain: str | None) -> list[dict[str, str | None]]:
    if not porcelain:
        return []
    worktrees: list[dict[str, str | None]] = []
    current: dict[str, str | None] = {}
    for line in porcelain.splitlines():
        if not line.strip():
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            if current:
                worktrees.append(current)
            current = {"path": value, "head": None, "branch": None}
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value.replace("refs/heads/", "")
    if current:
        worktrees.append(current)
    return worktrees


def collect_repo_boundary(repo: Path) -> RepoBoundary:
    top = run_git(repo, ["rev-parse", "--show-toplevel"])
    return RepoBoundary(
        repo_root=top or str(repo),
        git_available=bool(top),
        branch=run_git(repo, ["branch", "--show-current"]) or None,
        head=run_git(repo, ["rev-parse", "HEAD"]) or None,
        status_short=redact_string(run_git(repo, ["status", "--short"]) or ""),
        worktrees=parse_worktrees(run_git(repo, ["worktree", "list", "--porcelain"])),
    )


def detect_dryforge(repo: Path) -> DryforgeState:
    dryforge = repo / ".dryforge"
    if not dryforge.exists():
        return DryforgeState(False, False, {}, list(ACTIVE_DOCS), [], None, None, None)
    resolve_inside_repo(repo, dryforge)
    if not dryforge.is_dir():
        raise BridgeError(".dryforge exists but is not a directory")

    active_docs: dict[str, str] = {}
    missing: list[str] = []
    for name in ACTIVE_DOCS:
        path = dryforge / name
        if path.exists() and path.is_file():
            resolve_inside_repo(repo, path)
            active_docs[name[:-3]] = rel(repo, path)
        else:
            missing.append(name)

    archive_paths: list[Path] = []
    for child in dryforge.iterdir():
        if child.name.isdigit() and child.is_dir():
            resolve_inside_repo(repo, child)
            archive_paths.append(child)
    archive_paths.sort(key=lambda p: int(p.name))

    status_json: dict[str, Any] | None = None
    status_error: str | None = None
    status_path = dryforge / "status.json"
    if status_path.exists():
        resolve_inside_repo(repo, status_path)
        try:
            parsed = json.loads(status_path.read_text(encoding="utf-8"))
            status_json = redact(parsed) if isinstance(parsed, dict) else None
            if status_json is None:
                status_error = "status.json is not an object"
        except json.JSONDecodeError as exc:
            status_error = f"status.json parse error: line {exc.lineno}: {exc.msg}"

    return DryforgeState(
        exists=True,
        active=len(missing) == 0,
        active_docs=active_docs,
        missing_active_docs=missing,
        archives=[rel(repo, p) for p in archive_paths],
        latest_archive=rel(repo, archive_paths[-1]) if archive_paths else None,
        status_json=status_json,
        status_error=status_error,
    )


def parse_jsonl_path(repo: Path, path: Path) -> JsonlParseResult:
    if not path.exists():
        return JsonlParseResult(rel(repo, path), "missing", [])
    resolve_inside_repo(repo, path)
    events: list[dict[str, Any]] = []
    try:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JsonlError(f"JSONL corruption at {rel(repo, path)} line {lineno}: {exc.msg}") from exc
            if not isinstance(item, dict):
                raise JsonlError(f"JSONL corruption at {rel(repo, path)} line {lineno}: expected object")
            events.append(item)
    except UnicodeDecodeError as exc:
        raise JsonlError(f"JSONL decode error at {rel(repo, path)}: {exc}") from exc
    return JsonlParseResult(rel(repo, path), "valid", events)


def parse_task_log(repo: Path) -> JsonlParseResult:
    return parse_jsonl_path(repo, repo / TASK_LOG_REL)


def parse_legacy_task_logs(repo: Path) -> list[JsonlParseResult]:
    results: list[JsonlParseResult] = []
    for legacy_rel in LEGACY_TASK_LOG_RELS:
        path = repo / legacy_rel
        if not path.exists():
            continue
        try:
            results.append(parse_jsonl_path(repo, path))
        except BridgeError as exc:
            results.append(JsonlParseResult(rel(repo, path), "unreadable", [], str(exc)))
    return results


def detect_repo_ops(repo: Path) -> RepoOpsState:
    summary_path = repo / OPS_SUMMARY_REL
    dashboard_path = repo / DASHBOARD_REL
    ledger_path = repo / LEDGER_REL
    evidence_dir = repo / EVIDENCE_DIR_REL
    legacy_summaries: list[str] = []
    for legacy_rel in LEGACY_SUMMARY_RELS:
        path = repo / legacy_rel
        if path.exists():
            try:
                resolve_inside_repo(repo, path)
                legacy_summaries.append(rel(repo, path))
            except BridgeError:
                legacy_summaries.append(f"unreadable:{legacy_rel.as_posix()}")
    ledger_entries: list[dict[str, Any]] = []
    if ledger_path.exists():
        try:
            ledger_entries = [e for e in parse_ledger(repo).get("entries", []) if isinstance(e, dict)]
        except BridgeError:
            ledger_entries = []
    return RepoOpsState(
        summary="present" if summary_path.exists() else "missing",
        task_log=parse_task_log(repo),
        ledger="present" if ledger_path.exists() else "missing",
        evidence_dir="present" if evidence_dir.exists() else "missing",
        dashboard="present" if dashboard_path.exists() else "missing",
        legacy_summaries=legacy_summaries,
        legacy_task_logs=parse_legacy_task_logs(repo),
        ledger_entries=ledger_entries,
    )


def detect_harness(repo: Path) -> HarnessState:
    workflows_dir = repo / WORKFLOWS_DIR_REL
    agents_skills = repo / SKILLS_DIR_REL
    legacy_harness = repo / LEGACY_HARNESS_DIR_REL
    team_specs = [rel(repo, p) for p in workflows_dir.glob("*/team-spec.md")] if workflows_dir.exists() else []
    skills = [rel(repo, p.parent) for p in agents_skills.glob("*/SKILL.md")] if agents_skills.exists() else []
    legacy_team_specs = [rel(repo, p) for p in legacy_harness.glob("*/team-spec.md")] if legacy_harness.exists() else []
    return HarnessState(
        workflows_dir="present" if workflows_dir.exists() else "missing",
        agents_skills="present" if agents_skills.exists() else "missing",
        team_specs=sorted(team_specs),
        skills=sorted(skills),
        legacy_harness="present" if legacy_harness.exists() else "missing",
        legacy_team_specs=sorted(legacy_team_specs),
    )


def combined_task_events(repo_ops: RepoOpsState) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for legacy in repo_ops.legacy_task_logs:
        if legacy.state == "valid":
            events.extend(legacy.events)
    events.extend(repo_ops.task_log.events)
    return events


def active_docs_hash(repo: Path, dryforge: DryforgeState) -> str:
    if not dryforge.active:
        return "missing"
    h = hashlib.sha256()
    for key in sorted(dryforge.active_docs):
        path = repo / dryforge.active_docs[key]
        resolve_inside_repo(repo, path)
        h.update(key.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:16]


def default_task_id(date: str, suffix: str) -> str:
    return f"task-{date}-{suffix}"


def dryforge_public_state(dryforge: DryforgeState) -> dict[str, Any]:
    return {
        "exists": dryforge.exists,
        "active": dryforge.active,
        "active_docs": dryforge.active_docs,
        "missing_active_docs": dryforge.missing_active_docs,
        "archives": dryforge.archives,
        "latest_archive": dryforge.latest_archive,
        "status_initialized": bool(dryforge.status_json and dryforge.status_json.get("initialized")),
        "status_error": dryforge.status_error,
    }


def event_idempotency_exists(events: Iterable[dict[str, Any]], key: str) -> bool:
    return any(event.get("idempotency_key") == key for event in events)


def append_event(repo: Path, event: dict[str, Any], *, dry_run: bool) -> WriteResult:
    log_path = ensure_parent_for_write(repo, repo / TASK_LOG_REL)
    parsed = parse_task_log(repo)
    key = event.get("idempotency_key")
    if key and event_idempotency_exists(parsed.events, key):
        return WriteResult(path=rel(repo, log_path), skipped=True, reason="duplicate idempotency_key")
    if dry_run:
        return WriteResult(path=rel(repo, log_path), skipped=True, reason="dry-run")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(redact(event), ensure_ascii=False, sort_keys=True) + "\n")
    return WriteResult(path=rel(repo, log_path), written=True)


def write_new_text(repo: Path, target: str | Path, content: str, *, dry_run: bool) -> WriteResult:
    path = ensure_parent_for_write(repo, target)
    if path.exists():
        return WriteResult(path=rel(repo, path), skipped=True, reason="already exists")
    if dry_run:
        return WriteResult(path=rel(repo, path), skipped=True, reason="dry-run")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return WriteResult(path=rel(repo, path), written=True)


def build_summary_block(dryforge: DryforgeState, recent_verification: str, workflow_candidate: str = "not_checked") -> str:
    active_state = "ready" if dryforge.active else ("missing" if not dryforge.exists else "incomplete")
    marker = "initialized" if dryforge.status_json and dryforge.status_json.get("initialized") else "missing"
    if dryforge.status_error:
        marker = dryforge.status_error
    lines = [
        SUMMARY_START,
        "## Dryforge 실행 상태",
        "",
        "| 항목 | 현재 상태 | 다음 액션 |",
        "| --- | --- | --- |",
        f"| Active 3문서 | `{redact_string(active_state)}` | active면 dryforge go 전후 control-plane 동기화 |",
        f"| 최신 archive | `{redact_string(dryforge.latest_archive or 'missing')}` | after-go evidence 연결 확인 |",
        f"| status marker | `{redact_string(marker)}` | initialized 여부 확인 |",
        f"| 최근 검증 | `{redact_string(recent_verification)}` | 실패 또는 누락이면 재검증 |",
        f"| 반복 workflow 후보 | `{redact_string(workflow_candidate)}` | workflow 승격 검토 |",
        SUMMARY_END,
        "",
    ]
    return "\n".join(lines)


def update_operations_summary(repo: Path, dryforge: DryforgeState, recent_verification: str, *, dry_run: bool) -> WriteResult:
    summary_path = ensure_parent_for_write(repo, repo / OPS_SUMMARY_REL)
    if summary_path.exists():
        text = summary_path.read_text(encoding="utf-8")
    else:
        text = "# Dryforge Ops Control Plane\n\n이 문서는 에이전트 운영 기록용입니다. 프로젝트 운영 문서는 docs/operations.md가 있으면 별도로 유지합니다.\n"
    block = build_summary_block(dryforge, recent_verification)
    if SUMMARY_START in text and SUMMARY_END in text:
        pattern = re.compile(re.escape(SUMMARY_START) + r".*?" + re.escape(SUMMARY_END) + r"\n?", re.S)
        new_text = pattern.sub(block, text, count=1)
    elif "## Dryforge 실행 상태" in text:
        pattern = re.compile(r"(?:\n?## Dryforge 실행 상태\n.*?)(?=\n##\s|\Z)", re.S)
        new_text = pattern.sub("\n" + block.rstrip() + "\n", text, count=1)
    else:
        sep = "" if text.endswith("\n") else "\n"
        new_text = text + sep + "\n" + block
    if new_text == text:
        return WriteResult(path=rel(repo, summary_path), skipped=True, reason="unchanged")
    if dry_run:
        return WriteResult(path=rel(repo, summary_path), skipped=True, reason="dry-run")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(new_text, encoding="utf-8", newline="\n")
    return WriteResult(path=rel(repo, summary_path), written=True)


def coerce_exit_code(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value.strip())
    return None


def parse_command_line(line: str, source: str) -> dict[str, Any] | None:
    cleaned = line.strip().lstrip("-*").strip().strip("`")
    m = re.search(r"(?P<command>.+?)(?:[:;,\-]\s*)?exit(?:_code)?\s*[:= ]\s*(?P<code>-?\d+)", cleaned, re.I)
    if not m:
        return None
    command = m.group("command").strip().strip("`:- ")
    if not command:
        return None
    return {"command": redact_string(command), "exit_code": int(m.group("code")), "source": source}


def normalize_command(item: Any, source: str) -> dict[str, Any] | None:
    if isinstance(item, dict):
        command = item.get("command") or item.get("cmd") or item.get("name")
        exit_code = coerce_exit_code(item.get("exit_code", item.get("exit", item.get("code"))))
        if command is not None and exit_code is not None:
            return {"command": redact_string(str(command)), "exit_code": exit_code, "source": item.get("source") or source}
    if isinstance(item, str):
        return parse_command_line(item, source)
    return None


def merge_evidence_from_json(data: Any, source: str, commands: list[dict[str, Any]], manual: list[str]) -> None:
    if not isinstance(data, dict):
        return
    candidates: list[Any] = []
    for key in ("commands", "command_evidence"):
        if isinstance(data.get(key), list):
            candidates.extend(data[key])
    evidence = data.get("evidence")
    if isinstance(evidence, dict):
        for key in ("commands", "command_evidence"):
            if isinstance(evidence.get(key), list):
                candidates.extend(evidence[key])
        if isinstance(evidence.get("manual_evidence"), list):
            manual.extend(redact_string(str(item)) for item in evidence["manual_evidence"] if str(item).strip())
    if isinstance(data.get("validation"), list):
        candidates.extend(data["validation"])
    if isinstance(data.get("manual_evidence"), list):
        manual.extend(redact_string(str(item)) for item in data["manual_evidence"] if str(item).strip())
    for item in candidates:
        command = normalize_command(item, source)
        if command:
            commands.append(command)


def collect_evidence(repo: Path, dryforge: DryforgeState) -> dict[str, Any]:
    commands: list[dict[str, Any]] = []
    manual: list[str] = []
    sources: list[str] = []
    parse_errors: list[str] = []
    candidate_files: list[Path] = []
    if dryforge.latest_archive:
        archive = repo / dryforge.latest_archive
        candidate_files.extend(archive / name for name in (
            "evidence.json", "verification.json", "validation.json", "result.json", "result.md", "handoff.md"
        ))
    candidate_files.extend(repo / ".dryforge" / name for name in ("evidence.json", "verification.json", "validation.json"))
    for path in candidate_files:
        if not path.exists() or not path.is_file():
            continue
        resolve_inside_repo(repo, path)
        source = rel(repo, path)
        sources.append(source)
        if path.suffix.lower() == ".json":
            try:
                merge_evidence_from_json(json.loads(path.read_text(encoding="utf-8")), source, commands, manual)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                parse_errors.append(f"{source} 파싱 실패: {exc}")
        else:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                parsed = parse_command_line(line, source)
                if parsed:
                    commands.append(parsed)
    if dryforge.status_json:
        merge_evidence_from_json(dryforge.status_json, ".dryforge/status.json", commands, manual)
    seen: set[tuple[str, int, str]] = set()
    unique_commands: list[dict[str, Any]] = []
    for command in commands:
        key = (str(command.get("command")), int(command.get("exit_code", 999999)), str(command.get("source")))
        if key not in seen:
            seen.add(key)
            unique_commands.append(command)
    return redact({"commands": unique_commands, "manual_evidence": manual, "sources": sorted(set(sources)), "parse_errors": parse_errors})


def decide_after_go(dryforge: DryforgeState, evidence: dict[str, Any]) -> tuple[str, str, str]:
    commands = evidence.get("commands") or []
    manual = evidence.get("manual_evidence") or []
    parse_errors = evidence.get("parse_errors") or []
    if not dryforge.latest_archive:
        return "blocked", "blocked", "dryforge archive가 없어 go 결과를 확인할 수 없습니다."
    if dryforge.active:
        return "needs_review", "pending", "active 3문서가 남아 있어 archive 완료 여부 검토가 필요합니다."
    if parse_errors:
        return "needs_review", "pending", "검증 증거 파싱 오류가 있어 완료로 기록하지 않았습니다."
    if commands:
        failed = [cmd for cmd in commands if cmd.get("exit_code") != 0]
        if failed:
            return "validated", "blocked", "검증 명령 실패가 있어 완료로 기록하지 않았습니다."
        return "completed", "completed", "검증 명령이 exit 0으로 완료되어 dryforge 결과를 완료 기록으로 동기화했습니다."
    if manual:
        return "completed", "completed", "명시적 수동 검증 증거가 있어 dryforge 결과를 완료 기록으로 동기화했습니다."
    return "needs_review", "pending", "검증 증거가 없어 완료로 기록하지 않았습니다."


def recent_verification_label(evidence: dict[str, Any]) -> str:
    commands = evidence.get("commands") or []
    if commands:
        first = commands[0]
        return f"{first.get('command')} exit {first.get('exit_code')}"
    if evidence.get("manual_evidence"):
        return "manual evidence"
    return "missing"


def write_evidence_json(repo: Path, task_id: str, evidence: dict[str, Any], *, dry_run: bool) -> WriteResult:
    target = repo / EVIDENCE_DIR_REL / f"{task_id}.evidence.json"
    content = json.dumps(redact(evidence), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return write_new_text(repo, target, content, dry_run=dry_run)


def normalize_evidence_record(
    *,
    repo: Path,
    dryforge: DryforgeState,
    boundary: RepoBoundary,
    task_id: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    commands = evidence.get("commands") or []
    manual = evidence.get("manual_evidence") or []
    blockers: list[str] = []
    if not dryforge.latest_archive:
        blockers.append("missing_archive")
    if dryforge.active:
        blockers.append("active_docs_still_present")
    if not commands and not manual:
        blockers.append("missing_verification_evidence")
    if evidence.get("parse_errors"):
        blockers.append("evidence_parse_error")
    failed = [cmd for cmd in commands if cmd.get("exit_code") != 0]
    if failed:
        blockers.append("failed_command_evidence")
    completion_allowed = bool(dryforge.latest_archive and not dryforge.active and not failed and not evidence.get("parse_errors") and (commands or manual))
    return redact(
        {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "task_id": task_id,
            "normalized_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat(),
            "repo": {"root": str(repo), "branch": boundary.branch, "head": boundary.head},
            "dryforge": dryforge_public_state(dryforge),
            "commands": commands,
            "manual_evidence": manual,
            "sources": evidence.get("sources") or [],
            "parse_errors": evidence.get("parse_errors") or [],
            "completion_allowed": completion_allowed,
            "blockers": blockers,
            "links": {
                "task_log": TASK_LOG_REL.as_posix(),
                "ledger": LEDGER_REL.as_posix(),
                "evidence_json": (EVIDENCE_DIR_REL / f"{task_id}.evidence.json").as_posix(),
            },
        }
    )


def parse_ledger(repo: Path) -> dict[str, Any]:
    path = repo / LEDGER_REL
    if not path.exists():
        return {"schema_version": LEDGER_SCHEMA_VERSION, "entries": []}
    resolve_inside_repo(repo, path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BridgeError(f"dryforge ledger is corrupt: {rel(repo, path)} line {exc.lineno}: {exc.msg}")
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise BridgeError(f"dryforge ledger has invalid shape: {rel(repo, path)}")
    data.setdefault("schema_version", LEDGER_SCHEMA_VERSION)
    return data


def update_ledger_index(repo: Path, entry: dict[str, Any], *, dry_run: bool) -> WriteResult:
    path = ensure_parent_for_write(repo, repo / LEDGER_REL)
    ledger = parse_ledger(repo)
    entries = ledger.setdefault("entries", [])
    key = entry["idempotency_key"]
    replaced = False
    for index, existing in enumerate(entries):
        if isinstance(existing, dict) and existing.get("idempotency_key") == key:
            entries[index] = entry
            replaced = True
            break
    if not replaced:
        entries.append(entry)
    ledger["schema_version"] = LEDGER_SCHEMA_VERSION
    ledger["updated_at"] = _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat()
    if dry_run:
        return WriteResult(path=rel(repo, path), skipped=True, reason="dry-run")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(ledger), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return WriteResult(path=rel(repo, path), written=True, reason="updated" if replaced else "created")


def open_ledger_entries(repo_ops: RepoOpsState) -> list[dict[str, Any]]:
    return [e for e in repo_ops.ledger_entries if not e.get("completion_allowed", True) or e.get("blockers")]


def recommend_next(dryforge: DryforgeState, repo_ops: RepoOpsState) -> str:
    open_entries = open_ledger_entries(repo_ops)
    if open_entries:
        latest = open_entries[-1]
        task = latest.get("task_id") or latest.get("archive") or "the last recorded cycle"
        reason = ", ".join(str(b) for b in latest.get("blockers") or []) or "completion not allowed"
        return f"resolve the open operations entry for {task} ({reason}) before the next dryforge cycle"
    if dryforge.active:
        return "run after-ready, then dryforge go"
    if dryforge.latest_archive:
        return "run after-go to sync latest archive"
    return "run dryforge ready before syncing"


def build_assessment(repo: Path) -> dict[str, Any]:
    dryforge = detect_dryforge(repo)
    repo_ops = detect_repo_ops(repo)
    return {
        "repo": str(repo),
        "dryforge": dryforge_public_state(dryforge),
        "repo_ops": dataclasses.asdict(repo_ops),
        "repo_boundary": dataclasses.asdict(collect_repo_boundary(repo)),
        "harness": dataclasses.asdict(detect_harness(repo)),
        "recommendation": recommend_next(dryforge, repo_ops),
    }


def require_summary(repo: Path) -> None:
    ensure_parent_for_write(repo, repo / OPS_SUMMARY_REL)
    ensure_parent_for_write(repo, repo / TASK_LOG_REL)


def detect_preflight(repo: Path) -> PreflightResult:
    risks: list[dict[str, str]] = []
    try:
        repo_ops = detect_repo_ops(repo)
    except JsonlError as exc:
        return PreflightResult(
            status="blocked",
            risks=[{"severity": "blocked", "kind": "corrupt_jsonl", "detail": str(exc)}],
            recommended_next_action=f"repair {TASK_LOG_REL.as_posix()} before dryforge go",
        )
    boundary = collect_repo_boundary(repo)
    if repo_ops.summary == "missing":
        risks.append({"severity": "warn", "kind": "missing_ops_summary", "detail": f"{OPS_SUMMARY_REL.as_posix()} is missing"})
    if repo_ops.task_log.state == "missing":
        risks.append({"severity": "warn", "kind": "missing_task_log", "detail": f"{TASK_LOG_REL.as_posix()} is missing"})
    for legacy in repo_ops.legacy_task_logs:
        if legacy.state not in ("valid", "missing"):
            risks.append({"severity": "warn", "kind": "legacy_task_log_unreadable", "detail": legacy.error or legacy.path})
    events = combined_task_events(repo_ops)
    if events:
        latest = events[-1]
        if latest.get("status") == "blocked" or latest.get("event") == "blocked":
            risks.append({"severity": "blocked", "kind": "repo_ops_blocked", "detail": f"latest task-log event is blocked: {latest.get('task_id', 'unknown')}"})
        elif any(event.get("status") == "blocked" or event.get("event") == "blocked" for event in events[-10:]):
            risks.append({"severity": "warn", "kind": "recent_blocked_event", "detail": "recent task-log events include blocked work"})
    risk_text = ""
    for summary_rel in (OPS_SUMMARY_REL, *LEGACY_SUMMARY_RELS):
        summary_path = repo / summary_rel
        if summary_path.exists():
            resolve_inside_repo(repo, summary_path)
            risk_text += summary_path.read_text(encoding="utf-8", errors="replace")[:12000]
    risk_text += "\n".join(json.dumps(event, ensure_ascii=False) for event in events[-10:])
    if RUNTIME_RISK_RE.search(risk_text):
        risks.append({"severity": "warn", "kind": "live_runtime_risk", "detail": "operations evidence mentions live/runtime/deploy/migration risk"})
    dirty = boundary.status_short or ""
    if RUNTIME_RISK_RE.search(dirty):
        risks.append({"severity": "warn", "kind": "dirty_runtime_surface", "detail": "git status includes runtime-sensitive paths"})

    if any(risk["severity"] == "blocked" for risk in risks):
        status = "blocked"
        action = "resolve blocked operations state before dryforge go"
    elif risks:
        status = "warn"
        action = "review warnings before dryforge go; continue only if risks are accepted"
    else:
        status = "ok"
        action = "ready for dryforge go"
    return PreflightResult(status=status, risks=risks, recommended_next_action=action)


def run_doctor(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    assessment_code, assessment = run_assess(repo, args)
    preflight = detect_preflight(repo)
    dryforge = detect_dryforge(repo)
    checks: list[dict[str, str]] = []
    if dryforge.exists:
        checks.append({"name": "dryforge_state", "status": "ok", "detail": "dryforge directory detected"})
    else:
        checks.append({"name": "dryforge_state", "status": "warn", "detail": ".dryforge directory is missing"})
    repo_ops = assessment.get("repo_ops", {})
    task_log_state = repo_ops.get("task_log", {}).get("state")
    checks.append({"name": "task_log", "status": "ok" if task_log_state in ("valid", "missing") else "blocked", "detail": str(task_log_state)})
    checks.append({"name": "preflight", "status": preflight.status, "detail": preflight.recommended_next_action})
    if assessment_code == EXIT_BLOCKED or preflight.status == "blocked" or any(check["status"] == "blocked" for check in checks):
        health = "blocked"
    elif preflight.status == "warn" or any(check["status"] == "warn" for check in checks):
        health = "warn"
    else:
        health = "ok"
    recommended = preflight.recommended_next_action if health != "ok" else assessment.get("recommendation", "run dryforge-ops after-ready/after-go as appropriate")
    return EXIT_OK if health != "blocked" else EXIT_BLOCKED, {
        "mode": "doctor",
        "health": health,
        "checks": checks,
        "preflight": dataclasses.asdict(preflight),
        "assessment": assessment,
        "recommended_next_action": recommended,
    }


def run_preflight(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    result = detect_preflight(repo)
    return EXIT_BLOCKED if result.status == "blocked" and args.strict else EXIT_OK, {"mode": "preflight", **dataclasses.asdict(result)}


def run_before_go(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    dryforge = detect_dryforge(repo)
    if not dryforge.active:
        raise BridgeError(f"active dryforge docs are missing: {', '.join(dryforge.missing_active_docs)}")
    require_summary(repo)
    preflight = detect_preflight(repo)
    if preflight.status == "blocked":
        return EXIT_BLOCKED, {"mode": "before-go", "preflight": dataclasses.asdict(preflight), "write": dataclasses.asdict(WriteResult(skipped=True, reason="preflight blocked"))}
    boundary = collect_repo_boundary(repo)
    parsed = parse_task_log(repo)
    date = args.date or today_iso()
    task_id = args.task_id or default_task_id(date, "dryforge-before-go")
    docs_hash = active_docs_hash(repo, dryforge)
    idempotency_key = f"dryforge-ops:before-go:{docs_hash}:{boundary.head or 'no-git-head'}"
    event = {
        "task_id": task_id,
        "event": "preflight",
        "status": "open" if preflight.status == "ok" else "pending_review",
        "date": date,
        "type": "ops",
        "summary": "dryforge go 실행 전 control-plane preflight를 기록했습니다.",
        "files": list(dryforge.active_docs.values()),
        "validation": [f"preflight: {preflight.status}"],
        "result": preflight.recommended_next_action,
        "next": ["dryforge go 실행 후 after-go로 evidence, ledger, task-log를 동기화합니다."],
        "repo_state": {"branch": boundary.branch, "head": boundary.head},
        "dryforge": dryforge_public_state(dryforge),
        "preflight": dataclasses.asdict(preflight),
        "links": {"task_log": TASK_LOG_REL.as_posix(), "ledger": LEDGER_REL.as_posix()},
        "idempotency_key": idempotency_key,
    }
    append_result = WriteResult(path=parsed.path, skipped=True, reason="duplicate idempotency_key") if event_idempotency_exists(parsed.events, idempotency_key) else append_event(repo, event, dry_run=args.dry_run)
    summary_result = update_operations_summary(repo, dryforge, f"before-go preflight {preflight.status}", dry_run=args.dry_run)
    return EXIT_OK, {"mode": "before-go", "event": event, "append": dataclasses.asdict(append_result), "summary": dataclasses.asdict(summary_result), "dry_run": args.dry_run}


def run_assess(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    try:
        return EXIT_OK, build_assessment(repo)
    except JsonlError as exc:
        return EXIT_BLOCKED, {
            "repo": str(repo),
            "dryforge": dryforge_public_state(detect_dryforge(repo)),
            "repo_ops": {"task_log": {"path": TASK_LOG_REL.as_posix(), "state": "corrupt", "error": str(exc)}},
            "repo_boundary": dataclasses.asdict(collect_repo_boundary(repo)),
            "recommendation": f"repair {TASK_LOG_REL.as_posix()} before writing",
        }


def run_after_ready(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    dryforge = detect_dryforge(repo)
    if not dryforge.active:
        raise BridgeError(f"active dryforge docs are missing: {', '.join(dryforge.missing_active_docs)}")
    require_summary(repo)
    parsed = parse_task_log(repo)
    boundary = collect_repo_boundary(repo)
    date = args.date or today_iso()
    task_id = args.task_id or default_task_id(date, "dryforge-ready")
    docs_hash = active_docs_hash(repo, dryforge)
    idempotency_key = f"dryforge-ops:after-ready:{docs_hash}:{boundary.head or 'no-git-head'}"
    event = {
        "task_id": task_id,
        "event": "planned",
        "status": "open",
        "date": date,
        "type": "code",
        "summary": "dryforge ready 3문서를 control-plane planned 이벤트로 동기화했습니다.",
        "files": list(dryforge.active_docs.values()),
        "validation": [],
        "result": "dryforge active 3문서가 준비되어 후속 dryforge go 실행 대기 상태입니다.",
        "next": ["dryforge go 실행 후 after-go로 검증 증거를 동기화합니다."],
        "repo_state": {"branch": boundary.branch, "head": boundary.head},
        "worktree_state": {"worktrees": boundary.worktrees},
        "live_state": {"status": boundary.live_state},
        "dryforge": dryforge_public_state(dryforge),
        "evidence": {"active_docs_hash": docs_hash},
        "links": {"task_log": TASK_LOG_REL.as_posix(), "ledger": LEDGER_REL.as_posix()},
        "idempotency_key": idempotency_key,
    }
    append_result = WriteResult(path=parsed.path, skipped=True, reason="duplicate idempotency_key") if event_idempotency_exists(parsed.events, idempotency_key) else append_event(repo, event, dry_run=args.dry_run)
    summary_result = update_operations_summary(repo, dryforge, "ready docs present", dry_run=args.dry_run)
    return EXIT_OK, {"mode": "after-ready", "event": event, "append": dataclasses.asdict(append_result), "summary": dataclasses.asdict(summary_result), "dry_run": args.dry_run}


def run_after_go(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    dryforge = detect_dryforge(repo)
    require_summary(repo)
    parsed = parse_task_log(repo)
    boundary = collect_repo_boundary(repo)
    date = args.date or today_iso()
    task_id = args.task_id or default_task_id(date, "dryforge-go")
    archive_key = dryforge.latest_archive or "no-archive"
    idempotency_key = f"dryforge-ops:after-go:{archive_key}:{boundary.head or 'no-git-head'}"
    evidence = collect_evidence(repo, dryforge)
    normalized_evidence = normalize_evidence_record(repo=repo, dryforge=dryforge, boundary=boundary, task_id=task_id, evidence=evidence)
    event_name, status, result = decide_after_go(dryforge, evidence)
    if (event_name, status) == ("completed", "completed") and not normalized_evidence["completion_allowed"]:
        raise BridgeError("completed event refused because normalized evidence does not allow completion")
    validation = [f"{cmd.get('command')}: exit {cmd.get('exit_code')}" for cmd in evidence.get("commands", [])]
    if not validation and status != "completed":
        validation = ["검증 증거가 확인되지 않았습니다."]
    evidence_path = (EVIDENCE_DIR_REL / f"{task_id}.evidence.json").as_posix()
    links = {"task_log": TASK_LOG_REL.as_posix(), "ledger": LEDGER_REL.as_posix(), "evidence_json": evidence_path if dryforge.latest_archive else None}
    event = {
        "task_id": task_id,
        "event": event_name,
        "status": status,
        "date": date,
        "type": "code",
        "summary": "dryforge go/archive 결과를 control-plane 이벤트로 동기화했습니다.",
        "files": [archive_key] if dryforge.latest_archive else [],
        "validation": validation,
        "result": result,
        "next": ["필요하면 dashboard 또는 handoff로 운영 산출물을 갱신합니다."],
        "repo_state": {"branch": boundary.branch, "head": boundary.head},
        "worktree_state": {"worktrees": boundary.worktrees},
        "live_state": {"status": boundary.live_state},
        "dryforge": dryforge_public_state(dryforge),
        "evidence": normalized_evidence,
        "links": links,
        "idempotency_key": idempotency_key,
    }
    ledger_entry = {
        "idempotency_key": idempotency_key,
        "task_id": task_id,
        "event": event_name,
        "status": status,
        "date": date,
        "archive": dryforge.latest_archive,
        "git_head": boundary.head,
        "task_log": TASK_LOG_REL.as_posix(),
        "evidence_json": evidence_path if dryforge.latest_archive else None,
        "handoff": None,
        "completion_allowed": normalized_evidence["completion_allowed"],
        "blockers": normalized_evidence["blockers"],
        "summary": event["summary"],
    }
    duplicate = event_idempotency_exists(parsed.events, idempotency_key)
    if duplicate:
        append_result = WriteResult(path=parsed.path, skipped=True, reason="duplicate idempotency_key")
        evidence_abs = repo / evidence_path
        if dryforge.latest_archive and not evidence_abs.exists():
            evidence_result = write_evidence_json(repo, task_id, normalized_evidence, dry_run=args.dry_run)
        else:
            evidence_result = WriteResult(path=rel(repo, evidence_abs) if dryforge.latest_archive else None, skipped=True, reason="duplicate idempotency_key")
    else:
        evidence_result = write_evidence_json(repo, task_id, normalized_evidence, dry_run=args.dry_run) if dryforge.latest_archive else WriteResult(path=None, skipped=True, reason="missing archive")
        append_result = append_event(repo, event, dry_run=args.dry_run)
    ledger_result = update_ledger_index(repo, ledger_entry, dry_run=args.dry_run) if dryforge.latest_archive else WriteResult(path=None, skipped=True, reason="missing archive")
    summary_result = update_operations_summary(repo, dryforge, recent_verification_label(evidence), dry_run=args.dry_run)
    exit_code = EXIT_BLOCKED if args.strict and status != "completed" else EXIT_OK
    return exit_code, {
        "mode": "after-go",
        "event": event,
        "append": dataclasses.asdict(append_result),
        "evidence_file": dataclasses.asdict(evidence_result),
        "ledger": dataclasses.asdict(ledger_result),
        "summary": dataclasses.asdict(summary_result),
        "dry_run": args.dry_run,
    }


def load_event_payload(raw: str, source: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BridgeError(f"event JSON is invalid: {source} line {exc.lineno}: {exc.msg}")
    if not isinstance(data, dict):
        raise BridgeError(f"event JSON must be a single object: {source}")
    return data


def run_ops_log(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    ops_dir = repo / OPS_DIR_REL
    if not ops_dir.is_dir():
        raise BridgeError(
            f"{OPS_DIR_REL.as_posix()} is missing: log only appends into an existing ops plane; run assess and after-ready first"
        )
    if args.event == "-":
        event = load_event_payload(sys.stdin.read(), "stdin")
    else:
        event_path = Path(args.event)
        if not event_path.is_file():
            raise BridgeError(f"event file not found: {args.event}")
        event = load_event_payload(event_path.read_text(encoding="utf-8"), args.event)
    event.setdefault("date", args.date or today_iso())
    event.setdefault("task_id", args.task_id or default_task_id(str(event["date"]), "ops-log"))
    if args.idempotency_key:
        event["idempotency_key"] = args.idempotency_key
    missing = [field for field in REQUIRED_EVENT_FIELDS if not str(event.get(field) or "").strip()]
    if missing:
        raise BridgeError(f"event is missing required fields: {', '.join(missing)}")
    commands: list[dict[str, Any]] = []
    manual: list[str] = []
    merge_evidence_from_json(event, "ops-log-event", commands, manual)
    failed = [cmd for cmd in commands if cmd.get("exit_code") != 0]
    if (str(event.get("event")), str(event.get("status"))) == ("completed", "completed") and (failed or not (commands or manual)):
        raise BridgeError(
            "completed/completed refused: the event needs command evidence with exit code 0 or explicit manual_evidence"
        )
    require_summary(repo)
    dryforge = detect_dryforge(repo)
    append_result = append_event(repo, event, dry_run=args.dry_run)
    summary_result = update_operations_summary(
        repo, dryforge, recent_verification_label({"commands": commands, "manual_evidence": manual}), dry_run=args.dry_run
    )
    return EXIT_OK, {
        "mode": "log",
        "event": event,
        "append": dataclasses.asdict(append_result),
        "summary": dataclasses.asdict(summary_result),
        "dry_run": args.dry_run,
    }


def render_dashboard(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_ops = detect_repo_ops(repo)
    summary_path = repo / OPS_SUMMARY_REL
    summary_preview = ""
    if summary_path.exists():
        resolve_inside_repo(repo, summary_path)
        summary_preview = summary_path.read_text(encoding="utf-8", errors="replace")[:4000]
    rows = "\n".join(
        f"<tr><td>{html.escape(str(e.get('date','')))}</td><td>{html.escape(str(e.get('event','')))}</td><td>{html.escape(str(e.get('status','')))}</td><td>{html.escape(str(e.get('task_id','')))}</td><td>{html.escape(str(e.get('summary','')))}</td></tr>"
        for e in repo_ops.task_log.events[-20:]
    )
    if not rows:
        rows = "<tr><td colspan='5'>No task-log events recorded.</td></tr>"
    ledger_rows = "\n".join(
        f"<tr><td>{html.escape(str(e.get('date','')))}</td><td>{html.escape(str(e.get('task_id','')))}</td><td>{html.escape(str(e.get('status','')))}</td><td>{'yes' if e.get('completion_allowed') else 'no'}</td><td>{html.escape(', '.join(str(b) for b in e.get('blockers') or []) or '-')}</td><td>{html.escape(str(e.get('archive','') or '-'))}</td></tr>"
        for e in repo_ops.ledger_entries[-20:]
    )
    if not ledger_rows:
        ledger_rows = "<tr><td colspan='6'>No ledger entries recorded.</td></tr>"
    blockers = [e for e in repo_ops.task_log.events if e.get("status") == "blocked" or e.get("event") == "blocked"]
    open_ledger = len(open_ledger_entries(repo_ops))
    content = f"""<!doctype html>
<html lang="ko">
<meta charset="utf-8">
<title>Dryforge Ops Dashboard</title>
<style>body{{font-family:system-ui,sans-serif;margin:32px;line-height:1.5;color:#111827}}.card{{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:16px 0;background:#fff}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #e5e7eb;padding:8px;vertical-align:top}}th{{background:#f9fafb;text-align:left}}.badge{{display:inline-block;border-radius:999px;padding:2px 10px;background:#eef2ff}}pre{{white-space:pre-wrap;background:#f9fafb;border:1px solid #e5e7eb;padding:12px;border-radius:8px}}</style>
<h1>Dryforge Ops Dashboard</h1>
<div class="card"><strong>Current status</strong><br><span class="badge">events: {len(repo_ops.task_log.events)}</span> <span class="badge">blocked: {len(blockers)}</span> <span class="badge">ledger: {html.escape(repo_ops.ledger)}</span> <span class="badge">open cycles: {open_ledger}</span></div>
<div class="card"><h2>Recommended next action</h2><p>{html.escape(recommend_next(detect_dryforge(repo), repo_ops))}</p></div>
<div class="card"><h2>Cycle ledger</h2><table><thead><tr><th>Date</th><th>Task</th><th>Status</th><th>Completion allowed</th><th>Blockers</th><th>Archive</th></tr></thead><tbody>{ledger_rows}</tbody></table></div>
<div class="card"><h2>Recent events</h2><table><thead><tr><th>Date</th><th>Event</th><th>Status</th><th>Task</th><th>Summary</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="card"><h2>Summary preview</h2><pre>{html.escape(summary_preview or 'No .agents/ops/operations.md yet.')}</pre></div>
<p>Source: {html.escape(OPS_SUMMARY_REL.as_posix())}, {html.escape(TASK_LOG_REL.as_posix())}, {html.escape(LEDGER_REL.as_posix())}</p>
</html>
"""
    dashboard = repo / DASHBOARD_REL
    target = proposed_path(dashboard) if dashboard.exists() else dashboard
    result = write_new_text(repo, target, content, dry_run=args.dry_run)
    return EXIT_OK, {"mode": "dashboard", "dashboard": dataclasses.asdict(result), "dry_run": args.dry_run}


def create_handoff(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_ops = detect_repo_ops(repo)
    dryforge = detect_dryforge(repo)
    target = args.handoff or (HANDOFF_DIR_REL / f"handoff-{args.date or today_iso()}.md").as_posix()
    recent_events = repo_ops.task_log.events[-5:]
    completed = [e for e in recent_events if e.get("event") == "completed" and e.get("status") == "completed" and e.get("evidence", {}).get("completion_allowed")]
    verification = "완료 증거가 있는 최근 completed 이벤트가 있습니다." if completed else "검증 증거가 확인된 completed 이벤트가 없으므로 완료 주장은 보류합니다."
    completed_lines = [f"- {e.get('date')} {e.get('task_id')}: {e.get('summary')}" for e in recent_events if e.get("status") == "completed"]
    if not completed_lines:
        completed_lines = ["- 최근 completed 이벤트가 없습니다."]
    content = "\n".join([
        "# Dryforge 결과 핸드오프",
        "",
        "## 현재 상태",
        f"- Active 3문서: {'있음' if dryforge.active else '없음'}",
        f"- 최신 archive: `{dryforge.latest_archive or 'missing'}`",
        f"- Ledger: `{LEDGER_REL.as_posix()}`",
        f"- Task log: `{TASK_LOG_REL.as_posix()}`",
        "",
        "## 완료된 내용",
        *completed_lines,
        "",
        "## 검증 증거",
        f"- {verification}",
        "",
        "## 열린 리스크",
        "- 검증 증거가 누락된 이벤트는 completed로 간주하지 않습니다.",
        "",
        "## 다음 액션",
        "- 필요하면 dryforge archive와 control-plane task-log를 재검토합니다.",
        "",
        "## Workflow 승격 후보",
        "- `workflow suggest` 결과를 확인합니다.",
        "",
    ])
    result = write_new_text(repo, target, content, dry_run=args.dry_run)
    if result.skipped and result.reason == "already exists":
        raise BridgeError(f"handoff already exists: {result.path}")
    return EXIT_OK, {"mode": "handoff", "handoff": dataclasses.asdict(result), "dry_run": args.dry_run}


def slugify_domain(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (re.sub(r"-+", "-", slug) or "general")[:63]


def suggest_harness(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_ops = detect_repo_ops(repo)
    events = combined_task_events(repo_ops)
    adopted_at: dict[str, int] = {}
    for idx, event in enumerate(events):
        if str(event.get("event")) == WORKFLOW_ADOPTED_EVENT:
            adopted_at[slugify_domain(str(event.get("workflow") or event.get("type") or "general"))] = idx
    counts: Counter[str] = Counter()
    evidence: defaultdict[str, list[str]] = defaultdict(list)
    for idx, event in enumerate(events):
        if str(event.get("event")) == WORKFLOW_ADOPTED_EVENT:
            continue
        candidate = slugify_domain(str(event.get("type") or "general"))
        if idx <= adopted_at.get(candidate, -1):
            continue
        counts[candidate] += 1
        if len(evidence[candidate]) < 5:
            evidence[candidate].append(str(event.get("task_id") or event.get("idempotency_key") or "unknown"))
    candidates = [
        {
            "workflow_candidate": candidate,
            "confidence": "high" if count >= 5 else "medium",
            "reason": f"same task type observed {count} times",
            "evidence_task_ids": evidence[candidate],
        }
        for candidate, count in counts.items()
        if count >= 3
    ]
    return EXIT_OK, {
        "mode": "workflow-suggest",
        "candidates": candidates,
        "adopted_workflows": sorted(adopted_at),
        "delegate_to": "harness skill",
        "legacy_sources": [item.path for item in repo_ops.legacy_task_logs if item.state == "valid"],
    }


def proposed_path(path: Path) -> Path:
    candidate = path.with_name(path.stem + ".proposed" + path.suffix)
    if not candidate.exists():
        return candidate
    for idx in range(2, 100):
        alt = path.with_name(path.stem + f".proposed-{idx}" + path.suffix)
        if not alt.exists():
            return alt
    raise BridgeError(f"cannot find non-overwriting proposed path for {path}")


def to_plain_lines(payload: dict[str, Any]) -> str:
    mode = payload.get("mode")
    if mode == "doctor":
        lines = [f"health={payload.get('health')}", f"recommended_next_action={payload.get('recommended_next_action')}"]
        for check in payload.get("checks", []):
            lines.append(f"check={check.get('name')} status={check.get('status')} detail={check.get('detail')}")
        return "\n".join(lines)
    if mode == "preflight":
        lines = [f"preflight_status={payload.get('status')}", f"recommended_next_action={payload.get('recommended_next_action')}"]
        for risk in payload.get("risks", []):
            lines.append(f"risk={risk.get('kind')} severity={risk.get('severity')} detail={risk.get('detail')}")
        return "\n".join(lines)
    if "dryforge" in payload and "repo_ops" in payload:
        dryforge = payload["dryforge"]
        repo_ops = payload["repo_ops"]
        lines = [
            f"dryforge_active={str(dryforge.get('active')).lower()}",
            f"latest_archive={dryforge.get('latest_archive') or 'missing'}",
            f"repo_ops_summary={repo_ops.get('summary', 'unknown')}",
            f"task_log={repo_ops.get('task_log', {}).get('state', 'unknown')}",
            f"ledger_open={sum(1 for e in repo_ops.get('ledger_entries', []) if not e.get('completion_allowed', True) or e.get('blockers'))}",
            f"recommendation={payload.get('recommendation')}",
        ]
        if repo_ops.get("task_log", {}).get("error"):
            lines.append(f"error={repo_ops['task_log']['error']}")
        return "\n".join(lines)
    if mode == "workflow-suggest":
        candidates = payload.get("candidates") or []
        adopted = payload.get("adopted_workflows") or []
        lines: list[str] = []
        if not candidates:
            lines.append("workflow_candidate=none")
        for item in candidates:
            lines.append(f"workflow_candidate={item['workflow_candidate']}")
            lines.append(f"confidence={item['confidence']}")
            lines.append(f"evidence_task_ids={','.join(item['evidence_task_ids'])}")
        if adopted:
            lines.append(f"adopted_workflows={','.join(adopted)}")
        if candidates:
            lines.append("delegate_to=harness skill (design the reusable workflow there)")
        return "\n".join(lines)
    if "event" in payload:
        event = payload["event"]
        lines = [
            f"mode={mode}",
            f"event={event.get('event')}",
            f"status={event.get('status')}",
            f"idempotency_key={event.get('idempotency_key')}",
        ]
        for key in ("append", "evidence_file", "ledger", "summary"):
            if key in payload:
                result = payload[key]
                lines.append(f"{key}={result.get('path') or 'none'} written={str(result.get('written')).lower()} skipped={str(result.get('skipped')).lower()} reason={result.get('reason') or ''}")
        return "\n".join(lines)
    lines = []
    for key, value in payload.items():
        lines.append(f"{key}={json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, dict) else value}")
    return "\n".join(lines)


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--date")
    parser.add_argument("--task-id")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--strict", action="store_true")


def build_product_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dryforge native ops control-plane.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "preflight", "before-go", "after-ready", "after-go", "assess", "dashboard"):
        child = sub.add_parser(name)
        add_common_options(child)
    handoff = sub.add_parser("handoff")
    handoff.add_argument("handoff", nargs="?")
    add_common_options(handoff)
    log_parser = sub.add_parser("log")
    log_parser.add_argument("--event", required=True, help="path to one JSON event object, or '-' to read stdin")
    log_parser.add_argument("--idempotency-key", dest="idempotency_key")
    add_common_options(log_parser)
    workflow = sub.add_parser("workflow")
    wf_sub = workflow.add_subparsers(dest="workflow_command", required=True)
    suggest = wf_sub.add_parser("suggest")
    add_common_options(suggest)
    return parser


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    actual = list(sys.argv[1:] if argv is None else argv)
    return build_product_parser().parse_args(actual)


def dispatch(repo: Path, args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    command = args.command
    if command == "doctor":
        return run_doctor(repo, args)
    if command == "preflight":
        return run_preflight(repo, args)
    if command == "before-go":
        return run_before_go(repo, args)
    if command == "assess":
        return run_assess(repo, args)
    if command == "after-ready":
        return run_after_ready(repo, args)
    if command == "after-go":
        return run_after_go(repo, args)
    if command == "dashboard":
        return render_dashboard(repo, args)
    if command == "handoff":
        return create_handoff(repo, args)
    if command == "log":
        return run_ops_log(repo, args)
    if command == "workflow" and args.workflow_command == "suggest":
        return suggest_harness(repo, args)
    raise BridgeError("no mode selected", EXIT_ERROR)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        repo = resolve_repo(args.repo)
        exit_code, payload = dispatch(repo, args)
    except BridgeError as exc:
        payload = {"error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True) if args.json_output else f"error={exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover
        payload = {"error": f"unexpected error: {exc}"}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True) if args.json_output else f"error=unexpected error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if args.json_output:
        print(json.dumps(redact(payload), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(to_plain_lines(redact(payload)))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
