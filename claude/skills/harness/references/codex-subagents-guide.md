# Codex Subagents Guide

Use this guide when a harness might benefit from bounded Codex subagents.

## Core rule

Subagents are optional but may be spawned autonomously when the task is read-heavy, review-heavy, multi-part, or clearly parallelizable. A harness should still work as a single-agent workflow, and the parent agent always owns requirements, synthesis, integration, and final acceptance. In Leanforge `Run`, repo-local skills may provide reviewer/explorer lenses only; `Run` keeps execution authority.

Durable repository-specific guidance belongs in `.agents/skills/` or `docs/harness/`. Subagents are execution-time helpers, not persistent project configuration.

## When to use subagents

Use subagents without waiting for a separate user command when the work benefits from compartmentalization, such as:

- independent codebase exploration across different surfaces
- parallel review categories such as security, correctness, tests, and docs
- competing research or design positions
- bounded generation branches followed by synthesis

Avoid subagents for:

- ordinary linear edits
- tasks where all branches need the same context
- sensitive changes requiring one owner
- cases where extra threads add cost but not quality

## Safe defaults

- Keep subagent roles narrow and evidence-focused.
- Prefer read-only behavior for explorer/reviewer work.
- Parent agent remains responsible for final synthesis and acceptance.
- Child agents should return concise findings with file paths, evidence, and uncertainty.
- Do not let child agents own persistent plan state unless the user explicitly requests delegated execution.
- Do not design Leanforge repo-local skills to replace `Run` implementers, worktree handling, merge gates, or status lifecycle.

## Handoff files

When subagents produce outputs, use deterministic files:

```text
_workspace/{phase}_{agent}_findings.md
_workspace/{phase}_synthesis.md
_workspace/{phase}_decision.md
```

Each finding file should include:

- task received
- files or sources inspected
- findings
- evidence
- uncertainty
- recommended next action

The parent reads all findings before making the final decision.
