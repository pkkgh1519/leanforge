# Changelog

## v1.6.5 (2026-06-21)

- switch public marketplace source documentation from `fn-opt/leanforge` to `pkkgh1519/leanforge`
- update plugin author/developer marketplace metadata to `pkkgh1519` while preserving original LICENSE notices

## v1.6.4 (2026-06-21)

- standardize Harness user-facing invocation as `/leanforge:harness` in README and Codex prompts
- keep Codex display names as `Leanforge:*` while using slash commands for invocation guidance

## v1.6.3 (2026-06-21)

- remove site/homepage metadata and documentation links; no Leanforge site is declared until a dedicated site exists
- switch marketplace install documentation to `fn-opt/leanforge` (superseded by v1.6.5)
- switch repository metadata and README links to `pkkgh1519/leanforge`

## v1.6.2 (2026-06-21)

- make `.leanforge/` the canonical local state directory for Prime/Run/Set lifecycle docs
- keep `.dryforge/` only as a guarded legacy migration source; active legacy runs and worktrees are never migrated automatically
- update repo-local Run-compatible skill validation to block direct reads from both `.leanforge` and legacy `.dryforge` active docs

## v1.6.1 (2026-06-21)

- clarify that the external marketplace package path remains `fn-opt/dryforge` as a distribution-compatibility path while the installed plugin identity is `leanforge`
- point plugin homepage/repository metadata at the current `pkkgh1519/dryforge-ops` remote

## v1.6.0 (2026-06-21)

- rename the plugin identity and visible command surface to Leanforge
- rename lifecycle skills: ready → prime, go → run, migration → set, and dryforge-go-tdd → run-tdd
- keep the local runtime state directory as `.dryforge/` for backward compatibility

## v1.5.0 (2026-06-20)

- remove the `dryforge-ops` skill from the default Claude/Codex plugin surface
- keep status, handoff, interrupted-run recovery, and cycle history in core `.dryforge/` state
- decouple `Run` and `harness` from `.agents/ops` ledgers, task logs, dashboards, and workflow-suggest adoption records

## v1.4.0 (2026-06-11)

- dryforge-ops: wire the ledger read-consume path — `dashboard` now renders cycle-ledger roll-up (task, status, blockers) with open-cycle count, and `doctor` recommendation is ledger-aware (points to latest unresolved entry before suggesting next lifecycle step)
- dryforge-ops: `assess` and `dashboard` gracefully handle corrupt ledger.json (parses via try/except, never blocks)
- All 28 dryforge-ops tests pass; 3-way install parity verified

## v1.3.0 (2026-06-10)

- dryforge-ops: add the `log` mode — append one guarded ad-hoc task-log event (full JSONL parse, idempotency, secret redaction); refuses a missing `.agents/ops/` plane and refuses `completed/completed` without exit-0 command evidence or explicit manual evidence
- dryforge-ops: `workflow suggest` closes the flywheel — `workflow_adopted`/`adopted` events suppress an adopted candidate until new repetition accumulates after the adoption, and adoption records no longer count as repetition signal
- harness: record workflow adoption back into the dryforge-ops plane (Phase 7) so suggested candidates stop re-flagging once installed
- harness: output language is discovered at runtime and never assumed; interviewing no longer depends on any specific installed skill; description is platform-neutral
- benchmark: replace the stale workflow apply/validate case with the adoption-flywheel case

## v1.2.0 (2026-06-10)

- bundle the `harness` skill (durable repo-local agent workflow design) into the plugin
- dryforge-ops: `workflow suggest` now delegates reusable workflow design to the harness skill and removes the half-absorbed `apply`/`validate` modes
- dryforge-ops: drop the legacy `--flag` CLI surface; subcommand form is the only CLI
- wire `Leanforge Run` completion to an optional `dryforge-ops after-run` operations sync

## v1.1.0 (2026-06-09)

- v1.1.0 large update

## v1.0.2 (2026-06-08)

- v1.0.2 : minor update

## v1.0.1 (2026-06-07)

- README EDIT

## v1.0.0 (2026-06-07)

- official release v1.0.0

## v0.5.1 (2026-06-06)

- v0.5.1 minor update

## v0.5.0 (2026-06-03)

- claude, codex multi-platform support + orchestration efficiency improve

## v0.2.5 (2026-06-02)

- update v0.2.5 - orchestration effiency improvement

## v0.2.0 (2026-06-01)

- v0.2.0 update -performance enhance

## v0.1.2 (2026-06-01)

- improve task execution efficiency

## v0.1.1 (2026-06-01)

- fix: prevent output path collision with user projects
