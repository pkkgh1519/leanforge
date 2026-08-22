# Adaptive Assurance Phase 1.2 Observation Record

> Copy this worksheet into a private study workspace for one Prime cycle. Do not commit a completed
> record to the public Leanforge repository. Complete and seal Section A without showing its contents to
> the adjudicator, complete Section B, then reveal Section A and complete Sections C–E.

## A. Cohort and sealed shadow prediction — collector only

- Study version: `2`
- Study batch: `<batch-id>`
- Predeclared observation window or case range: `<sealed scope>`
- Inclusion/exclusion criteria version: `<criteria-id>`
- Enrollment status: `<eligible | excluded>`
- Predeclared exclusion reason, when excluded: `<reason or none>`
- Leanforge commit: `<exact commit SHA>`
- Adaptive Assurance contract Git blob object ID: `<exact blob id>`
- Case ID: `<sanitized-id>`
- Coarse task category: `<docs | test | local-fix | config | feature | refactor | dependency | operations | other>`
- Host: `<claude | codex | other>`
- Model/settings label, only when exposed by the host: `<label | unavailable>`
- Cycle: `<first | delta>`
- Capture status: `<present | absent>`
- Collector role or initials: `<redacted identifier>`
- Adjudication arrangement: `<separate adjudicator | mechanically blinded same person | not independent>`

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
- Prediction contents hidden from adjudicator: `<yes | no>`
- Case enrollment decided before prediction reveal: `<yes | no>`
- If any answer is `no`, use a second adjudicator or mark the comparison `unevaluable`.

## B. Independent observed class — adjudicator before reveal

- Pinned Leanforge commit confirmed: `<yes | no>`
- Pinned contract blob confirmed: `<yes | no>`
- Evidence-window endpoint: `<Prime G7 | Run completion | terminal blocker | user abandonment>`
- Evidence availability: `<complete | incomplete | contradictory>`
- Evidence sources reviewed, sanitized: `<final 3-doc, reviewer findings, command evidence, blocker summary>`
- Adjudicator role or initials: `<redacted identifier>`
- Adjudicator had not read Section A or the sidecar: `<yes | no>`

### Observed classification

- Independently observed class: `<lite | standard | assurance | unevaluable>`
- Newly discovered hard triggers: `<closed atoms or none>`
- Newly discovered Lite required-true failures: `<closed facts or none>`
- Newly discovered Lite required-false violations: `<closed facts or none>`
- Later escalation signal: `<none | to_standard | to_assurance>`
- Classification basis: `<concise evidence-based rationale>`

Apply the pinned contract revision that produced the prediction. Do not infer success from missing
evidence. When one class cannot be supported without guessing, select `unevaluable`.

## C. Reveal and safety comparison

Complete only after Section B is fixed.

- Revealed shadow mode: `<lite | standard | assurance | absent>`
- Comparison label: `<exact | conservative | lite_to_standard | material_false_negative | unevaluable>`
- Material false negative: `<yes | no | unevaluable>`
- Required safety disposition: `<none | inspect grounding | revise eligibility | revise hard-trigger detection | repeat with independent adjudicator | no-go>`
- Resolver or second-adjudicator outcome, when used: `<concise result or none>`

### Underclassification explanation

Required for every `lite_to_standard` or `material_false_negative` record.

- Initial prediction basis: `<what was grounded at ELICIT exit>`
- Later fact or trigger: `<what changed or was discovered>`
- Why the difference matters: `<concrete safety or ceremony consequence>`
- Proposed contract, grounding, or study disposition: `<minimal action>`
- Router or contract changed as a result: `<yes | no>`
- If `yes`, new study batch ID: `<required new batch>`

## D. Product north-star observation

Record only values available without changing the observed Prime/Run cycle.

- Shadow collection caused an additional user question: `<yes | no | unevaluable>`
- User was asked to choose or understand a mode: `<yes | no | unevaluable>`
- Shadow collection added a subagent dispatch: `<yes | no | unevaluable>`
- Shadow collection caused an additional broad repo scan: `<yes | no | unevaluable>`
- Shadow collection changed live Prime or Run behavior: `<yes | no | unevaluable>`
- Prime invocation to G7 or stop, when available: `<duration | unavailable>`
- User question count: `<integer | unavailable>`
- User reply turns: `<integer | unavailable>`
- Subagent count: `<integer | unavailable>`
- Tool-call or file-read count: `<value | unavailable>`
- Host usage/tokens: `<value | unavailable>`
- 3-doc-gate result: `<clear | blocking | not reached | unavailable>`
- 3-doc-gate blocker count: `<integer | unavailable>`
- Approval summary size: `<words/tokens | unavailable>`

### Potential Lite value

- Strict-Lite eligibility remains true at evidence-window end: `<yes | no | unevaluable>`
- Candidate ceremony that a binary pilot could omit: `<closed list>`
- Hard boundary that must remain: `<closed list>`
- Measured or conservatively bounded removable cost: `<value and basis | unavailable>`
- Expected promotion/recovery cost: `<value and basis | unavailable>`
- Estimated net removable cost after shadow tax: `<value and uncertainty | unavailable>`

Do not record a saving that depends on removing intent ownership, actual command evidence, recovery,
final diff, user approval, integration choice, or on creating a third Standard execution topology.

## E. Redaction and integrity check

- [ ] The exact Leanforge commit and contract blob are recorded.
- [ ] The observation window and inclusion/exclusion criteria were fixed before prediction reveal.
- [ ] This case was not selected or excluded because of its shadow mode or outcome.
- [ ] No raw user prompt is included.
- [ ] No proprietary source, patch, or customer content is included.
- [ ] No secret, credential, personal data, repository URL, or absolute path is included.
- [ ] The exact sidecar payload was copied rather than reconstructed.
- [ ] The independent class was fixed before the shadow mode was revealed.
- [ ] Missing or contradictory evidence was not counted as a pass.
- [ ] This record did not alter the observed Prime or Run cycle.
- [ ] This record is not pooled with a different router, contract, host, model, or settings revision.

## F. Study disposition

- Usable safety observation: `<yes | no>`
- Counts toward mode coverage: `<lite | standard | assurance | no>`
- Counts toward host coverage: `<claude | codex | other | no>`
- Counts toward potential-value analysis: `<yes | no>`
- Requires individual study-report entry: `<yes | no>`
- Final note, redacted: `<optional concise note>`
