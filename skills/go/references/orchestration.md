# orchestration.md — wave lifecycle (force-load)

The mechanics behind the SKILL's per-wave flow: scheduling, parallel-dispatch constraints,
status handling, context budget, and failure handling. Loaded for the whole run. The wave
lifecycle is a proven scaffold — keep its structure and the safety constraints; use judgment
inside each step.

## Wave scheduling

- Topologically sort the plan's `depends` into waves: a wave = tasks with no unmet dependency.
- **Batch ≤8 concurrent.** If a wave has more than ~8 independent tasks, split into
  sub-batches (practical parallelism is ~5–8).
- Do not recompute or reorder dependencies — the producer (ready or set) owns
  the graph. If it fails to parse, has a cycle, or a `depends` names a missing task → **stop and
  escalate** (producer-side defect), never silently re-judge.

## Parallel dispatch — constraints (safety, non-negotiable; unordered)

- **Do not pass `isolation: worktree` to implementer dispatch** — omit isolation so the
  implementer runs in place, **pinned to the pre-created absolute worktree path**, and verify
  location with `git rev-parse --show-toplevel` at the subagent's start. (There is no
  `isolation: none` value to set — the orchestrator owns worktree creation; letting the dispatch
  tool create its own `isolation: worktree` silently loses the commit, and an unpinned subagent
  leaks edits into the main checkout.)
- **Create worktrees serially** — concurrent `git worktree add` contends on `.git/config.lock`.
- **Task worktrees do not contain the 3-doc.** `dryforge/` is gitignored, so a freshly-added task
  worktree (a clean checkout of the feature branch) has **no** `spec.md` / `plan.md` / `handoff.md`
  in it. Pass every spec slice, task contract, and hard gate **inline in the subagent prompt** — and
  never instruct an implementer or reviewer to *read* `dryforge/…` from its worktree (the file isn't
  there). The orchestrator's own copy, in the feature worktree, is for the orchestrator; the task
  subagents get what they need through their prompt.
- **Verify the work before merging (objective, not existence-only)** — the task branch must be
  strictly *ahead* of the feature branch (`git rev-list feature..task` non-empty) AND its diff
  non-empty and touching the task's declared targets; never trust the subagent's self-report. (A
  bare "a commit exists" can pass even when the subagent ran in the wrong checkout.) Compute the
  "touches its targets" diff against the **merge-base** — `git diff feature...task` (**three-dot**),
  not two-dot `git diff feature task`: once earlier tasks in the wave have merged, the feature tip
  has moved, and a two-dot diff surfaces those siblings' files and muddies the check.
- **Restore the orchestrator's cwd after each wave** — subagent runs can drift it.
- **Subagent output is bounded** — instruct large results to a file + a digest, not inline.
- **Practical parallelism ~5–8** — reflected in the batch size above.
- **Don't disable the build cache or daemon** for isolation's sake (e.g. a build tool's
  daemon-off or cache-off flags). Warm it once and share it across worktrees; tearing it down forces
  a full recompute every wave.
- **Share dependencies; don't reinstall per worktree.** A task worktree needs the *source*
  isolated, not the dependency tree (that's immutable). Instead of installing deps in each
  worktree, share the warm dependency store — symlink/reflink the external/third-party deps —
  but **relink workspace-internal packages to *this* worktree's own source** (a blanket
  symlink of the whole dependency directory makes a workspace's own packages resolve to the wrong
  tree, so a parallel edit wouldn't be seen). The payoff is mostly **disk** under high parallelism;
  the time payoff is large only when per-worktree install is genuinely expensive (cold store, heavy
  install-time hooks, daemon-off recompute) — when the package manager already shares a global store,
  install is cheap and disk is the win. **Caveat — path-mapping / project-graph monorepos**
  (workspace tools that resolve internal packages via a project graph or path aliases): even
  careful relinking often fails to resolve in a fresh worktree, so a per-worktree install from the
  warm store is the safe default there; don't force symlink sharing. **Cleanup caveat (bit us in
  dogfooding):** a dependency-store *symlink* you create for sharing is itself an **untracked
  symlink**, and a trailing-slash ignore pattern (`<dir>/`) does **not** match it (that form matches
  a real directory, not a symlink of that name) — so it silently **blocks the mandated safe `git
  worktree remove`**. Two parts: (1) ignore it with a **slash-less** pattern (`<dir>`, which matches
  both a real dir and a symlink); (2) at cleanup, treat the share-symlink as the orchestrator's
  *own* expected artifact — remove the symlink first, then safe-remove the worktree (this is not
  `--force`-ing away unreviewed work).
- **Worktrees isolate *files*, not *runtime*.** Shared external resources — DB, cache, queue,
  ports — are shared across all tasks *and* with the original project (same containers). Treat
  any command that can mutate them as dangerous even when it looks read-only (e.g. a
  `--shadow-database-url` that resets its target); never point one at the real/shared store. On
  unexpected state drift in a shared resource, **stop and escalate** — don't run destructive
  recovery on a guess.
  - **Declared shared-resource expectations.** A task spec may declare what state a shared
    external resource must be in for the task to run — *clean-slate* (must start empty/reset),
    *state-agnostic* (works against any state), *additive-only* (may add, must not mutate/remove
    existing), or *forbidden-mutations* (named operations the task must never perform). When the
    implementer finds the resource in an unexpected state versus its declared expectation, it
    returns **BLOCKED** with the specifics (what it expected, what it found). When an implementer
    returns **DONE_WITH_CONCERNS** about shared-resource state, the orchestrator **inspects the
    actual state against the declared expectation** before deciding between retry-with-clean (reset
    the resource, re-dispatch) and escalate — it does not guess.
  - **Ordering / external-state deps.** Beyond file-collision, tasks may be ordered by a runtime
    sequence (one must run before another) or by external shared-state initialization (a migration,
    a seed, a registered fixture). Go honors explicit `depends` for these and **serializes declared
    external-state writers**; it does not infer them — the producer discovers them (see
    `dependency-calc.md`).

## Agent status protocol

Each implementer returns one status:

| Status | Meaning | Orchestrator response |
|---|---|---|
| `DONE` | complete, self-checks pass | spec-review → merge |
| `DONE_WITH_CONCERNS` | complete, but flags something | record the concern; spec-review; weigh at code-review |
| `NEEDS_CONTEXT` | missing info to proceed | provide the missing context, re-dispatch |
| `BLOCKED` | cannot proceed (conflict, ambiguity) | analyze; walk the bounded escalation ladder (below), then **escalate to the user** |

**Bounded escalation ladder** (for `BLOCKED` / `NEEDS_CONTEXT`): **attempt 1** — re-dispatch with
more context (the missing slice, the resolved ambiguity); **attempt 2** — re-dispatch with an
upgraded model; if it is **still BLOCKED**, **escalate to the user** with full context: what was
tried, what each attempt produced, and why it failed. The budget is bounded — do not loop
re-dispatching past the ladder.

## Context budget

- **Resident**: the 3-doc (~1–3K) + wave schedule + accumulated per-task summaries
  (~100–200 tokens each) + spec-review verdicts (~20 tokens each).
- **Temp-load → use → drop**: authoring an implementer prompt (the relevant plan+spec slice),
  analyzing a failure (the error output). Drop after the judgment.
- Keep raw diffs out of the orchestrator — spec review runs in the subagent's context.
- **Watch retry bloat**: temp-loads have per-item caps but no total cap; repeated failures can
  swell the orchestrator. Compress to summaries and drop promptly.

## Per-wave step order (and why)

After all tasks in a wave return `DONE` and pass **spec-review** (`spec-review-prompt.md`):

> **spec-review is a dispatched subagent, never inline.** Do not substitute an orchestrator
> `git show` / diff read — that reverts the raw diff into the orchestrator (context-budget
> violation) and loses review independence. **Invariant: before a wave merges, N tasks ran N
> spec-reviews.** This is the *spec-first* half of spec-first 1+1; skipping it silently halves
> the review model.

1. **Merge serially** into the feature branch (commit-existence verified first). **The merge
   commit message must satisfy the project's commit-msg hooks** (a commit-message linter, a secret
   scanner, …) — many
   repos reject a non-conventional message (e.g. a bare `merge T1: …`), which leaves the merge
   *incomplete*. Use the project's commit convention (discovered in GATHER / from config), and if a
   hook rejects the merge, treat it as a blocking step, not done. **Recovery (diagnostic-first,
   floor not ceiling):** inspect the rejecting hook's name and its full output, verify branch
   state with `git log` (did the merge commit land or not?), and retry with the GATHER-discovered
   commit convention; if it still rejects, escalate with the hook name, the error, the message you
   attempted, and the branch state — don't blindly reword and re-fire.
2. **Regen barriers** — run the plan's `regen_barriers` whose `after` is now satisfied. **If a
   barrier writes files a later task consumes, commit that regenerated output on the feature branch**
   (same reason as the wiring commit below): the regen runs in the feature worktree, but a later
   wave's task worktree is a fresh checkout of the *committed* feature tip — an uncommitted (or
   gitignored) regen artifact won't be there, so the downstream task imports/builds against a missing
   file. If the artifact is deliberately ephemeral (nothing downstream reads it), leave it; the test
   is "does a later task depend on it?" — if yes, commit it (and make sure it isn't gitignored).
   **Recovery (floor not ceiling):** if a barrier exits non-zero or produces conflicting output,
   capture the command + exit code + stderr, then analyze whether a *prior merge in this wave broke
   a precondition* the barrier relies on (a moved file, a renamed symbol, a changed schema). If the
   barrier's regenerated output would *overwrite* files a task already merged, do not let it clobber
   — escalate with the command, the output, and which merged files it would overwrite.
3. **Deferred wiring** — the single writer appends all shared registrations for the wave
   (feature tasks left these alone; this avoids parallel collisions on shared files), **applied
   idempotently** (check-before-append, so a partial-wave retry does not double-register;
   conflicting registrations → escalate). **A wiring conflict** = the same key / route / export /
   identifier is registered twice, or registered incompatibly by two tasks (one key, divergent
   targets). On a conflict, capture the file + the conflicting lines + the involved tasks and
   **escalate — never auto-pick a winner** (the spec, not the orchestrator, decides which
   registration is correct). **Then commit the wiring edits on the feature branch**
   (`git add` the specific wiring files + a hook-satisfying message) — this is mandatory, not
   optional. The wiring is written in the feature worktree, but **uncommitted edits do not travel**:
   the next wave's task worktrees branch from the *committed* feature tip, and the final `--no-ff`
   merge to main carries only committed history — so an uncommitted wiring is silently dropped from
   both, while every gate below (run in this same worktree, where the edits are still on disk) shows
   a false green. Commit it so the gate, the next wave, and main all see the same state.
4. **Integration gate** — run **the project's verify commands** (discovered in GATHER — may be a
   typecheck/lint/test set, a build/run, or a single command; not every stack has all three) on the
   merged result, **after** wiring is committed (step 3); **green = those commands exit 0, output
   captured** (per-task self-checks don't guarantee combined correctness). For a compiled stack the
   build/compile is the primary gate and runs here every wave. Gating the *committed*
   state — not uncommitted working-tree edits — is what makes the green trustworthy.
   **If GATHER returned ZERO verify commands, "green" must not be left undefined** — it degrades
   to a user-provided custom check, named human-approval evidence, or an explicit "no automated
   gate" recorded decision. Go does not invent a gate; it honors whatever the 3-doc records (the
   producer surfaces this), and the absence of a gate is itself a recorded decision, not silence.
   **Verify scope:** per-wave **FULL verify is the safe baseline.** Affected-only verification
   (verify the changed files + their static dependents each wave, with a full verify at completion)
   is an **OPTIONAL orchestrator mode**, valid only WHEN GATHER discovers the project supports
   filtering — a test selector or an affected-graph command that is *discovered, never assumed*
   (see `develop/research/008-parallel-isolation-provisioning.md`). Absent such a tool, full verify
   every wave.
5. **Code review** — once the gate is green, a per-wave quality reviewer (`reviewer-prompt.md`)
   checks the merged result; **clear = zero blocking findings**; fix-dispatch any blocking issue.
6. **Clean up** the task worktrees — but **only after** asserting each task commit is an ancestor of
   the feature branch (`git merge-base --is-ancestor`); if a merge silently didn't take, do not
   remove — escalate. Avoid `--force`/`-D`. Then proceed to the next wave.

**The merge→regen→wiring→gate→review→cleanup sequence above is the correctness ordering and does
not change.** But it splits into three streams that may *overlap in wall-clock time* without
violating that ordering:

- **Stream A (serial, on the critical path):** merge → regen barriers → deferred wiring →
  **COMMIT on the feature branch** (steps 1–3). These mutate the feature branch and MUST stay
  ordered.
- **Stream B (after A commits):** the integration gate + per-wave code review (steps 4–5), run on
  the committed feature tip.
- **Stream C:** provisioning of the *next* wave's task worktrees (`git worktree add` off the
  committed feature tip + dependency share) **MAY begin as soon as Stream A has committed** — it
  does **not** wait for Stream B to clear. This reclaims idle provisioning time only.

**Feature-tip lock + refresh.** Next-wave worktrees branch from the *gate-passing committed tip*.
If Stream B surfaces a fix, the fix-dispatch **acquires the feature-tip lock**, and any next-wave
worktrees already created by Stream C are **refreshed** (rebased onto / recreated from) the new tip
before any next-wave dispatch.

**Advisory findings are recorded, never dropped.** Code-review findings that are *not*
fix-dispatched must be recorded and **explicitly marked accepted** (signed off) before the next
wave starts — they are never silently dropped once Stream C has provisioned ahead.

This overlap is an **OPT-IN latency optimization.** If the lock/refresh bookkeeping is uncertain
for a run, **fall back to fully serial wave advance** (today's behavior) — provisioning the next
wave only after the gate is green and review is clear. The overlap is never a correctness hazard:
it only ever reclaims idle provisioning time.

**Single-task wave (parallelism=0).** When a wave is one task with no shared-write declared,
**per-wave code-review is skipped** (folded into the completion-time review) and the
**deferred-wiring decision is inlined** — there are no parallel siblings to collide on a shared
file, so the single writer's registrations can go in directly. **spec-review, the integration
gate, and the completion review are never skipped.**

A wave does **not** advance until every task passes, the gate is green, and code review clears.
**Provisioning (Stream C) may overlap** — it may start once Stream A has committed. **Dispatch of
the next wave still waits** for a green gate + cleared review, so a broken wave never has work
built on top of it.

**The orchestrator does not edit task code directly.** Bugs and review findings go through
**fix-dispatch** (a subagent). The *only* direct orchestrator write is the deferred-wiring step
(3) — the single-writer shared registrations that are its own job. (A small fix done inline
still leaks the diff into the orchestrator and skips independent review.)

**Where a fix-dispatch runs (pin it, or the fix lands nowhere).** A fix-dispatch is run like a
task: in a worktree on a branch off the **feature** branch — reuse the relevant task's worktree if
it is still present (pre-cleanup), else create a fresh fix worktree off the feature branch. The
subagent commits its fix there; the orchestrator then **merges that branch back into the feature
branch** under the same merge-gate (strictly ahead, touches the intended targets, hook-satisfying
message). A fix committed only in a stray worktree, or applied to the integrated tree without a
merge back to feature, is silently lost — pin the worktree path the same way implementer dispatch
does.

## Failure handling

| Failure | Response |
|---|---|
| `BLOCKED` / `NEEDS_CONTEXT` | walk the bounded ladder: attempt 1 more context → attempt 2 upgraded model → escalate |
| max retries exceeded | **escalate to the user + preserve the worktree for manual recovery** (do not discard) |
| spec-review fail | re-dispatch with the specific fix |
| merge conflict | analyze; resolve if mechanical / same-intent, else escalate |
| merge commit-msg hook rejection | inspect hook name + full output; verify branch state (`git log`); retry with the GATHER-discovered commit convention; else escalate with hook name + error + attempted message + branch state |
| regen-barrier non-zero / conflicting output | capture command + exit + stderr; analyze whether a prior merge broke a precondition; if it would overwrite merged files, escalate |
| deferred-wiring conflict | capture file + conflicting lines + involved tasks; escalate (never auto-pick a winner) |
| integration gate fail | analyze → identify the causing task → fix-dispatch |
| code-quality issue | fix-dispatch |
| architecture mismatch / suspected spec violation / data-corruption risk | **stop and escalate** |

- **Partial wave failure — cleanup order + retry semantics**: keep the merged successful tasks.
  **Preserve the failed task's worktree for diagnosis** (do not clean it). **Clean up only the
  successful worktrees**, and only after the ancestor check (`git merge-base --is-ancestor`).
  **Never delete the feature branch.** On retry, create a **FRESH worktree branched from the
  CURRENT feature tip** — which now includes this wave's already-merged successes (the feature tip
  advances per merge), so the retry builds on the integrated state, not the stale pre-wave tip. The
  wave doesn't proceed until all pass.
- **Safety net**: worktree isolation means a discarded failed task never affects the feature
  branch. Verify real work exists (`git log` / `git diff`) before relying on a result.

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
