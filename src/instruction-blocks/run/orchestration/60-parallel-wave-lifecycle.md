
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
