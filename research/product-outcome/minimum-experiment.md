# Minimum product-outcome experiment

## Identity

- Experiment ID: `leanforge.product-outcome.minimum-v1`
- Baseline tree: the product surface at `cbbb90758d28112a0918a1f999b841b9e8f7a7e6`
- Candidate: the immediate product-outcome patch built on that tree
- Evaluator: `tools/product_outcome_experiment.py`
- Raw host traces: none

## Question

Does the candidate make Leanforge's public promise, command discovery, onboarding, and completed-result
example agree with the authoritative product outcome: a verified change, captured evidence, remaining
risk, and a user-owned integration choice?

## Predeclared deterministic checks

The candidate must pass all seven checks. A partial score is failure.

1. English and Korean README introductions lead with the trusted-change outcome.
2. Claude and Codex marketplace copy leads with the outcome, not `3-doc` or "any input" plumbing.
3. Prime, Run, Set, and Run TDD descriptions state their user-facing outcome.
4. Run requires four clearly labeled final-result sections: Change, Verification, Remaining risk, and Integration.
5. Consumer and installation documentation expose the same four-part result contract.
6. A sanitized completed cycle traces contract, actual change, evidence, remaining risk, and integration state.
7. Public copy makes no unmeasured claim that every task is faster or cheaper.

Known-opposite mutations must fail for at least: 3-doc-first marketplace copy, missing remaining-risk
section, missing terminal-blocker preserved-state reporting, generated Run result drift, missing
verification in the completed example, and an unmeasured "every task faster" claim.

## Repository gates

Run the evaluator and its known-opposite mutations, then the repository gates:

```text
python tools/product_outcome_experiment.py --json
python -m unittest tests.test_product_outcome_experiment -v
bash build/build.sh
git diff --exit-code -- claude codex
test -z "$(git status --porcelain --untracked-files=all -- claude codex)"
python -m unittest discover -s tests -v
git diff --check
```

## Interpretation boundary

Passing means the product surfaces and example are internally aligned and mechanically guarded. It
does not mean an installed Claude Code or Codex host invoked the plugin correctly, and it does not
measure Time to Trusted Change, token cost, question count, user reading time, rework, or defect rate.
Those claims require captured host runs and paired evaluation.
