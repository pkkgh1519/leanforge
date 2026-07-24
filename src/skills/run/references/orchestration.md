# orchestration.md — wave lifecycle (force-load)

The mechanics behind the SKILL's per-wave flow: scheduling, dispatch constraints, status handling,
context budget, and failure handling. Loaded for the whole run. The wave lifecycle is a proven
scaffold — keep its structure and the safety constraints; use judgment inside each step.

## Reporting principle

User-facing text = wave completion, blockers, final results. Internal operations (merge, gate,
worktree lifecycle, branch cleanup, dependency install) produce **no text output**. Output tokens
are direct cost.

## Verification Plan

Before the first wave, write a compact verification plan in the orchestrator's working notes:

- command set and purpose
- which commands can run independently in parallel
- which commands are cheap per-wave gates
- which commands are expensive and reserved for the completion gate unless risk demands earlier use
- whether the project supports affected-only filtering for intermediate gates

The plan prevents re-deciding verification every wave. Independent commands may run in parallel as
long as each exit code is captured separately. The completion gate remains the full safety net.

## Wave scheduling

- Topologically sort the plan's `depends` into waves: a wave = tasks with no unmet dependency.
- **Classify each wave:** multiple tasks = **parallel** (worktrees). Single task = **sequential**,
  whose execution mode is set by the task's `risk`:
  - **`MECHANICAL` / `NONE`** → the **orchestrator implements directly on the base** (no worktree, no
    dispatch, no integration gate) — commit on the base, **verify with captured evidence** (same floor
    as a dispatched implementer: command + captured exit code; real testable behavior left untested =
    not done), advance. **You own conformance here — the final review is insurance, not your check.**
  - **Omitted `risk`** → the producer did *not* judge; treat it as **unclassified, not `MECHANICAL`** —
    judge at read time and bias toward dispatch / stronger verification if it shows any behavioral
    surface (degrade-don't-corrupt).
  - **`RISKY`** → **dispatch one subagent in a worktree** + merge-gate (independent verification, A=A
    avoidance; the merge-gate protects the base from risky work). This is the parallel-wave machinery
    with a single task — the final review must not be the *only* independent check on risky work.
  - A **no-file-diff** task always uses the base-pinned-subagent path (next bullet), regardless of risk.
- **Parallel wave:** task worktrees branched from the base; dispatch in action-local runtime-capacity
  batches. Integration gate after merge catches cross-task interactions.
- **ROI collapse (objective conditions, not a free judgment).** A multi-task wave defaults to parallel
  worktrees. Collapse to **orchestrator-direct on the base** **only** on an objective condition — a
  **single shared runtime** the tasks cannot isolate within (one DB / container stack / port set), or a
  **greenfield** codebase where cross-agent convention drift outweighs the parallelism. This is a *rule*,
  not a free "ROI doesn't pay" call. **Record the collapse internally** (which wave, which condition) —
  do **not** surface it for a non-technical user to adjudicate (they cannot evaluate a parallelism/
  isolation trade-off, and the terms are internal tokens). Collapsed tasks carry the per-task evidence
  floor and are **reviewed as if independently authored** — collapse removes dispatch overhead, never the
  verification bar. **Collapse does NOT skip the cascade-guard:**
  the conditional mid-run spec-review still fires for any task meeting its narrow bar — **RISKY +
  downstream dependents + deviation-cascade risk** — even when implemented inline. Collapse saves
  dispatch / worktree / merge / per-wave-gate overhead, **not** that targeted guard. (RISKY alone
  never triggers a spec-review — it only sizes test ceremony — so "more RISKY" ≠ "more spec-reviews",
  and collapse stays cheap.)
- **No-file-diff tasks stay off the worktree path.** A task whose declared work targets are
  **state / external only** — its result lives *outside* the tree (a DB migration run, an external
  config applied, a remote registration), so it produces **no file diff** — is handled on the
  **base sequentially** (a base-pinned implementer; verified by commit message + captured external
  evidence per `implementer-prompt.md`), **never dispatched into a parallel worktree.** Two reasons:
  the parallel **merge-gate is file-diff-based** (`git diff base...task` must touch declared targets)
  and would reject its empty file diff; and a worktree isolates *files*, not the external runtime it
  mutates, so parallel isolation buys nothing while costing worktree + dispatch overhead. If
  topological sort places such a task in a multi-task wave, **peel it off** and run it on the base
  before/after the worktree batch — do not put it in the pool. (Recognize it from the plan's work
  targets: files | state | external — a task with no `files` target is this case.)
- **Live-capacity contract.** Immediately before each slot-consuming dispatch action, calculate from
  host-advertised live state:

  ```text
  free_slots = max(0, runtime_total_slots - active_slot_consumers)
  batch_size = min(ready_dispatchable_tasks, free_slots, explicit_user_limit_or_infinity)
  ```

  Count the root and every running child that consumes a runtime slot. Recalculate after every
  collection, interruption, completion, or dispatch; never cache capacity. A lower user limit remains
  binding. Choose exactly one host path below; never mix or emulate another host's tools.
  - **Codex.** Immediately before each dispatch or eligible idle-child reactivation, call `list_agents`.
    At zero free slots, call `wait_agent` once and then call `list_agents` again. No state change or a
    second zero-slot result blocks rather than waiting indefinitely. If total capacity is unavailable,
    degrade to **one child at a time**. A list failure gets one bounded retry, then blocks. Only fresh
    admission permits `spawn_agent` or an eligible `followup_task`; `send_message` to a running child
    and `wait_agent` do not consume a new slot or permit retasking. A capacity race rejection gets one
    wait/re-list retry. A second capacity rejection or no state change reports capacity exhaustion and
    blocks. An idle implementer may use `followup_task` only when its immediately preceding status was
    `NEEDS_CONTEXT` or `BLOCKED` and the bounded retry keeps the same graph task, unchanged task
    contract, same role, and same pinned work location. A different task or role, a changed task
    contract or work location, any review or re-review, `DONE` or `DONE_WITH_CONCERNS`, a fix-dispatch,
    and the upgraded-model attempt require a fresh child.
  - **Claude Code.** Use only live capacity or child-state signals exposed by the host and dispatch via
    `Agent`. If total capacity or a separate preflight signal is unavailable, admit **one child at a
    time**. At zero capacity or on a capacity rejection, wait for a running child result, refresh once,
    and block on no state change or a second rejection. A prior implementer may continue only when its
    immediately preceding structured status was `NEEDS_CONTEXT` or `BLOCKED` and the bounded retry keeps
    the same task, unchanged contract, same role, and same pinned work location. Every review,
    re-review, upgraded-model attempt, changed task, contract, role, or work location, `DONE` or
    `DONE_WITH_CONCERNS`, and fix-dispatch starts a fresh child.
  Slot pressure may delay an independent review but never replace it with self-review.
- **Fresh leaf children.** Every Codex child creation sets `fork_turns: "none"` explicitly; never omit
  the field or use `"all"`. Children receive only task-local inputs and may not delegate or spawn.
- Do not recompute or reorder dependencies — the producer owns the graph. Parse failure / cycle /
  dangling `depends` → **stop and escalate** (producer-side defect).

## Dispatch ROI checklist

Before spawning any subagent, ask whether the dispatch buys at least one of:

- physical file isolation for parallel writes
- independent review perspective for risky/spec-sensitive work
- meaningful context isolation for broad exploration or log/diff analysis
- wall-clock speed from truly independent work

If none apply, keep the work inline. Inline work still needs a commit and **captured evidence**, and
you **own its conformance** — the final review is insurance, not your check. The optimization removes
dispatch overhead, never the verification bar.

## Sequential wave — execution

A single-task wave runs in one of three modes (by `risk` + target type; see Wave scheduling).

- **Orchestrator-direct** (`MECHANICAL` / `NONE`, file-diff task; omitted only after read-time
  judgment confirms the task is mechanical). Omitted `risk` remains unclassified, not `MECHANICAL`;
  first judge the task at read time and bias toward dispatch / stronger verification if any
  behavioral surface appears. The orchestrator
  implements directly on the base — it reads the task's behavioral contract + spec slice itself (no
  prompt authoring, no dispatch), writes the code, runs right-sized verification (capturing command +
  exit code), and commits on the base. No worktree, no dependency install, no integration gate, **no
  implementer status protocol** — the orchestrator knows its own state. If the task turns out
  ambiguous, behavioral, multi-file, or riskier than declared, treat it as a **runtime risk upgrade**
  (`graph-contract.md`): strengthen verification (conditional spec-review or final-review focus); do
  not silently push on. **Keep the sawtooth** — load the task's files, work, commit, drop what the
  next task won't need.
- **Subagent in a worktree** (`RISKY`, file-diff task). The parallel-wave machinery with one task:
  create a worktree off the base, dispatch one implementer (pinned to the worktree absolute path; omit
  `isolation: worktree`; verify with `git rev-parse --show-toplevel`), collect its structured
  summary, then **merge-gate** into the base (strictly ahead + diff touches declared targets).
  Independent verification is the point.
- **No-file-diff task (any risk) — base-pinned subagent.** Dispatch one implementer pinned to the
  **base** directory (omit `isolation: worktree`); it commits on the base. Verification is the
  **commit message + captured external evidence** (command exit / render / API or state response),
  not a file diff. (A worktree would isolate files, not the external runtime it mutates, and the
  file-diff merge-gate can't verify it.)

**Both dispatched modes:** verify the commit after return (`git log`; for file-diff, the diff touches
declared targets — never trust self-report); **restore the orchestrator's cwd** (subagent runs can
drift it); **subagent output is bounded** (large results → file + digest). **No integration gate** for
a sequential wave — the self-checks run on the cumulative base (which already includes all prior
waves); with a single task cross-task interaction risk is zero, and the completion gate catches
cross-wave interactions at the end.

## Parallel wave — dispatch constraints (safety, non-negotiable; unordered)

- **Do not pass `isolation: worktree` to implementer dispatch** — omit isolation so the
  implementer runs in place, **pinned to the pre-created absolute worktree path**, and verify
  location with `git rev-parse --show-toplevel` at the subagent's start.
- **Create worktrees serially, under `.leanforge/worktrees/`.** Each task worktree lives at
  `.leanforge/worktrees/<task-id>` — inside the gitignored `.leanforge/`, so worktrees never sprawl into
  the project tree or get tracked, and cleanup stays contained. Concurrent `git worktree add` contends
  on `.git/config.lock` → create serially. **Worktree pool:** after live-capacity admission, create or
  grow the pool only to the current `batch_size`; never provision work that cannot be dispatched. If
  capacity later grows, grow lazily. Between waves, reuse only a clean pooled worktree whose prior work
  safely landed. After the prior wave's gate/fix is green, serialize base writes through the next
  handoff and pin the current base-tip SHA. Before assigning the worktree to another task, require an
  empty `git status --porcelain`; capture its current HEAD with `git rev-parse HEAD`, require it to equal
  the previously verified `<prior-task-tip>` from the merge gate, and prove that tip landed with
  `git merge-base --is-ancestor <prior-task-tip> <current-base-tip>`, and require that the new task
  branch name is absent. Then create and switch to it from the pinned tip with
  `git checkout -b <new-task-branch> <current-base-tip>`. Immediately before dispatch, confirm the base
  ref still resolves to `<current-base-tip>`; any failed check or mismatch blocks and preserves the
  worktree, and never force-reset or overwrite it. Defer removal until after the completion gate
  passes; then clean up all eligible successful worktrees and merged task branches in one batch (not
  per-wave), after proving each landed commit is an ancestor of the base. Remove dependency-share
  symlinks, safe-remove each eligible worktree without `--force`, then delete its merged task branch
  with `git branch -d`. Preserve dirty, failed, ambiguous, stale-base, or branch-collision worktrees and
  branches as reported diagnostic recovery state. Remove the now-empty `.leanforge/worktrees/`
  directory and task scratch/temp dirs only when no diagnostic recovery state remains. **Leave no
  disposable litter** — in that case, once the run finishes (3-doc moved into `NNN/` at archiving),
  `.leanforge/` holds only `NNN/` archives, `status.json`, and `backup/` (the active 3-doc lives at the
  root only between the producer writing it and archiving). This avoids repeated create/remove cycles
  and a cluttered `.leanforge/`.
- **Task worktrees do not contain the 3-doc.** `.leanforge/` is gitignored, so a freshly-added task
  worktree has **no** `spec.md` / `plan.md` / `handoff.md`. Pass every spec slice, task contract,
  and hard gate **inline in the subagent prompt**.
- **Verify the work before merging (objective, not existence-only)** — the task branch must be
  strictly *ahead* of the base (`git rev-list base..task` non-empty) AND its diff non-empty and
  touching declared targets — checked with **three-dot** diff (`git diff base...task`).
- **Restore the orchestrator's cwd after each wave.**
- **Subagent output is bounded.**
- **Parallelism follows the live-capacity contract above; never substitute a fixed numeric range.**
- **Don't disable the build cache or daemon.** Warm it once and share across worktrees.
- **Enable incremental / caching mode at scaffold** when the project's build or verify tools
  support it but default to off. Check the tool's config or documentation during scaffold setup;
  if an incremental or cache option exists, enable it. Repeated verify runs (per-wave gates,
  completion gate) benefit from warm caches. This is the orchestrator's scaffold responsibility,
  not a per-task concern.
- **Share dependencies; don't reinstall per worktree.** Symlink/reflink external deps; relink
  workspace-internal packages to this worktree's own source. **Caveat — path-mapping monorepos:**
  per-worktree install from the warm store is the safe default; don't force symlink sharing.
  **Cleanup caveat:** a dependency-store symlink is untracked; ignore it with a **slash-less**
  pattern (`<dir>`, not `<dir>/`); remove the symlink before safe-removing the worktree.
- **Slash-less gitignore — verify at scaffold, before any worktree.** After scaffold commits,
  confirm `.gitignore` uses slash-less patterns for dependency directories (the project's dependency
  store directory, without a trailing slash). A trailing-slash pattern does not match a symlink, so
  worktree dependency symlinks get staged by `git add`. Fix this **before** creating the first
  parallel wave's worktrees — every worktree agent will otherwise hit the same papercut
  independently.
- **Worktrees isolate *files*, not *runtime*.** Shared external resources (DB, cache, queue, ports)
  are shared across all tasks. Treat mutations as dangerous; on unexpected state drift, **stop and
  escalate**.
  - **Declared shared-resource expectations** (clean-slate / state-agnostic / additive-only /
    forbidden-mutations) are honored per the producer's dependency-calc rules.
  - **Ordering / external-state deps** — `Run` honors explicit `depends` and serializes declared
    external-state writers.
  - **Name agent-created ephemeral resources deterministically.** When a task (or scaffold) spins up
    an external runtime resource that takes a name — a container, a service instance, a database
    schema, a namespace, a temp queue — derive the name from a stable identifier (project +
    task/wave id), **never a random name.** Random names leak (the orchestrator can't find them to
    clean up) and risk silent collisions across parallel tasks sharing the runtime. *What* needs a
    name is discovered from the project (stack-agnostic); the rule is deterministic-not-random, and
    tear the resource down when its task/wave completes.

## Agent status protocol

Each **dispatched** implementer returns one status (orchestrator-direct sequential work has none —
the orchestrator knows its own state):

| Status | Meaning | Orchestrator response |
|---|---|---|
| `DONE` | complete, self-checks pass | merge (review per policy — the single final review, or a mid-run spec-review if it triggers) |
| `DONE_WITH_CONCERNS` | complete, but flags something | record the concern; weigh at final review (or mid-run spec-review if review policy triggers it) |
| `NEEDS_CONTEXT` | missing info to proceed | provide the missing context, re-dispatch |
| `BLOCKED` | cannot proceed (conflict, ambiguity) | analyze; walk the bounded escalation ladder (below), then **escalate to the user** |

**Bounded escalation ladder** (for `BLOCKED` / `NEEDS_CONTEXT`): **attempt 1** — re-dispatch with
more context (the missing slice, the resolved ambiguity); **attempt 2** — re-dispatch with an
upgraded model; if it is **still BLOCKED**, **escalate to the user** with full context: what was
tried, what each attempt produced, and why it failed. The budget is bounded — do not loop
re-dispatching past the ladder.

## Context budget

- **Resident**: the 3-doc + wave schedule + accumulated per-task summaries
  (~100–200 tokens each) + spec-review verdicts (~20 tokens each).
- **Temp-load → use → drop**: authoring an implementer prompt (the relevant plan+spec slice),
  analyzing a failure (the error output). Drop after the judgment.
- **Sequential direct execution → sawtooth.** When the orchestrator implements a `MECHANICAL` /
  `NONE` task itself, it temporarily holds that task's file context. Load → implement → commit →
  **drop**; don't carry one sequential task's files into the next.
- Keep raw diffs out of the orchestrator — spec review runs in the subagent's context.
- **Watch retry bloat**: temp-loads have per-item caps but no total cap; repeated failures can
  swell the orchestrator. Compress to summaries and drop promptly.

## Per-wave step order

> **Review policy.** Default: a single **final review** after all waves merge — one subagent
> checks the full base diff for spec conformance + code quality. Mid-run spec-review is added only
> when the orchestrator judges that a **RISKY task with downstream dependents** could cascade a
> deviation. When dispatched, spec-review is always a subagent (never inline) to preserve
> independence.

### Sequential wave (single task)

1. **Pick the execution mode by `risk`** (see Wave scheduling): `MECHANICAL`/`NONE` →
   orchestrator implements directly on the base; omitted `risk` remains unclassified, not
   `MECHANICAL`, until read-time judgment confirms the direct path; `RISKY` → a worktree subagent + merge-gate; a
   no-file-diff task → a base-pinned subagent. (Details in "Sequential wave — execution".)
2. **Verify the result without merging a RISKY branch yet** — orchestrator-direct / no-file-diff:
   verify the commit on the base (`git log`; file-diff touches declared targets; no-file-diff: commit
   message + captured external evidence). RISKY worktree: verify commit existence and the merge-gate
   preconditions (strictly ahead + diff touches declared targets). Never trust self-report.
3. **Spec review** (conditional) — complete it before a RISKY branch merges or downstream work begins.
   Review the task branch for worktree execution, the raw base diff for orchestrator-direct/collapsed
   work, or captured external evidence for a no-file-diff task.
4. **Land the RISKY branch** — after a clear conditional review (when triggered), merge-gate it into
   the base. Orchestrator-direct and no-file-diff work is already committed on the base.
5. **Regen barriers** — run barriers whose `after` is now satisfied. Commit regenerated output if a
   later task depends on it. Recovery: if a barrier exits non-zero, capture command + exit + stderr,
   analyze whether a prior merge broke a precondition; if it would overwrite merged files, escalate.
6. **Deferred wiring** — if applicable, the single writer appends shared registrations directly
   (no parallel siblings to collide). Commit on the base.
7. **No integration gate.** The self-checks ran on the cumulative base. → next wave.

### Parallel wave (multiple tasks)

1. **Verify every task branch before merge.** Confirm commit existence and the merge-gate
   preconditions: the branch is strictly ahead and its three-dot diff touches declared **file**
   targets. No-file-diff tasks never reach this path; see Wave scheduling.
2. **Spec review** (conditional) — review each triggered task branch before that branch is eligible to
   merge. A blocking verdict stops the merge and downstream work.
3. **Merge serially** into the base. The merge commit must satisfy hooks.
   Recovery: inspect hook output, verify branch state, retry with discovered convention; else escalate.
4. **Regen barriers** — same as sequential. Commit if downstream depends on it.
5. **Deferred wiring** — the single writer appends all registrations, **idempotently**
   (check-before-append; conflicts → escalate). **Commit on the base** — uncommitted wiring is
   silently lost to later worktrees and the final merge.
6. **Integration gate** — run the project's verify commands on the merged + wired base; **green =
   exit 0, output captured**. This catches cross-task interactions. Failure → fix-dispatch or
   escalate. **If the producer found zero verify commands**, the absence of a gate is a recorded
   decision, not silence. **Record the base tip SHA after the gate passes** (e.g. `GATE_SHA=$(git rev-parse HEAD)`) — the
   completion gate compares against it to avoid redundant re-runs (see SKILL.md, Completion gate). **Run verify commands in parallel** when they are independent — capture each exit code separately
   so failure attribution is clear. Wall time = max(commands), not sum. Pattern: issue all verify
   commands in a single Bash call, backgrounding each and collecting its exit code individually
   (e.g. `cmd1 & p1=$!; cmd2 & p2=$!; wait $p1; e1=$?; wait $p2; e2=$?`), then report per-command
   pass/fail.
7. **Retain or recycle** task worktrees. Reuse only clean worktrees whose landed commits are ancestors
   of the base; preserve failed or ambiguous worktrees. Successful worktrees and merged task branches
   remain until post-completion-gate batch cleanup. → next wave.

### Advancing waves

**Sequential waves advance immediately** — no gate to wait for, so the next wave can begin as
soon as the commit is verified and regen/wiring are done.

**Parallel waves:** **by default, overlap** the next wave's provisioning (worktree creation +
dependency share) with the current wave's integration gate — begin provisioning as soon as the
merge + wiring commits land, before the gate finishes. Gates are the **largest wall-clock sink**
(verify/build/container time), so overlapping provisioning with them is a real, free speedup — do it,
don't run strictly sequentially by default. The next wave's **dispatch still waits for a green gate**,
but the worktrees and dependencies are already ready. On gate failure the provisioned worktrees
are harmless (no task work yet) — remove or reuse after the fix. Fall back to fully serial advance
only if lock contention or refresh bookkeeping makes overlap unsafe. (Intermediate per-wave gates may
also use the test runner's affected-only filter; the completion gate always runs the full set.)

**Advisory findings are recorded, never dropped.** Findings not fix-dispatched must be explicitly
marked accepted — never silently dropped.

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
