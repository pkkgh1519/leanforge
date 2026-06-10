# Task-log Event Schema

Canonical path:

```text
.agents/ops/task-log.jsonl
```

Legacy `docs/operations/task-log.jsonl` may be read for context but is not modified by dryforge-ops.

Required fields:

```json
{
  "task_id": "task-YYYY-MM-DD-slug",
  "event": "planned",
  "status": "open",
  "date": "YYYY-MM-DD",
  "summary": "..."
}
```

Recommended fields: `type`, `files`, `validation`, `result`, `next`, `repo_state`, `worktree_state`, `live_state`, `dryforge`, `evidence`, `idempotency_key`.

## Event/status mapping

| Mode | Condition | event | status |
| --- | --- | --- | --- |
| after-ready | active docs exist | planned | open |
| after-go | verification passed | completed | completed |
| after-go | verification failed | validated | blocked |
| after-go | evidence missing | needs_review | pending |
| after-go | archive missing | blocked | blocked |
| log | ad-hoc agent work between dryforge cycles | as provided | as provided |
| log | harness skill adopted a suggested workflow | workflow_adopted | adopted |

Before append, parse the entire canonical JSONL file. If any non-empty line is invalid JSON or not an object, abort the write. If an existing event has the same `idempotency_key`, skip append and report the duplicate as an idempotent no-op.

## Ad-hoc events via `log`

`log --event <file|->` appends exactly one caller-provided event after the same full-parse and idempotency checks. Rules:

- It refuses to bootstrap a missing `.agents/ops/` plane; run `after-ready` (or create the plane deliberately) first.
- `date` and `task_id` are filled from `--date`/`--task-id` or defaults when omitted; `event`, `status`, and `summary` must be present in the JSON.
- `completed/completed` is refused unless the event carries command evidence with exit code `0` (in `evidence.commands` or parseable `validation` lines) or explicit `manual_evidence`.
- Pass `--idempotency-key` when a re-run must stay a no-op; ad-hoc events have no natural key and duplicate appends are otherwise possible.
- Keep `type` a short ASCII keyword (for example `code`, `qa`, `docs`, `research`, `ops`); `workflow suggest` groups by slugified `type`, and non-ASCII values collapse into `general`.

A `workflow_adopted` event names the adopted candidate in its `workflow` field. `workflow suggest` excludes adoption records from repetition counts and suppresses an adopted candidate until new events of that type accumulate after the adoption.
