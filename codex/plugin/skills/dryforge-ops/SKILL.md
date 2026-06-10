---
name: dryforge-ops
description: "Use when operating dryforge native control-plane records for ready/go/migration outcomes, .agents/ops evidence, ledgers, task logs, dashboards, handoffs, and repeatable .agents workflows without reimplementing dryforge execution."
---

# dryforge-ops

`dryforge-ops` is dryforge's native control-plane skill.
Keep dryforge `ready`, `go`, and `migration` as the lifecycle center. Treat `.dryforge/` as read-only evidence by default. Use the helper script to record dryforge outcomes into `.agents/ops` and to propose repeatable `.agents/workflows` only when repetition is visible.

## Quick start

Run the helper from this skill directory:

```bash
python scripts/dryforge_ops.py assess <repo>
python scripts/dryforge_ops.py doctor <repo>
python scripts/dryforge_ops.py preflight <repo>
python scripts/dryforge_ops.py before-go <repo>
python scripts/dryforge_ops.py after-ready <repo>
python scripts/dryforge_ops.py after-go <repo>
python scripts/dryforge_ops.py log <repo> --event event.json
python scripts/dryforge_ops.py workflow suggest <repo>
```

Use `--dry-run` before any write mode when the repository state is unfamiliar.
Use `--json` when another tool will consume the output.

## Operating rules

- Do not reimplement or bypass dryforge `go`.
- Do not mutate `.dryforge/` by default.
- Parse `.agents/ops/task-log.jsonl` before every append.
- Read existing `docs/operations.md` and `docs/operations/` as legacy repo-ops context, and `docs/harness/` as the harness skill's plane; preserve all of them read-only without overwriting.
- Reject corrupt JSONL, unsafe write paths, and symlink or junction escapes.
- Use `idempotency_key` to skip duplicate events.
- Never write `completed/completed` without command evidence with exit code `0` or explicit manual evidence.
- Redact secret-like values before writing summaries, handoffs, or evidence previews.
- Do not overwrite existing handoff or generated files. Existing targets receive `.proposed` alternatives instead.
- Delegate reusable workflow design to the `harness` skill; do not generate project workflow docs from this bridge.

## Workflow

1. Assess the repository:
   - detect active `.dryforge/{handoff,spec,plan}.md`
   - detect numeric `.dryforge/NNN/` archives and `status.json`
   - validate `.agents/ops` summary, task-log, ledger, and evidence state
   - surface open ledger cycles (entries that are incomplete or carry blockers) as the recommended next action
   - read `docs/operations*` (legacy repo-ops) and `docs/harness` (harness skill plane) context without modifying it
   - collect git branch/head/status/worktree evidence when available
2. After dryforge `ready`, run `after-ready`:
   - require active 3-docs
   - append exactly one `planned/open` event to `.agents/ops/task-log.jsonl`
   - update the marked `Dryforge 실행 상태` section in `.agents/ops/operations.md`
3. Before dryforge `go`, run `doctor`, `preflight`, or `before-go`:
   - report `ok`, `warn`, or `blocked`
   - detect blocked state and live/runtime risk
   - record preflight evidence when `before-go` is used
4. After dryforge `go`, run `after-go`:
   - inspect the latest archive and evidence files
   - normalize evidence into schema version `dryforge-ops.evidence.v1`
   - write evidence JSON under `.agents/ops/evidence/`
   - update `.agents/ops/ledger.json` as the operations ledger
   - append `completed`, `validated`, `needs_review`, or `blocked` based on evidence
   - update the operations summary without duplicating the section
5. For later phases, use:
   - `dashboard` to render a read-only operations dashboard — a cycle-ledger roll-up, the open-cycle count, recent task-log events, and the recommended next action
   - `handoff <path>` to create a no-overwrite handoff note
   - `log --event <file|->` to append one guarded ad-hoc event — work done outside ready/go cycles, or a `workflow_adopted` record after the harness skill installs a suggested workflow; it refuses a missing `.agents/ops/` plane and refuses `completed/completed` without evidence
   - `workflow suggest` to detect repeated task types and emit a `delegate_to=harness skill` signal when a workflow recurs; candidates already recorded as `workflow_adopted` stay suppressed until new repetition accumulates

## References

- `references/dryforge-ops-contract.md` for ownership boundaries and CLI modes.
- `references/task-log-event-schema.md` for JSONL fields and idempotency.
- `references/evidence-json-schema.md` for the normalized `after-go` evidence schema (`dryforge-ops.evidence.v1`).
- `references/operations-summary-section.md` for the generated summary block.
- `references/harness-upgrade-policy.md` for workflow suggestion and harness-delegation rules.
- `references/dryforge-hook-guide.md` for bridge-first dryforge usage.

