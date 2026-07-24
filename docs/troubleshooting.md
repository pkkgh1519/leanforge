# Troubleshooting

This page covers the common installation and first-run failure modes for
Leanforge.

## Command does not appear after install

1. Confirm the marketplace source is `pkkgh1519/leanforge`.
2. Re-run the install command for your client.
3. Restart the client if the command palette caches plugin metadata.
4. Check that the installed plugin identity is `leanforge`, not an older name.

Expected commands:

- `Leanforge:Prime` (`/leanforge:prime`)
- `Leanforge:Run` (`/leanforge:run`)
- `Leanforge:Set` (`/leanforge:set`)
- Codex only: `Leanforge:Run TDD` (`/leanforge:run-tdd`)

## `Leanforge:Run TDD` is missing

`Leanforge:Run TDD` is Codex-only. Claude Code installations should use the core
`Leanforge:Prime` -> `Leanforge:Run` lifecycle.

## Git is missing

Install git and make sure it is available on `PATH`. Leanforge uses git-backed
state and worktree isolation during execution.

## Project is not a git repository

Leanforge may ask to initialize git and create an initial commit before execution
can continue. This is expected because later `Run` work depends on a stable git
base.

## Active `.leanforge/run.json` blocks a new run

`.leanforge/run.json` is an interrupted-run marker. Do not delete it casually.
Choose one of these paths instead:

- resume the interrupted run;
- abandon it deliberately;
- repair or archive the active 3-doc if the run stopped before completion.

Leanforge uses this guard to avoid overwriting active design contracts.

## Legacy `.dryforge/` state blocks migration

If `.dryforge/` contains an active `run.json`, active root 3-doc, or
`worktrees/`, Leanforge will not migrate it automatically. Resolve the legacy run
first, then retry the Leanforge command.

See [Dryforge to Leanforge migration](migration-dryforge-to-leanforge.md).

## Both `.leanforge/` and `.dryforge/` exist

Leanforge treats `.leanforge/` as canonical. If both directories contain active
state, do not merge or delete either directory blindly. Decide which state is
canonical, finish or abandon the other state, and then retry.

## Checks fail in this repository

For repository contributors, the contract test suite is:

```text
python -m unittest discover -s tests -v
```

The GitHub Actions CI workflow runs the same command on pull requests.

## SDD-lite feels too heavy for a task

SDD-lite Stage 1 is scoped to behavior-changing work. Documentation,
configuration, mechanical wiring, and scaffold-only work should remain
lightweight. If a task is non-behavioral but the workflow is treating it like a
feature change, keep the evidence path minimal and call out the mismatch during
review.
