
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

<!-- leanforge:run-semantic:RUN-EXTERNAL-PROOF:start -->
```json
{
  "id": "RUN-EXTERNAL-PROOF",
  "kind": "external_proof",
  "definition": "The external implementer is mechanically pinned by a non-empty scalar base value exactly equal to the selected base before action; a successful route then captures green external evidence, makes one unconditional implementer-owned base commit, and receives independent git-log commit proof.",
  "constraints": [
    "The selected-base fact and implementer base-pin fact each carry one non-empty scalar value, the values are equal, and both facts precede external action.",
    "Green external evidence follows the action and precedes one unconditional implementer-owned base commit.",
    "Independent orchestrator-owned git-log commit proof follows the base commit."
  ]
}
```
<!-- leanforge:run-semantic:RUN-EXTERNAL-PROOF:end -->

**Both dispatched modes:** verify the commit after return (`git log`; for file-diff, the diff touches
declared targets — never trust self-report); **restore the orchestrator's cwd** (subagent runs can
drift it); **subagent output is bounded** (large results → file + digest). **No integration gate** for
a sequential wave — the self-checks run on the cumulative base (which already includes all prior
waves); with a single task cross-task interaction risk is zero, and the completion gate catches
cross-wave interactions at the end.
