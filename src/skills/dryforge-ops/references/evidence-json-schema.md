# Evidence JSON Schema

`after-go` writes normalized evidence to:

```text
.agents/ops/evidence/<task_id>.evidence.json
```

Required top-level fields:

```json
{
  "schema_version": "dryforge-ops.evidence.v1",
  "task_id": "task-YYYY-MM-DD-dryforge-go",
  "normalized_at": "ISO-8601",
  "repo": {
    "root": "/path/to/repo",
    "branch": "main",
    "head": "abc123"
  },
  "dryforge": {
    "latest_archive": ".dryforge/001",
    "active": false
  },
  "commands": [
    {
      "command": "npm test",
      "exit_code": 0,
      "source": ".dryforge/001/evidence.json"
    }
  ],
  "manual_evidence": [],
  "sources": [".dryforge/001/evidence.json"],
  "parse_errors": [],
  "completion_allowed": true,
  "blockers": [],
  "links": {
    "task_log": ".agents/ops/task-log.jsonl",
    "ledger": ".agents/ops/ledger.json",
    "evidence_json": ".agents/ops/evidence/task-YYYY-MM-DD-dryforge-go.evidence.json"
  }
}
```

Completion is allowed only when:

- a dryforge archive exists,
- active 3-docs are not still present,
- command evidence exists with all exit codes `0` or explicit manual evidence exists,
- no evidence parse errors exist.
