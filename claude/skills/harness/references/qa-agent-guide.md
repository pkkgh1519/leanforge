# QA Agent Guide

Use QA when a harness output can fail silently or when multiple roles produce artifacts that must align.

## QA responsibilities

- verify required paths and files
- check that skills and team specs agree
- check frontmatter and trigger descriptions
- inspect handoff files for required fields
- verify reviewer criteria are concrete
- distinguish missing evidence from weak evidence
- recommend narrow fixes

## QA output

```markdown
# QA Review

## Material inspected

## Checks run

## Findings

### Critical

### Major

### Minor

## Suggested repairs

## Re-review result
```

## Review discipline

- Lead with findings that affect correctness.
- Avoid style-only comments unless style hides ambiguity or breakage.
- Include file paths and exact sections when practical.
- Keep repair scope narrow.
- Re-run validation after repair.

## Failure scenarios to test

- missing `name` or `description` frontmatter
- duplicated skill trigger
- root `AGENTS.md` too long
- handoff file path mismatch
- optional custom agent missing required TOML field
- benchmark run without baseline
- review loop with no stop condition
