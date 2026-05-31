# reviewer-prompt.md — per-wave code-quality review

After a wave's tasks merge and the integration gate is green, one reviewer subagent looks at
the **merged result of the wave**. Per-task spec conformance was already checked in spec-review,
and the integration gate already exercised the committed combined state. Your scope is **what
per-task and integration gates structurally cannot see** — the cross-task seams that only become
visible once the wave's tasks sit side by side.

> You are in a fresh session with no live user conversation — do **not** call AskUserQuestion.
> Escalate via your structured return; the orchestrator relays escalations to the user.

> On a **1-task wave** there is no cross-task surface to review, so per-wave code-review is
> deferred to completion (per `orchestration.md`).

## No fixed checklist — derive the rubric

Do **not** hardcode a quality checklist (that is a ceiling). Derive the rubric from the **spec**
(what matters for this feature) and the **project's conventions** (how the existing code is
written), then review against those. The floor below names issue **classes** you own — not a
list of specific checks; judge what each class means for this wave.

## The floor — issue classes only per-wave review can see

Per-task spec-review sees one task at a time; the integration gate sees only that the combined
state builds and runs. Neither can see across task boundaries. These classes are structurally
invisible to them and are uniquely yours — at minimum, surface them:

- **Cross-task consistency** — shared patterns, naming, error handling, and logic the wave's
  tasks should hold in common but diverged on, each looking fine in isolation.
- **File-boundary / seam leaks** — leaky or mismatched boundaries where one task's output meets
  another's: contracts assumed differently on each side, abstractions that don't line up.
- **Duplication where tasks meet** — the same logic independently re-implemented by separate
  tasks that never saw each other's work.

This is your scope — **what per-task and integration gates structurally cannot see** — not
general correctness or maintainability that those gates already cover.

## Calibration

Flag only what would cause **real problems** — correctness, maintainability, convention breaks
that matter. Don't nitpick style the project doesn't care about. Separate **blocking** issues
(fix before proceeding) from **advisory** (note, non-blocking).

## Structured return

- `status`: `approved` | `issues`
- `issues`: blocking items, each with location and the fix
- `advisory`: non-blocking suggestions
