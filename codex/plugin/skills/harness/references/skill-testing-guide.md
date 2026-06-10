# Skill Testing Guide

Test a harness like a reusable product, not a one-off prompt.

## Test classes

### Structure tests

- required files exist
- `SKILL.md` frontmatter is valid
- references are readable
- team spec paths match generated paths
- optional custom agents have required TOML fields

### Discoverability smoke tests

After generating or changing a repo-local skill, test from the target repository root:

- start a fresh Codex thread, restart/reload the host, or use the host's documented skill-refresh path
- verify the new skill name and description are surfaced by the available skill list or by an equivalent prompt/context inspection surface
- run one positive trigger that should load the skill and record the observed routing
- run one near-miss trigger that should not load the skill
- run one overlap-routing trigger when another skill could match, and verify the more specific skill wins

If the host has no reliable skill-list command, record a fresh-session trigger transcript as the discoverability proof.

### Trigger tests

- prompt that should activate the skill
- near-miss prompt that should not
- overlapping prompt that should route to the right specialist

### Scenario tests

- normal happy path
- missing input path
- review finds a flaw
- benchmark requested
- maintenance/drift requested

### Baseline comparison

When useful, compare:

1. no-harness baseline
2. harness-guided output
3. reviewed/repaired harness output

Record results in `_workspace/experiments/{run}/results.tsv`.

## Assertion examples

```text
Given a request to build a reusable review workflow,
the output includes a team spec, at least one review criterion,
and a validation command.

Given a one-off bug explanation request,
the harness skill should not generate durable workflow files.
```

## Repair loop

1. Run the test.
2. Record the failure.
3. Apply the smallest instruction or file-path fix.
4. Re-run the test.
5. Update maintenance notes if the failure is likely to recur.
