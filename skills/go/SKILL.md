---
name: go
description: >
  Execute a refined 3-doc (handoff, spec, plan) produced by ready or set:
  wave-based parallel implementation with right-sized verification (test-first where it fits),
  spec-first review, and integration gates, in a fresh session. Use when the user runs /dryforge:go
  after a producer wrote the 3-doc. Requires git.
disable-model-invocation: true
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion
---

# go

Consume the **3-doc** a producer (ready or set) wrote and realize the spec:
parallel, wave-based execution with right-sized verification (test-first where it fits), spec-first
review, and integration gates. Runs in a fresh session (S2) — the 3-doc is the only source of truth. **Load `references/orchestration.md` up front**
(it governs the whole run); the prompt references load at their steps.

## Core principles (apply throughout)

- **Follow the plan's Execution Graph; never re-judge dependencies.** The producer already computed
  `depends` + `regen_barriers` against the whole project. Derive waves from it — do not invent,
  drop, or reorder dependencies. (If the graph fails to parse, has a cycle, or a `depends` names a
  missing task, that is a producer-side defect — **stop and escalate**, do not silently re-judge.)
- **Serve the spec.** "Correct" = matches the spec. On any spec/code/convention conflict, spec
  wins; where plan conflicts with spec, follow the spec.
- **escalate-don't-guess.** Architecture mismatch, suspected spec violation, ambiguous task,
  unresolvable conflict → stop and **ask the user**; never guess. When a task returns
  `NEEDS_CONTEXT` / `BLOCKED`, the orchestrator escalates to the user **synchronously** — the run
  pauses until the user responds, never a silent hang or a timeout-drop. The subagents themselves
  never call `AskUserQuestion` (their prompt files carry that fresh-session rule); only the
  orchestrator relays escalations to the user.
- **Protect main; evidence over self-report.** Never modify main outside the final user-approved
  merge. Gates pass on captured command exit codes, not on an agent's "looks fine."
- **Floor, not ceiling.** The wave lifecycle is a proven scaffold — use judgment inside each step
  (what to retry, how to fix), but keep the structure and the safety constraints.

## Input & preconditions

- Invocation: `/dryforge:go`. Load the 3-doc (handoff → spec → plan) from the project's
  `dryforge/` (project-root-relative). If absent, ask for the path.
- **git required** — worktree isolation depends on it. If not a repo, offer `git init` **and make an
  initial commit** (an empty repo has no HEAD, so no worktree/branch can be created). If git is not
  installed, stop and say so.
- **Main-protection precondition (before any worktree):** identify the project's main branch (docs /
  remote default / ask — do not guess). Verify `main` has no unpushed commits and the working tree
  has no modified/staged **tracked** files; if either fails, **stop and report** (do not proceed on a
  dirty/ahead main). All work happens off a fresh feature branch, never on main.
  - **The producer left `dryforge/` as plain untracked files** (produce never touches git). So
    *untracked content under `dryforge/` is the expected handoff state and counts as clean* — do not
    treat it as a dirty tree. Anything else untracked or modified is foreign work → stop and report.
  - **You own the `dryforge/` git mechanics.** On the feature worktree (below), add `dryforge/` to
    `.gitignore` and commit that **on the feature branch** — never on main, so main is never made
    ahead of its remote. If a prior run left `dryforge/` *tracked*, run `git rm -r --cached dryforge/`
    on the feature branch first (untracks without deleting), then ignore it.
- Read **handoff first** (it governs: document roles, hard gates, execution shape), then spec and
  plan. Parse the plan's Execution Graph **per `references/graph-contract.md`** — the consumer-side
  schema (what the YAML fields mean and the rules go must hold when reading them). It mirrors the
  producers' authoring schema; if the plan's graph contradicts it, that is a producer-side defect →
  stop and escalate.

## Graph validation (before any irreversible worktree creation)

Validate the plan's Execution Graph **before creating the feature worktree** — it is cheap and safe
to fail (no git state mutated yet), so catch a malformed graph before any worktree exists to unwind.
Parse the YAML, then confirm the graph is **acyclic**, that every `depends` / `after` id **names a
real task** (no dangling reference), and that the plan body and the graph **agree on the task id set**
(no graph task missing from the plan body, none in the body absent from the graph). `graph-contract.md`
is the authoritative rule set for these checks. On any failure, **report the specific error** — which
check failed and where (the offending id / cycle / mismatch) — and the recovery: the user fixes the
plan YAML and re-runs `/dryforge:go`, which re-validates from scratch (no partial state is left behind,
since validation precedes worktree creation).

## Flow

Parse the graph → topological sort into waves (batches of **≤8 concurrent**) → **create the feature
worktree branched from main** (`git worktree add -b dryforge/<feature> <path> <main>`). In the
feature worktree, **set up `dryforge/`**: copy the 3-doc in (the orchestrator reads it *here* — the
task subagents do **not** read `dryforge/`; they receive spec slices inline, see
`orchestration.md`), then add `dryforge/` to `.gitignore` and **commit that ignore rule on the
feature branch** (untrack a prior-run `dryforge/` with `git rm -r --cached dryforge/` first if
needed). All task branches derive from the **feature** branch, never from main. Then, per wave:

**Runtime-adaptive scaffolding (1-task graph).** Size the per-wave scaffold to the graph the
producer actually wrote. When the parsed graph has exactly **one task** (a single wave, no
parallelism), there is no cross-task surface — so a 1-task graph doesn't need per-wave cross-task
review: **skip the per-wave code-review** (step 7) and run code review once at completion instead,
and **inline or skip the deferred-wiring step** (step 5) when the task declares no shared-write
(there are no sibling registrations to coordinate). **Never** skip the dispatched per-task
spec-review (step 4), the per-wave integration gate (step 6), or the completion gate — those verify
the task itself, not cross-task interaction, and apply at any graph size.

1. **Create task worktrees** — serially (avoid `.git/config.lock` contention), each branched off the
   feature branch. **If the project has an installable dependency tree**, install or share it (can
   run in parallel / background; sharing guidance in `orchestration.md`) — skip this for a project
   with no separate dependencies (a single-file program, vendored or system libs).
2. **Dispatch implementers** — one subagent per task, in parallel, ≤8 at a time
   (`implementer-prompt.md`): **right-sized verification** (the implementer consumes the
   producer-set `risk` tier — RISKY/MECHANICAL/NONE — to size its test ceremony, per
   `implementer-prompt.md`; if a task omits `risk`, the implementer judges it at build time),
   shared-write constraints, pinned worktree path.
3. **Collect** — each returns a structured summary (status + files + tests + concerns); keep the
   summary only, not raw diffs.
4. **Spec review** (per task, `spec-review-prompt.md`) — a dispatched subagent checks the diff
   against the spec requirement and reports pass / needs-fix only. The reviewer receives only the
   spec slice + the raw diff — **not** the implementer's summary/claims (preserve independence).
   Before a wave merges, N tasks must have run N spec-reviews.
5. **Merge serially** into the feature branch. **Merge-gate per task (objective, not existence-only):**
   the task branch is strictly **ahead** of the feature branch (`git rev-list feature..task` non-empty)
   AND its diff is non-empty and touches the task's declared targets — checked against the merge-base
   (`git diff feature...task`, **three-dot**, so wave siblings already merged into feature don't
   pollute it) — never trust a self-report.
   The **merge commit message must satisfy the project's commit-msg hooks** (a rejected hook leaves
   the merge incomplete). Then run **regen barriers**, then the **deferred wiring** step (a single
   writer appends all shared registrations, idempotently — check-before-append, so a partial-wave
   retry does not double-write; conflicting registrations → escalate) **and commit the wiring on the
   feature branch** — uncommitted wiring is silently lost to later waves' worktrees and to the final
   merge, even though the gate (run in this worktree) would still show green.
6. **Integration gate** — run **the project's verify commands** (discovered in EXPLORE/GATHER — may
   be a typecheck/lint/test set, a build/run, or a single command; not every stack has all three, so
   never assume the triad) on the merged result **after** wiring; **green = those commands exit 0,
   output captured** (per-task green ≠ combined green). Failure → analyze → fix-dispatch or escalate.
   (Run per wave whatever is the project's **primary correctness gate** — for a compiled stack the
   **build/compile *is* that gate** and must run every wave, since a wave that doesn't compile isn't
   green; defer only genuinely *expensive, end-only* steps to the completion gate, not the primary
   gate.)
7. **Code review** (per wave, on the merged result) — quality reviewer (`reviewer-prompt.md`).
   **Clear = zero blocking findings, recorded.**
8. **Clean up** task worktrees — but only after asserting each task's commit is an ancestor of the
   feature branch (`git merge-base --is-ancestor`); if not (e.g. a merge silently failed), **do not
   remove** — escalate. Prefer safe `git worktree remove` (no `--force`) so a non-empty/dirty tree
   stops cleanup. For a **successful** task, a safe remove can still be blocked by untracked
   per-worktree artifacts — build output, an un-ignored dependency directory, or a **dependency-store
   symlink you created for sharing** (note: a trailing-slash ignore pattern like `<dir>/` matches a
   real directory but **not** a symlink of that name — ignore it slash-less, `<dir>`). These should
   be ignored so they neither block cleanup nor read as a dirty tree; and the share-symlink is the
   orchestrator's *own* artifact, so
   remove it first, then retry the safe remove (never `--force` away unreviewed work). **After removing a merged task's worktree, delete its now-merged task branch**
   (`git branch -d`, which refuses if unmerged — itself a safety check). Then → next wave. (A failed
   task's worktree and branch are preserved for diagnosis.)

**Advancing waves (overlap allowed, dispatch still gated).** "Advance" does not force the next wave's
setup to wait behind this wave's gate and review: once Stream A has committed the merged + wired
feature tip, the next wave's **provisioning** (worktree creation + dependency share off that committed
tip) MAY overlap the current wave's integration gate and code review. But the next wave's **dispatch**
still waits for a **green gate + cleared review** — only idle provisioning time is reclaimed, never the
correctness gate. This is an opt-in latency optimization; if the feature-tip lock / refresh bookkeeping
is uncertain, fall back to fully serial wave advance. The Stream A/B/C mechanics (serial feature-branch
mutation, the gate/review stream, and overlapped provisioning + feature-tip lock/refresh) live in
`references/orchestration.md` — don't re-derive them here.

Spec review per task + code review per wave is the **spec-first 1+1** model. Mechanics, CC dispatch
constraints, status protocol, context budget, and failure handling live in `references/orchestration.md`.

## Completion gate (avoid self-judgment A=A)

Done only when ALL hold — on **evidence**, not assertion:
- every wave merged; every spec requirement traced to a merged + spec-reviewed task; zero open
  `BLOCKED` / needs-fix. **"Zero open BLOCKED" is not "counted as done"** — each BLOCKED task must have
  **completed escalation to the user** (the user has been told and has resolved its disposition) with
  its **worktree preserved** for diagnosis; a BLOCKED task may never be silently tallied into "done".
- every `DONE_WITH_CONCERNS` concern **resolved (fix-dispatched) or explicitly accepted and
  recorded** (at code-review or by the user) — a flagged concern is never silently carried into
  "done".
- a **final full check** — **all** of the project's verify commands (whatever the stack actually has
  — e.g. typecheck / lint / test / build, or fewer; including any genuinely expensive end-only step
  deferred from the per-wave gate) on the integrated feature branch **exit 0, with the commands and
  exit codes captured and shown** (not "looks green"). **Why re-run everything when each wave already
  passed:** a per-wave gate proves each wave green *in isolation*, but the integrated result can break
  on **cross-wave interactions** that no single wave's gate could see — so the completion gate re-runs
  the full verify set against the whole feature branch as the final, all-together check. Running the
  full verify set every wave is the **safe baseline**; narrowing to an **affected-only** subset is an
  optional efficiency lever only where the project's tooling supports reliable impact analysis (see
  `develop/research/008-parallel-isolation-provisioning.md`).
- no residual escalation outstanding — and any task that returned `NEEDS_CONTEXT` / `BLOCKED` was
  escalated to the user **synchronously** (the orchestrator pauses the run and waits for the user's
  response — never a silent hang or a timeout-drop). Subagents themselves never call `AskUserQuestion`
  (the prompt files carry that fresh-session rule); only the orchestrator relays escalations to the user.

## Finish

After the completion gate passes: ask the user **how to integrate** — the right answer depends on
the project's convention (direct merge to the main branch, or push the feature branch and open a
review request / PR, or just hand off the branch). Never integrate on your own.
- **Merge to the main branch →** fetch and confirm it has not moved (if it has, re-integrate/
  escalate); merge the feature branch with **`--no-ff`** (preserve history per project norm) **from a
  checkout that is on the main branch** — the primary checkout (check it out there first) or a
  dedicated main worktree; do **not** assume the current worktree/cwd is on the main branch, or the
  merge runs against the wrong branch. **On conflict, abort and escalate** (do not leave the main
  branch half-merged). Only after confirming the merge committed and nothing is unmerged/unpushed,
  clean up worktrees + branches.
- **Open a PR / push the feature branch →** push it and surface the branch (and a PR if the project
  uses them); leave integration to the project's review flow. Keep the worktree until the user says
  it's safe to clean up.
- **Hand off only →** keep the feature branch and worktree intact.
