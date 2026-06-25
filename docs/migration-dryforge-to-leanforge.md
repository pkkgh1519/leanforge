# Dryforge to Leanforge migration

Leanforge is the renamed and productized plugin identity. The canonical local
state directory is `.leanforge/`. Older repositories may still contain
`.dryforge/` from pre-rename runs.

## What changed

| Area | Current Leanforge behavior |
|---|---|
| Marketplace source | `pkkgh1519/leanforge` |
| Plugin identity | `leanforge` |
| User-facing command prefix | `Leanforge:*` and `/leanforge:*` |
| Canonical state directory | `.leanforge/` |
| Legacy state directory | `.dryforge/`, read only for guarded compatibility migration |

## Command mapping

Use the current Leanforge lifecycle:

| Current command | Use for |
|---|---|
| `Leanforge:Prime` (`/leanforge:prime`) | Create the reviewed spec, plan, and handoff. |
| `Leanforge:Run` (`/leanforge:run`) | Execute the approved contract. |
| `Leanforge:Set` (`/leanforge:set`) | Onboard an existing codebase into the project harness. |
| `Leanforge:Harness` (`/leanforge:harness`) | Design or improve reusable agent workflows and skills. |

## Automatic compatibility migration

Leanforge may automatically move `.dryforge/` to `.leanforge/` only when all of
these are true:

1. `.leanforge/` is absent.
2. `.dryforge/` exists.
3. `.dryforge/` has no active `run.json`.
4. `.dryforge/` has no active root 3-doc files.
5. `.dryforge/` has no `worktrees/` directory.

When migration is safe, Leanforge records `.leanforge/migration.json` with the
schema `leanforge.stateMigration.v1`.

## When Leanforge refuses to migrate

Leanforge will stop instead of migrating if:

- `.dryforge/run.json` indicates an interrupted run;
- `.dryforge/` contains active root 3-doc files;
- `.dryforge/worktrees/` exists;
- both `.leanforge/` and `.dryforge/` contain active state.

This is intentional. The guard prevents active design contracts or task
worktrees from being overwritten by a rename migration.

## Recommended migration path

1. Commit or back up any work you care about before migration.
2. Install Leanforge from `pkkgh1519/leanforge`.
3. Run the Leanforge command that matches your next action:
   - `/leanforge:prime` for a new design cycle;
   - `/leanforge:run` to execute an approved contract;
   - `/leanforge:set` to onboard an existing codebase.
4. If Leanforge reports active legacy state, finish, resume, or deliberately
   abandon that legacy run first.
5. Retry the Leanforge command.
6. Confirm `.leanforge/migration.json` exists if an automatic migration occurred.

## Do not do this by default

- Do not manually rename `.dryforge/` while a run is active.
- Do not delete `.dryforge/worktrees/` unless you have verified the work was
  merged or is disposable.
- Do not keep two active state directories without deciding which one is
  canonical.

## Git ignore behavior

Leanforge keeps local state out of normal commits. Target repositories should
ignore both directories:

```text
.leanforge/
.dryforge/
```

`Leanforge:Set` and `Leanforge:Run` ensure this for target project state. If you
manage gitignore manually, keep both entries until legacy state has been fully
resolved.
