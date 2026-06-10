# Orchestrator Template

Use this template when generating `docs/harness/{domain}/team-spec.md` or an orchestrator skill. Keep the contract model-agnostic: describe the work, evidence, validation, and stop rules without depending on a specific model version or provider behavior.

```markdown
# {Domain} Harness Team Spec

## Purpose

## Users and Expertise Assumptions

## Outcome

State the concrete user-visible result this harness should produce.

## Success Criteria

- Criterion:
- Criterion:
- Criterion:

## Scope

### In Scope

### Out of Scope

## Evidence Requirements

- Files or sources the agent must inspect:
- Artifacts the agent must create or update:
- Evidence that must appear in the final report:

## Retrieval Budget

State the expected search/read budget and the condition for stopping retrieval. Prefer enough evidence to support the outcome, not unlimited exploration.

## Validation

Commands, smoke tests, scenario checks, or manual review steps that prove the harness is usable.

## Side-Effect Boundary

List actions that require explicit approval before execution, such as writing outside the target repository, modifying user-level configuration, publishing externally, deleting or overwriting files, using credentials, or touching production/billing/deployment surfaces.

## Stop / Report Rule

State when the agent must stop and report instead of guessing, broadening scope, or taking side effects.

## Architecture Pattern

Chosen pattern:
Why this is the smallest sufficient pattern:

## Roles

### {Role}

Responsibility:
Inputs:
Outputs:
Handoff files:
Review edges:
Failure behavior:

## Workflow

1. Phase:
   - owner:
   - input:
   - output:
   - done condition:

## Handoff Contract

| File | Owner | Reader | Purpose | Required fields |
| --- | --- | --- | --- | --- |

## Review and Repair Loop

## Optional Subagent Usage

## Benchmark or Scenario Tests

## Maintenance and Drift

## Completion Packet

Outcome:
Files changed:
Artifacts created:
Evidence:
Validation commands:
Validation result:
Known limitations:
Side-effect boundary respected:
Next optional step:

## Changelog
```
