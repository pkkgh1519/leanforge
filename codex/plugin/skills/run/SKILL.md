---
name: run
description: >
  Execute a refined 3-doc (handoff, spec, plan) produced by Prime:
  wave-based parallel implementation with right-sized verification (test-first where it fits),
  spec-first review, and integration gates. Use when the user invokes the `Run` skill after `Prime` wrote the 3-doc. Requires git.
---

# Leanforge:Run

> **Reply in the user's language from the first line and keep it throughout.** Write natively; the
> language of the 3-doc, codebase, or these instructions never overrides the user's language.

Consume the **approved 3-doc** produced by `Prime` and realize the spec through dependency-aware
waves, right-sized verification, spec-first review, and integration gates. Run in the same session as
Prime when possible; the self-contained 3-doc—not dialogue—is execution authority. Force-load
`references/orchestration.md`. Force-load `references/harness-lifecycle.md` before any state-directory
compatibility or interrupted-run decision and reuse it at the harness step; load prompt references at
their dispatch steps.

## Core principles

- **Follow the Execution Graph.** The producer owns `depends` and `regen_barriers`; do not invent,
  remove, or reorder them. A malformed graph is a producer-side defect and blocks.
- **Serve the spec.** Correct means spec-conformant. Spec beats plan, code, and convention; suspected
  spec error or conflict returns to the user rather than being silently repaired.
- **Escalate, do not guess.** Ambiguity, architecture mismatch, `NEEDS_CONTEXT`, `BLOCKED`, conflict,
  or data risk pauses the run while the orchestrator asks the user. Children never ask directly.
- **Protect main; prove results.** Existing projects stay on a feature branch until user-approved
  integration; greenfield may use main. Captured commands, output, and exit codes—not self-report—pass
  gates. The lifecycle is a floor, not a ceiling.
- **Use children only when they earn their cost.** The orchestrator handles ordinary sequential
  `MECHANICAL`/`NONE` work directly. Parallel file work, a single `RISKY` task, and independent review
  use children as defined in `orchestration.md`.
- **Explicit isolated dispatch.** Every child is a non-delegating leaf. On Codex, every child creation
  sets `fork_turns: "none"` explicitly; never omit it or use `"all"`. Apply `orchestration.md`'s
  action-local live-slot admission before every slot-consuming dispatch or idle-child reactivation.
  Dispatch every implementer and reviewer as a general-purpose child with full read/edit/run tools,
  never a plan-only or search-only role; reviewer prompts still impose read-only behavior where required.
- **Repo-local lenses are optional aids.** Use matching harness-generated artifacts only as
  review/explore/checklist lenses under `repo-lens-routing.md`; they never replace Run or implement.
- **Own conformance upstream.** Implement and verify as if the final review did not exist. The final
  review is independent insurance for rare residuals, not permission for shallow work.
- **Report results, not plumbing.** Speak only for a needed question, real blocker, wave completion,
  or final result. Keep routine reading, writing, dispatch, merge, gates, and cleanup silent and use
  plain language without internal labels or tool narration.

## Input and preconditions

- **Input.** Load `.leanforge/handoff.md`, then `spec.md`, then `plan.md`. If `.leanforge/` is absent
  but legacy `.dryforge/` exists, apply `harness-lifecycle.md`'s guarded compatibility migration before
  reading the documents.
- **Git required.** If needed, offer `git init` plus an initial commit. Stop if Git is unavailable.
- **Interrupted-run preflight.** Inspect `.leanforge/run.json` separately from `status.json` before
  first-cycle/delta classification. An active marker is an interrupted Run even when `status.json` is
  absent; do not overwrite it or regenerate the Foundation. Verify its recorded 3-doc hashes and Git
  facts; any mismatch stops for user resolution. Ask the user whether to resume or abandon the run,
  and only after an explicit resume choice continue work that filesystem and Git evidence make safe.
  The marker is advisory: actual artifacts and Git state decide. A completed/abandoned stale marker
  may be cleaned after normal checks. If `.leanforge/` is absent and legacy `.dryforge/run.json` is active or
  `.dryforge/worktrees/` exists, resolve that run before migration.
- **Base determination.** Identify the main branch from repository evidence or ask—never guess. Require
  no unpushed main commits and no modified/staged tracked files. Greenfield uses main; an existing
  project creates `Leanforge/<feature>` from main. Untracked `.leanforge/` producer output is expected;
  other foreign work blocks. On the base, add `.leanforge/` and `.dryforge/` to `.gitignore` and commit;
  if either state directory is tracked, remove it from the index before continuing.
- **Verify commands.** Resolve build/test/lint commands from handoff hard gates and project scripts
  before the first wave.
- **Read authority in order.** Handoff governs roles, hard gates, and execution shape; spec governs
  behavior; plan governs task contracts and graph order. On first cycle, a missing Project Foundation
  blocks before implementation: stop and ask the user to regenerate the 3-doc through `Prime`. Treat
  Foundation as non-executable durable context and a harness
  source—not an implementation target or execution authority. Do not infer work, constraints,
  abstractions, extension points, or compatibility steps from it. Build only present-tense spec
  requirements and handoff hard gates; if a future direction legitimately constrains this slice,
  Prime has already written that narrow constraint there.

## Graph validation

Before branch/worktree mutation, parse the Execution Graph under `references/graph-contract.md`.
Require an acyclic graph, valid `depends`/`after` task IDs, and an exact plan-body/graph task-ID match.
Report the offending ID, cycle, or mismatch and require a corrected plan; leave no partial state.

## Flow

Force-load `references/orchestration.md`. Topologically derive waves and recalculate action-local live
capacity immediately before every dispatch. Follow that reference for scheduling, worktrees, status,
merge gates, wiring, verification, context budget, cleanup, and failure handling.

1. **Set up the base.** Create the feature branch when required, commit state-directory ignore setup,
   and keep active 3-doc files local. Only the orchestrator reads them; children receive the relevant
   task/spec/hard-gate slice inline. State/external-only tasks stay sequential on the base.
2. **Scaffold inline.** Establish manifests, dependencies, layout, build config, entry points, and
   shared types from approved technical decisions. Batch independent writes. Dispatch unusually large
   or investigative scaffold work only when isolation or exploration justifies it.
3. **Choose the documented execution mode.** For a single file-diff task, `MECHANICAL`/`NONE` runs
   orchestrator-direct with the same captured-evidence floor as `implementer-prompt.md`; omitted `risk`
   remains unclassified and biases toward dispatch when behavior appears; `RISKY` uses one worktree
   implementer. No-file-diff work uses a base-pinned implementer with captured external evidence.
4. **Run parallel waves in admitted batches.** Create worktrees serially under
   `.leanforge/worktrees/<task-id>`, provision only the current live-capacity batch, and dispatch one
   general-purpose leaf per task. Share dependencies safely and keep runtime resources isolated or
   explicitly ordered. Collect structured statuses; apply the bounded escalation ladder without loops.
5. **Land and verify.** Run any triggered conditional spec-review before downstream work: review a
   branch task before its merge; review collapsed or base-pinned work from the raw base diff or
   captured external evidence before dependents proceed. Then prove task commits and declared targets,
    merge serially, run regeneration
    barriers, apply deferred wiring idempotently on the base, and commit it. Parallel waves run the
    integration gate with captured output; sequential waves advance after commit verification. Preserve
    failed or ambiguous worktrees for diagnosis. Do not remove successful task worktrees or branches
    before the completion gate passes. Between waves, after the prior gate/fix is green and with base
    writes serialized, reuse only after pinning the current base-tip, binding the worktree HEAD to the
    previously verified prior task commit, proving the prior task commit is an ancestor, and creating a
    new task branch at the pinned tip. Reconfirm the base ref immediately before dispatch. Preserve
    dirty, failed, ambiguous, stale-base, or branch-collision state rather than overwriting it. If an
    intermediate gate uses
    affected-only filtering, record what it skipped; the completion gate still runs the full set.
6. **Review policy.** Default to one final full-diff review. Add a conditional spec-review only when a
   `RISKY` task has downstream dependents and deviation could cascade. Use `spec-review-prompt.md` and
   `reviewer-prompt.md`; both remain independent leaves admitted through the live-slot contract.

**After all waves:**

7. **Persist coarse recovery state.** At durable milestones, atomically update `.leanforge/run.json`
   with only `in_progress`, `awaiting_user_approval`, `archive_in_progress`, `completed`, or
   `abandoned`. Include `activeDocs` hashes and base branch/commit facts. Do not checkpoint every
   command; verified Git and filesystem state remain recovery truth.
8. **Completion gate.** Run the full verify set on the base. Reuse the last parallel integration result
   only when it ran the same full set successfully and the base-tip SHA has not changed. After the gate
   passes, batch-remove eligible successful worktrees and merged task branches only after proving their
   commits are ancestors of the base; preserve failed or ambiguous worktrees and branches.
9. **Create or update the project harness.** Force-load `harness-lifecycle.md` and
   `harness-format.md`, then re-read the 3-doc. First cycle creates the full harness from Foundation,
   spec, and code; delta updates only changed-scope documentation and navigation. Apply clobber guards,
   back up/rework an existing entry file only with user approval, and keep file generation silent.
10. **Final review.** One fresh leaf reviews the full base diff for spec conformance, code quality,
    evidence integrity, ceremony budget, and the harness when changed, using `harness-review.md` and
    `reviewer-prompt.md`. A clear verdict means zero blocking findings.
11. **Fix if needed.** Triage every advisory. Fix trivial non-behavioral items directly; dispatch
    substantive behavioral or structural fixes. Code changes rerun completion, harness changes rerun
    harness review, and combined changes rerun both. Record an out-of-scope mismatch rather than
    expanding the approved task silently.
12. **User gate.** Present the result for approval. On first cycle reconcile the harness with agreed
    decisions; on delta summarize harness changes. Persist `awaiting_user_approval` before pausing.
13. **Archive and mark.** On approval, atomically enter `archive_in_progress`, move the active
    `.leanforge/{handoff,spec,plan}.md` into the next `.leanforge/NNN/`, delete the root copies only
    after verifying the archive, write `.leanforge/status.json` (`{ "initialized": true }`) if absent,
    and mark the run completed.

Parallel provisioning may overlap the current integration gate, but dispatch waits for green. Fall
back to serial when overlap or capacity is uncertain.

## Completion gate

Done only when all hold on evidence:
- every planned task is complete and landed, and every wave has landed on the base; every spec
  requirement traces to a landed task, and every landed task traces to the spec;
- an open `BLOCKED` or needs-fix task must not be counted complete. Its escalation must be resolved
  with the user and its worktree preserved for diagnosis; every concern is resolved or explicitly
  accepted;
- the integrated base passes the complete verify set with commands, output, and exit codes captured
  and shown;
- when the spec declares a runnable service, a minimal runtime smoke starts it, observes a successful
  response, and stops it; an unevaluable assertion is failure, never inferred success;
- no escalation remains outstanding.

## Finish

After harness, final review, user approval, and 3-doc archiving:

- **Greenfield:** work is already on main; report completion.
- **Existing project:** ask whether to merge to main, open a PR/push, or hand off the feature branch.
  For merge, fetch and confirm main has not moved; if it moved, re-integrate or escalate. Otherwise
  merge with `--no-ff` from a checkout on main and abort/escalate on conflict. After confirming the
  merge, clean up the feature branch. Never integrate without the user's choice.
