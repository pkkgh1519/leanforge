# dryforge-ops Contract

## Ownership

| Area | Owner | dryforge-ops behavior |
| --- | --- | --- |
| `.dryforge/` | dryforge | Read-only evidence by default |
| `.agents/ops/` | dryforge-ops | Safe append/update with JSONL, evidence, and ledger validation |
| `docs/operations.md` and `docs/operations/` | project/legacy repo-ops | Read-only legacy context; preserve without overwrite |
| `docs/harness/` | harness skill | Read-only here; owned and written by the bundled harness skill |
| `.agents/workflows/` and `.agents/skills/` | harness skill | Read-only detection here; reusable workflow design is delegated to the harness skill |

## Required CLI

```bash
python scripts/dryforge_ops.py assess <repo>
python scripts/dryforge_ops.py doctor <repo>
python scripts/dryforge_ops.py preflight <repo>
python scripts/dryforge_ops.py before-go <repo>
python scripts/dryforge_ops.py after-ready <repo>
python scripts/dryforge_ops.py after-go <repo>
python scripts/dryforge_ops.py dashboard <repo>
python scripts/dryforge_ops.py handoff .agents/ops/handoffs/handoff-YYYY-MM-DD.md <repo>
python scripts/dryforge_ops.py workflow suggest <repo>
```

Common options: `--dry-run`, `--date YYYY-MM-DD`, `--task-id task-YYYY-MM-DD-slug`, `--json`, `--strict`.

The subcommand form above is the canonical and only CLI surface. Author all hooks and docs with it;
add new modes to `build_product_parser` only.

## Product lifecycle modes

- `doctor` reports lifecycle health as `ok`, `warn`, or `blocked` and includes `recommended_next_action`.
- `preflight` detects blocked operations state and live/runtime risk before dryforge `go`.
- `before-go` records a preflight event for active 3-docs without running dryforge.
- `after-go` normalizes evidence, writes `.agents/ops/evidence/<task_id>.evidence.json`, updates `.agents/ops/ledger.json`, and appends the task-log event idempotently.
- `workflow suggest` groups completed task-log events by `type`, emits repeated-evidence `task_id` values for candidates, and prints `delegate_to=harness skill` so reusable workflow design is handed to the harness skill.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success or read-only assessment completed |
| 1 | Unexpected error |
| 2 | Validation or safety blocker |

