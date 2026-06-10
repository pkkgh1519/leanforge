# Skill Writing Guide

A Codex skill is a directory containing `SKILL.md` plus optional scripts, references, and assets.

## Required frontmatter

```markdown
---
name: domain-orchestrator
description: Trigger-focused description of when this skill should be used and when it should not.
---
```

## Body structure

Recommended sections:

1. Purpose
2. When to use
3. When not to use
4. Required inputs
5. Workflow
6. Outputs
7. Validation
8. References

## Description guidance

Good descriptions:

- front-load the main trigger words
- mention boundaries
- stay short enough to survive truncation
- avoid marketing language

Bad descriptions:

- "General helper for everything"
- long lists of unrelated tasks
- vague claims like "improves quality"
- hidden dependencies on runtime tools

## Progressive disclosure

Keep `SKILL.md` readable. Put long rubrics, examples, templates, and troubleshooting details in `references/`.

## Naming

- lowercase
- hyphen-separated
- deterministic
- domain-specific
- no spaces
- avoid names that collide with built-in tools

## Validation

After writing a skill:

- check frontmatter
- run near-miss trigger tests
- verify required references exist
- verify generated paths match the team spec
- ensure "when not to use" is clear
