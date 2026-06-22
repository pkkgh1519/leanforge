# Maintenance and Drift

Harness quality depends on ongoing maintenance. A generated harness can drift when paths change, skills overlap, validators become stale, or users start asking for workflows the original design did not cover.

## Phase 0 audit checklist

Before creating or changing a harness, inspect:

- `AGENTS.md`
- `.agents/skills/`
- `docs/harness/`
- `_workspace/`
- existing validation scripts
- benchmark or review artifacts
- changelog or maintenance notes

Classify each finding:

- preserve
- update
- archive
- replace
- remove only with explicit reason

## Drift types

### Path drift

A skill, doc, or team spec points to a file that no longer exists.

Repair by updating the pointer or restoring the missing artifact.

### Trigger drift

Two skills match the same request and give conflicting guidance.

Repair by narrowing descriptions and adding "when not to use" rules.

### Role drift

A role owns too many unrelated responsibilities or no longer matches the work.

Repair by splitting stable responsibilities or merging unused roles.

### Validation drift

The validator checks old paths or misses new mandatory files.

Repair the validator before claiming the harness is healthy.

### Benchmark drift

The evaluation no longer matches the user's current quality target.

Repair by updating the scenario, metric, or rubric and marking old runs as historical.

### Recovery-logic drift

Temporary heuristics remain after the underlying model/tool behavior improves.

Repair by moving them to a removable section or deleting them after validation.

## Phase 7 maintenance loop

After every material change:

1. Record what changed.
2. Run structural validation.
3. Run at least one scenario or smoke test.
4. Note failures and repairs.
5. Update the changelog.
6. Preserve useful superseded artifacts when they help auditability.
7. Keep root guidance short.

## Maintenance note template

```markdown
# Maintenance Note

Local time:
UTC time:
Repository:
Change type:

## What changed

## Why it changed

## Files inspected

## Drift found

## Repairs made

## Validation run

## Remaining risks

## Next check
```
