# Adaptive Assurance Phase 1.2 Observation Record

> Copy this worksheet into a private study workspace for one Prime cycle. Do not commit a completed
> record to the public Leanforge repository. Complete Section A, seal it, complete Section B without
> reading the prediction, then reveal Section A and complete Section C.

## A. Sealed shadow prediction — collector only

- Study version: `1`
- Case ID: `<sanitized-id>`
- Study batch: `<batch-id>`
- Coarse task category: `<docs | test | local-fix | config | feature | refactor | dependency | operations | other>`
- Host: `<claude | codex | other>`
- Cycle: `<first | delta>`
- Capture status: `<present | absent>`
- Collector role or initials: `<redacted identifier>`

Copy the sidecar unchanged when present:

```json
{
  "schema_version": 1,
  "shadow_only": true,
  "cycle": "first | delta",
  "mode": "lite | standard | assurance",
  "reasons": [],
  "hard_triggers": [],
  "missing_lite_required_true": [],
  "violated_lite_required_false": [],
  "harness_sync": true
}
```

- Section A sealed before adjudication: `<yes | no>`
- If `no`, use a second adjudicator or mark the comparison `unevaluable`.

## B. Independent observed class — adjudicator before reveal

- Evidence-window endpoint: `<Prime G7 | Run completion | terminal blocker | user abandonment>`
- Evidence availability: `<complete | incomplete | contradictory>`
- Evidence sources reviewed, sanitized: `<final 3-doc, reviewer findings, command evidence, blocker summary>`
- Adjudicator role or initials: `<redacted identifier>`
- Adjudicator had not read Section A: `<yes | no>`

### Observed classification

- Independently observed class: `<lite | standard | assurance | unevaluable>`
- Newly discovered hard triggers: `<closed atoms or none>`
- Newly discovered Lite required-true failures: `<closed facts or none>`
- Newly discovered Lite required-false violations: `<closed facts or none>`
- Later escalation signal: `<none | to_standard | to_assurance>`
- Classification basis: `<concise evidence-based rationale>`

Do not infer success from missing evidence. When one class cannot be supported without guessing, select
`unevaluable`.

## C. Reveal and comparison

Complete only after Section B is fixed.

- Revealed shadow mode: `<lite | standard | assurance | absent>`
- Comparison label: `<exact | conservative | lite_to_standard | material_false_negative | unevaluable>`
- Material false negative: `<yes | no | unevaluable>`
- Shadow collection caused an additional user question: `<yes | no | unevaluable>`
- Shadow collection changed live Prime or Run behavior: `<yes | no | unevaluable>`
- Required disposition: `<none | inspect grounding | revise eligibility | revise hard-trigger detection | repeat with independent adjudicator | no-go>`
- Resolver or second-adjudicator outcome, when used: `<concise result or none>`

### Underclassification explanation

Required for every `lite_to_standard` or `material_false_negative` record.

- Initial prediction basis: `<what was grounded at ELICIT exit>`
- Later fact or trigger: `<what changed or was discovered>`
- Why the difference matters: `<concrete safety or ceremony consequence>`
- Proposed contract, grounding, or study disposition: `<minimal action>`

## D. Redaction and integrity check

- [ ] No raw user prompt is included.
- [ ] No proprietary source, patch, or customer content is included.
- [ ] No secret, credential, personal data, repository URL, or absolute path is included.
- [ ] The exact sidecar payload was copied rather than reconstructed.
- [ ] The independent class was fixed before the shadow mode was revealed.
- [ ] Missing or contradictory evidence was not counted as a pass.
- [ ] This record did not alter the observed Prime or Run cycle.

## E. Study disposition

- Usable observation: `<yes | no>`
- Counts toward coverage target: `<lite | standard | assurance | no>`
- Requires individual study-report entry: `<yes | no>`
- Final note, redacted: `<optional concise note>`
