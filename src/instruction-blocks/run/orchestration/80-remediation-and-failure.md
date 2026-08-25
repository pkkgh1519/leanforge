
### Fix-dispatch and lightweight fix

**Substantive fix-dispatch** (bugs, review blocking findings): dispatched as a subagent on a branch
off the base — reuse a task worktree if present, else create a fresh one. The subagent commits;
the orchestrator merges back under the same merge-gate.

**Lightweight fix** (trivial advisory findings — 1–2 files, non-behavioral): the orchestrator MUST
triage each advisory after the final review. Trivial (1–2 files, non-behavioral — e.g. a missing
attribute, a test warning, a one-line comment) → edit directly on the base, commit, re-run the
completion gate. The default disposition is lightweight fix, not "accepted." Only mark an advisory
as accepted when a fix is genuinely inappropriate (design trade-off, spec-intentional behavior).
Do not skip advisories as "accepted" when a lightweight fix would take seconds. Scoped to trivial,
non-behavioral changes only — substantive findings still go to an independent fix-dispatch.

## Failure handling

<!-- leanforge:run-semantic:RUN-FAIL-CLOSED:start -->
```json
{
  "id": "RUN-FAIL-CLOSED",
  "kind": "failure_overlay",
  "definition": "Every result-bearing event carries one non-empty closed outcome, and every blocking, non-green, or unevaluable result enters the explicit failure overlay owned by runtime_failure_overlay before every continuation that follows that result. A concern disposition of promoted_to_failure is a failure result under the same forward-only overlay-before-continuation rule; earlier progress or routine events are not retroactively constrained. Continuations include route work and action, remedial worktree and implementer continuation, dispatch, merge, gate, cleanup, progress, user_output_wave_completion, and every routine read, write, dispatch, merge, gate, and cleanup event. The closed results cover task and merge checks, regeneration and wiring, integration, external evidence, completion verification, runtime smoke, conditional spec review, final review, and review verdict. Final full-diff review uses green for success and blocking, non-green, or unevaluable for failure; clear is verdict-only. Overlay alone does not recover a continued completion-gate or runtime-smoke failure: before any later dependent phase, the latest applicable attempt of that result type is orchestrator-owned and green. A terminal failure may stop after entering the overlay. Unevaluable is never green.",
  "constraints": [
    "Each event allows only its closed event-specific metadata and requires every identifier, value, owner, overlay, or result field used by its invariant.",
    "Every result-bearing event requires one non-empty outcome from its closed result vocabulary.",
    "Every blocking, non-green, and unevaluable closed result event, including all three final full-diff review failure outcomes and a blocking review verdict, and every promoted-to-failure concern disposition enters the failure overlay before any continuation that follows it, including user_output_wave_completion.",
    "failure_overlay_entered requires overlay failure and owner runtime_failure_overlay, and precedes every present route-work, remedial, dispatch, merge, gate, cleanup, progress, wave-completion output, or routine continuation after a failed result or promoted-to-failure disposition; prior continuations remain allowed.",
    "A failed completion gate or runtime smoke remains blocking in a continued flow until a later orchestrator-owned green attempt of the same result type precedes every dependent verification, smoke, final-review, verdict, completion, or user-gate phase.",
    "No continuation event is required after a terminal failure enters the overlay."
  ]
}
```
<!-- leanforge:run-semantic:RUN-FAIL-CLOSED:end -->

| Failure | Response |
|---|---|
| `BLOCKED` / `NEEDS_CONTEXT` | walk the bounded ladder: attempt 1 more context → attempt 2 upgraded model → escalate |
| max retries exceeded | **escalate to the user + preserve the worktree for manual recovery** (do not discard) |
| mid-run spec-review fail | re-dispatch with the specific fix |
| final review fail | fix-dispatch the blocking findings, re-run final review |
| merge conflict | analyze; resolve if mechanical / same-intent, else escalate |
| merge commit-msg hook rejection | inspect hook name + full output; verify branch state (`git log`); retry with the producer-discovered commit convention; else escalate with hook name + error + attempted message + branch state |
| regen-barrier non-zero / conflicting output | capture command + exit + stderr; analyze whether a prior merge broke a precondition; if it would overwrite merged files, escalate |
| deferred-wiring conflict | capture file + conflicting lines + involved tasks; escalate (never auto-pick a winner) |
| integration gate fail | analyze → identify the causing task → fix-dispatch |
| code-quality issue (final review) | fix-dispatch |
| architecture mismatch / suspected spec violation / data-corruption risk | **stop and escalate** |

- **Partial wave failure — cleanup order + retry semantics**: keep the merged successful tasks.
  **Preserve the failed task's worktree for diagnosis** (do not clean it). Retain successful
  worktrees until the completion gate; only a clean worktree whose landed commit is an ancestor of
  the base may be recycled between waves. **Never delete the base.** On retry, create a **FRESH worktree branched from the
  CURRENT base tip** — which now includes this wave's already-merged successes (the base tip
  advances per merge), so the retry builds on the integrated state, not the stale pre-wave tip. The
  wave doesn't proceed until all pass.
- **Safety net**: failed task changes remain isolated from the base; preserve the worktree for
  diagnosis. Verify real work exists (`git log` / `git diff`) before relying on a result.

## Escalate = ask the user

Anything you can't safely resolve — architecture mismatch, suspected spec violation,
unresolvable conflict, data-corruption risk — **stop and ask the user.** Don't guess; the spec
is ground truth and only the user changes it.

**Escalation is synchronous.** The orchestrator→user escalation **pauses** the run and waits for
the user's answer — it never silently hangs, fires-and-forgets, or proceeds on an assumption while
"waiting." (Subagents run in fresh sessions with no live user conversation, so they cannot ask the
user; they return their escalation through their structured result, and the orchestrator relays it
to the user synchronously.)

**Detection ≠ diagnosis.** Spotting that something broke is not the same as correctly
attributing *why*. A confident but wrong cause-attribution is possible — verify it against the
actual commands and output (not a self-report or a shallow grep) before acting destructively or
recording it as a durable fact. A misattribution that gets written down propagates.
