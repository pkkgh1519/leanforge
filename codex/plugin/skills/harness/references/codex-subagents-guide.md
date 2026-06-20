# Codex Subagents and Custom Agents Guide

Use this guide when a harness might benefit from Codex subagents or project-scoped custom agents.

## Core rule

Subagents are optional but may be spawned autonomously when the task is read-heavy, review-heavy, multi-part, or clearly parallelizable. A harness should still work as a single-agent workflow, and the parent agent always owns requirements, synthesis, integration, and final acceptance. In dryforge `go`, custom agents are reviewer/explorer lenses only; `go` keeps execution authority.

Prefer repo-local custom agents over global `default`, `explorer`, `worker`, or `reviewer` roles when the repo-local agent description is more specific to the repository task. Use global roles only when no project-local agent is a better fit.

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

## Custom agent files

Project-scoped custom agents live under the target repository, not the user-level Codex home:

```text
<repo>/.codex/agents/{agent-name}.toml
```

Every file should define:

```toml
name = "agent_name"
description = "Short description of when to use this agent."
developer_instructions = """
Instructions for the spawned agent.
"""
```

Optional fields can include `nickname_candidates`, `model`, `model_reasoning_effort`, `sandbox_mode`, and tool or skill configuration. Prefer omitting model pins so the parent Codex setup can choose the active model.

## Project-scoped config

Use `<repo>/.codex/config.toml` only for repository-local delegation settings such as `[agents] max_depth = 1` or `max_threads`. Do not create or modify user-level `~/.codex/config.toml` from a generated harness. If the target repository already has `.codex/config.toml`, preserve it and make the smallest additive change instead of replacing it.

## Safe defaults

- Read-only agents should set `sandbox_mode = "read-only"`.
- Keep `max_depth = 1` in repo-local `.codex/config.toml` unless recursive delegation is explicitly needed.
- Keep custom agents narrow and opinionated.
- Prefer read-only `sandbox_mode` for explorer/reviewer agents.
- Parent agent remains responsible for final synthesis and acceptance.
- Child agents should return concise findings with file paths, evidence, and uncertainty.
- Do not let custom agents own persistent plan state unless the user explicitly requests delegated execution.
- Do not use `default`, `worker`, `explorer`, or `reviewer` as project custom-agent names; prefix names by domain.
- Do not design dryforge repo-local agents to replace `go` implementers, worktree handling, merge gates, or status lifecycle.

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
