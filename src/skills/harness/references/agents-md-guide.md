# AGENTS.md Guide

`AGENTS.md` is always-loaded repository guidance. It should be short, durable, and repo-wide.

## Good root guidance

Use root `AGENTS.md` for:

- project purpose
- canonical paths
- build, test, and validation commands
- durable safety boundaries
- where deeper docs live

## Bad root guidance

Do not use root `AGENTS.md` for:

- long generated codebase summaries
- large style guides already enforced by tooling
- one-off task instructions
- giant lists of files
- volatile troubleshooting heuristics
- role-specific playbooks that belong in skills

## Recommended shape

```markdown
# Repository Agents Guide

## What

- One or two bullets about the repository.
- Canonical source and generated artifact paths.

## Why

- The reason the workflow exists.
- The quality or safety bar.

## How

- Exact validation commands.
- Links to deeper docs or skills.
```

## When Harness should create or update AGENTS.md

Create or revise `AGENTS.md` only when:

- the target repo has no repo-wide agent guidance and needs it
- canonical paths changed
- verification commands changed
- durable workflow boundaries changed
- the old file is too long, stale, or misleading

## When Harness should not update AGENTS.md

Do not update it when:

- the task is one-off
- the new instruction applies only to one generated skill
- the content belongs in `docs/harness/`
- the update would duplicate existing docs
- the user did not ask for durable repo-wide changes and the change is not necessary

## Review checks

- Under 4 KiB is preferred.
- Every bullet should apply to most agent sessions in the repo.
- Every path should exist or be clearly marked as a planned generated path.
- The file should point to deeper docs instead of copying them.
