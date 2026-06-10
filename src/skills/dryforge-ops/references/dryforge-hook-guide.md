# Dryforge Hook Guide

Control-plane-first manual flow:

1. Run dryforge `ready` to create `.dryforge/handoff.md`, `.dryforge/spec.md`, and `.dryforge/plan.md`.
2. Run `python scripts/dryforge_ops.py after-ready <repo>` to record the planned state.
3. Run dryforge `go` as the implementation engine.
4. Run `python scripts/dryforge_ops.py after-go <repo>` to sync archive, validation evidence, ledger, and task-log.

Optional future integration may call `after-go` from a dryforge final-stage hook, but the control-plane must keep working without any dryforge core patch.

