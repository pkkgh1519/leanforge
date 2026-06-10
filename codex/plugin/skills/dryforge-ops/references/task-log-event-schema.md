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

Before append, parse the entire canonical JSONL file. If any non-empty line is invalid JSON or not an object, abort the write. If an existing event has the same `idempotency_key`, skip append and report the duplicate as an idempotent no-op.
