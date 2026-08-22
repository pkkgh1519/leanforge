# Adaptive Assurance Pilot-Readiness Report

> Produce this report from one pinned study batch. Publish only redacted aggregates and redacted
> underclassification summaries. The report may authorize a Phase 2 design review, never Lite
> activation.

## 1. Decision

- Recommendation: `<GO_TO_PHASE_2_DESIGN_REVIEW | NO_GO>`
- Pinned Leanforge commit: `<exact SHA>`
- Adaptive Assurance contract Git blob: `<exact blob id>`
- Proposed pilot host scope: `<claude | codex | both | none>`
- Proposed execution topology: `<strict Lite vs existing Full Assurance | none>`
- Decision rationale: `<concise intersection of safety, cost, quality, burden, value, reversibility>`

## 2. Product north-star summary

- Primary outcome assessed: `Time to Trusted Change`
- Safety gate: `<pass | fail | unevaluable>`
- Shadow-tax gate: `<pass | fail | unevaluable>`
- Quality gate: `<pass | fail | unevaluable>`
- User-burden gate: `<pass | fail | unevaluable>`
- Potential-value gate: `<pass | fail | unevaluable>`
- Binary reversibility gate: `<pass | fail | unevaluable>`

A GO recommendation requires every gate to pass. A missing or unevaluable gate is NO-GO.

## 3. Cohort and integrity

- Study batch: `<id>`
- Observation window/case range: `<scope>`
- Inclusion/exclusion criteria: `<criteria id and summary>`
- Eligible cycles: `<count>`
- Enrolled cycles: `<count>`
- Excluded cycles by predeclared reason: `<counts>`
- Sidecar absent: `<count>`
- Unevaluable: `<count>`
- Claude usable observations: `<count>`
- Codex usable observations: `<count>`
- Blinding or integrity exceptions: `<count and disposition>`

## 4. Safety observation

### Counts by shadow mode and observed class

| Shadow | Observed Lite | Observed Standard | Observed Assurance | Unevaluable |
|---|---:|---:|---:|---:|
| Lite | `<n>` | `<n>` | `<n>` | `<n>` |
| Standard | `<n>` | `<n>` | `<n>` | `<n>` |
| Assurance | `<n>` | `<n>` | `<n>` | `<n>` |
| Absent | `<n>` | `<n>` | `<n>` | `<n>` |

### Comparison labels

- Exact: `<count>`
- Conservative: `<count>`
- Lite-to-Standard: `<count>`
- Material false negative: `<count>`
- Unevaluable: `<count>`

### Individual underclassifications

For every Lite-to-Standard or material false negative, include a redacted summary:

- Case ID: `<sanitized>`
- Shadow → observed: `<transition>`
- Later fact or hard trigger: `<closed atom>`
- Causal explanation: `<redacted>`
- Disposition: `<fixed | accepted not Lite-relevant | new batch required | unresolved>`

Any unresolved Lite → Assurance case makes the report NO-GO.

## 5. Installed-host behavior smoke

- Total smokes: `<count>`
- Claude: `<count>`
- Codex: `<count>`
- Classification-only user questions: `<count>`
- Classification subagents: `<count>`
- Mode choices shown to user: `<count>`
- Live Prime/Run behavior changes: `<count>`
- Telemetry failures that blocked product outcome: `<count>`
- Gate result: `<pass | fail | unevaluable>`

## 6. Paired A/B shadow-tax benchmark

- A revision: `2d2be39c01c9d19819acb0c658f07d06b06931a7`
- B revision: `<pinned candidate SHA>`
- Cases: `<count and categories>`
- Hosts: `<scope>`
- Repetitions: `<count>`
- A/B order randomized: `<yes | no>`
- Material host/model/settings changes: `<none | details and separated strata>`

| Metric | A | B | Delta | Margin | Result |
|---|---:|---:|---:|---:|---|
| Median time-to-G7 | `<v>` | `<v>` | `<%>` | `≤ +5%` | `<pass/fail>` |
| p90 time-to-G7 | `<v>` | `<v>` | `<%>` | `≤ +10%` | `<pass/fail>` |
| Median tokens/usage | `<v>` | `<v>` | `<%>` | `<predeclared>` | `<pass/fail/NA>` |
| Median tool calls | `<v>` | `<v>` | `<v>` | `<predeclared>` | `<pass/fail>` |
| Median files read | `<v>` | `<v>` | `<v>` | no broad scan | `<pass/fail>` |
| User questions | `<v>` | `<v>` | `<v>` | `0 classification-only` | `<pass/fail>` |
| Subagent dispatches | `<v>` | `<v>` | `<v>` | `0 classification-only` | `<pass/fail>` |

- Structural overhead confirmed as at most one contract read and one sidecar replacement: `<yes | no>`
- Shadow-tax gate: `<pass | fail | unevaluable>`

## 7. Quality and user burden

- Blinded 3-doc comparisons: `<count>`
- Surviving user-owned ambiguity, A/B: `<counts>`
- 3-doc-gate blocker rate, A/B: `<rates>`
- Graph/coverage defects, A/B: `<counts>`
- User reply turns, A/B: `<values>`
- Approval-summary size, A/B: `<values>`
- Extra approval steps: `<count>`
- Quality gate: `<pass | fail | unevaluable>`
- User-burden gate: `<pass | fail | unevaluable>`

## 8. Potential value

- Strict-Lite usable cases: `<count>`
- Candidate removable ceremonies: `<redacted aggregate>`
- Median conservatively estimated removable cost: `<value>`
- Median measured shadow tax: `<value>`
- Estimated removable-cost / shadow-tax ratio: `<ratio>`
- Required ratio: `≥ 2×`
- Promotion/recovery allowance included: `<yes | no>`
- Savings depend on a third Standard topology: `<yes | no; yes is failure>`
- Potential-value gate: `<pass | fail | unevaluable>`

These figures are a design estimate. They are not actual Lite performance evidence.

## 9. Phase 2 boundary

A GO recommendation must propose only:

```text
strict Lite
    or, on any uncertainty/new risk
existing Full Assurance
```

- Standard remains observation-only: `<yes | no>`
- User mode selection absent: `<yes | no>`
- Additional mode question absent: `<yes | no>`
- Monotonic Full Assurance fallback defined: `<yes | no>`
- Pilot can be disabled without breaking shadow or Full Assurance: `<yes | no>`
- Binary reversibility gate: `<pass | fail | unevaluable>`

## 10. Limitations and next action

- Unavailable measurements: `<list>`
- Sampling limitations: `<list>`
- Host-scope limitations: `<list>`
- Uncertainty that remains: `<list>`
- Next action: `<revise shadow and restart batch | stop | open separate Phase 2 design review>`

Even a GO report states only that a bounded pilot design is worth reviewing. Actual end-to-end Time to
Trusted Change improvement must be measured in Phase 2 before any broader activation.
