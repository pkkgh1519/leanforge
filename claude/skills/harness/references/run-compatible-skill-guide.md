# Run-Compatible Repo Skill Guide

Use this guide when Harness generates a repository-local skill that `Leanforge Run` may use during
review or diagnosis.

## Purpose

A run-compatible repo skill is a repository-specific review/explore/checklist lens. It captures
repeated risks, missing evidence patterns, or review findings from the repository so `Run` can inspect
future changes with sharper context.

It is not an implementer and does not own execution.

## Required section

Every run-compatible skill must include:

```markdown
## Leanforge Run usage

Allowed phases:
- final_review
- conditional_spec_review
- failure_exploration

Never use for:
- implementer replacement
- wave scheduling
- merge gate
- worktree lifecycle
- .leanforge state management
- legacy .dryforge migration state

Inputs Run must provide:
- changed files
- relevant spec slice
- verification evidence
- diff or commit range

Output:
- blocking findings
- advisory findings
- missing evidence
- uncertainty
```

## Trigger discipline

Keep the frontmatter description narrow. Prefer:

```yaml
description: "Use when Leanforge Run reviews API route/schema/client contract changes in this repository."
```

Avoid:

```yaml
description: "Use for all API work in this repository."
```

## Context boundary

The skill must not read active `.leanforge/handoff.md`, `.leanforge/spec.md`, or `.leanforge/plan.md`
directly. It must also avoid legacy `.dryforge/{handoff,spec,plan}.md` active docs. `Run` passes the
relevant spec slice, changed files, diff, and verification evidence inline.

## Generation boundary

Generate Run-compatible repository lenses only as repo-local skills under `.agents/skills/`.
Keep independent review or failure exploration needs inside the skill's `## Leanforge Run usage`
contract so `Run` can pass a bounded context slice to a generic reviewer or explorer.
