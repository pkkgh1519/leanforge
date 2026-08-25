
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
