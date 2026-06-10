# Benchmark Pack Guide

Use a benchmark pack when the user wants evidence that a harness improves consistency or quality. Keep source scenarios under `examples/benchmark-pack/` and run-specific outputs under `_workspace/experiments/{run}/` so canonical layout and benchmark references stay aligned.

## Minimum benchmark files

```text
examples/benchmark-pack/scenarios.tsv
examples/benchmark-pack/rubric.tsv
examples/benchmark-pack/expected-artifacts.md
_workspace/experiments/{run}/results.tsv
```

## Scenario columns

- `scenario_id`
- `prompt`
- `expected_artifacts`
- `quality_risk`
- `baseline_notes`

## Rubric columns

- `axis`
- `score_0`
- `score_1`
- `score_2`
- `score_3`
- `weight`

## Results columns

- `run_id`
- `scenario_id`
- `mode`
- `artifact_path`
- `score`
- `reviewer`
- `notes`

## Honest comparison

Compare at least:

- baseline/manual response
- harness-guided response
- harness-guided response after review/repair, if applicable

Do not report aggregate improvement unless:

- every scenario has a recorded score
- scoring criteria are stable
- reviewer identity or process is recorded
- failures are included instead of dropped

## Suggested review axes

- requirement coverage
- path correctness
- handoff clarity
- validation completeness
- limitation honesty
- user usability
