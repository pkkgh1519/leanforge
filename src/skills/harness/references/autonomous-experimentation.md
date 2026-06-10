# Autonomous Experimentation Profile

Autonomous experimentation is a workflow profile that can compose with Pipeline, Supervisor, or Producer-Reviewer. It is not a seventh architecture pattern.

Use it when the user wants iterative improvement on user-controlled compute with a fixed evaluation surface.

## Required definitions

Before running an experiment loop, define:

- mutable surface: what may change
- immutable surface: what must not change
- baseline artifact: the current behavior or output before harness guidance
- metric: how outputs will be compared
- budget: number of attempts, time, or token limit
- keep/discard policy: when a candidate is preserved
- ledger path: where results are recorded

## Suggested paths

```text
_workspace/experiments/{run}/baseline.md
_workspace/experiments/{run}/candidate_{n}.md
_workspace/experiments/{run}/review_{n}.md
_workspace/experiments/{run}/results.tsv
_workspace/experiments/{run}/decision.md
```

## Loop

1. Record baseline.
2. Propose one candidate change.
3. Run the fixed evaluation.
4. Record result in `results.tsv`.
5. Review failure or improvement.
6. Keep, discard, or narrow.
7. Stop at the budget or when the metric is stable enough.

## Guardrails

- Do not change the evaluation during a run.
- Do not compare outputs against a hidden rubric.
- Do not claim performance gains without recorded evidence.
- Keep raw outputs available when practical.
- Treat subjective review as review, not automated score.
