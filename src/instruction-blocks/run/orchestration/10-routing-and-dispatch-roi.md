
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
  - **Claude Code.** The host exposes no slot arithmetic and queues excess children itself; there is
    no preflight signal to read, so never emulate one and never serialize a ready wave to compensate.
    Treat `runtime_total_slots` as unbounded on this host: `free_slots` never binds, and `batch_size`
    reduces to `min(ready_dispatchable_tasks, explicit_user_limit_or_infinity)`. Dispatch the admitted
    batch as parallel `Agent` calls in a single message and collect completions as the host reports
    them; a failed dispatch gets one bounded retry, and a second failure or no state change blocks
    rather than looping. A prior implementer may continue via `SendMessage` to that same child only
    when its immediately preceding structured status was `NEEDS_CONTEXT` or `BLOCKED` and the bounded
    retry keeps the same task, unchanged contract, same role, and same pinned work location. Every
    review, re-review, upgraded-model attempt, changed task, contract, role, or work location, `DONE`
    or `DONE_WITH_CONCERNS`, and fix-dispatch starts a fresh child.
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
