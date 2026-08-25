# Troubleshooting

This page covers the common installation and first-run failure modes for
Leanforge.

## Skill or command does not appear after install

1. Confirm the marketplace source is `pkkgh1519/leanforge`.
2. Re-run the install command for your client.
3. Restart the client and open a new session after installation or an update.
4. Check that the installed plugin identity is `leanforge`, not an older name.

Host-specific entry points:

- **Claude Code:** `/leanforge:prime`, `/leanforge:run`, `/leanforge:set`, and optional
  `/leanforge:run-tdd`.
- **Codex CLI:** open `/skills` or type `$` and select `prime`, `run`, `set`, or `run-tdd`; when the
  names are unambiguous, `$prime`, `$run`, `$set`, and `$run-tdd` explicitly mention them.
- **ChatGPT desktop Codex surface:** select the corresponding installed Leanforge skill from the
  plugin/skill picker in a fresh conversation.

Codex plugins do not create `/leanforge:*` slash commands. An `Unrecognized command` response to
`/leanforge:prime` in Codex is an invocation mismatch, not evidence that the installed skill is absent.
For an unreleased candidate, also verify the active cache path and package digest with
[the local candidate procedure](local-candidate-testing.md) before attributing behavior to that branch.

## When to use `Leanforge:Run TDD` instead of `Leanforge:Run`

`Run TDD` is a thin wrapper: it runs the exact same `Run` workflow and adds one thing — a
mandatory vertical red-green-refactor loop for tasks that change observable behavior, plus a
standing refusal to accept shallow evidence (file existence, source-string checks, symbol
existence, skipped tests, weakened assertions) as proof a behavior works. `Run` alone already
applies right-sized, test-first verification by judgment; `Run TDD` removes the judgment call
for behavior-changing work and makes the discipline structural instead of optional.

Reach for `Run TDD` over plain `Run` when:

- the task carries real cost if wrong — business logic, authorization, financial or
  scoring calculations, state transitions, validation rules;
- other systems depend on the behavior — public API surface, parsing/serialization formats,
  anything with external consumers where a late-caught regression is expensive;
- the spec has an Acceptance & Evidence Matrix and you want each AC walked test-first,
  one behavior at a time, instead of implemented in one pass and verified after the fact;
- prior work in this codebase has shipped shallow or retrofitted tests, and you want the
  wrapper's explicit evidence exclusions enforced rather than left to judgment;
- the behavior has enough edge cases that implementing it in one pass tends to hide bugs —
  the vertical slice-by-slice loop surfaces them incrementally instead.

Stay on plain `Run` when the task is documentation-only, a harness or agent-instruction
update, formatting-only, a file move or rename, mechanical import/path wiring, a simple
configuration change, scaffolding with no observable behavior yet, or build/CI plumbing with
no product behavior change — `Run TDD` explicitly excludes these from forced TDD anyway, so
invoking it buys nothing `Run` doesn't already do.

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
