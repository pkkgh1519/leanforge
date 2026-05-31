# spec-review-prompt.md — per-task spec review

After an implementer returns `DONE`, one subagent checks that task's diff against the **spec
requirement** it was meant to realize — the "1" of spec-first 1+1, run **per task, before
merge** (a spec violation caught after merge costs an undo/redo). This is *conformance*, not
code quality (that is `reviewer-prompt.md`, per wave).

## Independence — what the reviewer is given

To stay independent, the reviewer receives **only** (a) the spec requirement(s) for the task and
(b) the raw diff / task branch — both **passed inline** (the worktree has no `dryforge/` files;
`dryforge/` is gitignored). It is **not** given the implementer's summary, `concerns`, or test
claims — re-derive conformance from the diff itself, do not anchor on the author's narrative.

For a declared **no-file-diff task** (state / operational / external — work whose result lives
outside the tree), there is no raw file diff to read: judge conformance from the commit message
plus the captured external evidence passed inline, not from a diff that doesn't exist.

## What to check

Given the spec requirement(s) for the task + the task's diff, in an independent context: does
the implementation **do what the spec says** — behavior, invariants, edge-case rules, API
surface? Judge conformance to the spec, nothing else. For a no-file-diff task the same question
holds against the commit message + captured external evidence rather than a file diff.

## Calibration

Flag a **real spec deviation** — missing behavior, a violated invariant, an edge case the spec
specifies that the code doesn't handle. Do **not** flag style, naming, or quality — that is the
per-wave reviewer's job. spec is "correct"; measure against it.

If the task's spec slice names a testable risk (edge case, invariant, validation) but the task was
classified RISK=NONE and shipped without a test, flag needs-fix — a real risk was sized away.

## Scaffold / infrastructure tasks (degrade the check)

Some tasks — most often a greenfield **Task 1** (scaffold the project: set up whatever it needs to
exist before feature work, as the stack defines it) — realize **no behavioral spec requirement**;
they exist to establish the harness the spec's *required-verification* needs. For such a task there is no behavior to conform to, so
spec-review **degrades** to: does it stand up the structural preconditions the spec relies on (the
verify commands run, the declared layout/exports exist as empty placeholders)? — not a behavioral
trace. Don't manufacture a behavioral deviation where the spec asks for none; `pass` on the harness
being correctly established. (The orchestrator still runs N reviews for N tasks; this just says what
"conformance" means for a task with no behavioral surface.)

## Structured return

- `status`: `pass` | `needs-fix`
- on `needs-fix`: the spec requirement violated + what is missing/wrong (specific enough to fix)

## escalate — when the spec itself is the problem

If the **spec** is ambiguous or self-conflicting (not just the implementation), say so — do not
pick an interpretation. The orchestrator escalates to the user; spec is ground truth and only
the user changes it.

You are in a fresh session with no live user conversation — do NOT call AskUserQuestion. Return
NEEDS_CONTEXT or BLOCKED (implementer) / escalate via your structured return; the orchestrator
relays escalations to the user.
