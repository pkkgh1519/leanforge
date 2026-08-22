# Adaptive Assurance Pilot-Readiness Report

> Report one pinned study batch using redacted aggregates. This report may authorize a Phase 2 design
> review, never Lite activation.

## 1. Decision

- Recommendation: `<GO_TO_PHASE_2_DESIGN_REVIEW | NO_GO>`
- Source commit: `<exact SHA>`
- Contract blob: `<exact blob id>`
- Generated-package digest by host: `<values>`
- Installed-package digest by host: `<values>`
- Proposed pilot host scope: `<claude | codex | both | none>`
- Proposed topology: `<strict Lite vs existing Full Assurance | none>`
- Rationale: `<safety, tax, quality, burden, value, reversibility>`

## 2. Product gate summary

| Gate | Claude | Codex | Overall |
|---|---|---|---|
| Safety and wrong-path | `<result>` | `<result>` | `<result>` |
| Removable-gate intervention | `<result>` | `<result>` | `<result>` |
| Installed identity and smoke | `<result>` | `<result>` | `<result>` |
| Shadow tax and endpoints | `<result>` | `<result>` | `<result>` |
| Quality | `<result>` | `<result>` | `<result>` |
| User burden | `<result>` | `<result>` | `<result>` |
| Prevalence-weighted value | `<result>` | `<result>` | `<result>` |
| Binary reversibility | `<result>` | `<result>` | `<result>` |

Every proposed host must pass independently. Missing or unevaluable data is NO-GO for that host.

## 3. Cohort, endpoints, and representative coverage

- Observation window and criteria: `<summary>`
- Eligible/enrolled/excluded/absent/unevaluable: `<counts>`
- Counts by host and shadow mode: `<table>`
- Counts by evidence endpoint: `<Prime-only | Run completion | Run blocker | abandonment>`
- Run-qualified shadow-Lite count by host: `<counts>`
- Counts by task category: `<redacted table>`
- Counts by Lite required-true failure: `<redacted table>`
- Counts by Lite required-false violation: `<redacted table>`
- Counts by later escalation family: `<redacted table>`
- Counts by hard-trigger family: `<redacted table>`
- Counts by removable-gate intervention: `<redacted table>`
- Per-host coverage floors satisfied: `<yes | no>`

## 4. Safety classification and interventions

### Shadow mode versus escalated observed class

| Host | Shadow | Observed Lite | Observed Standard | Observed Assurance | Unevaluable |
|---|---|---:|---:|---:|---:|
| `<host>` | Lite | `<n>` | `<n>` | `<n>` | `<n>` |
| `<host>` | Standard | `<n>` | `<n>` | `<n>` | `<n>` |
| `<host>` | Assurance | `<n>` | `<n>` | `<n>` | `<n>` |

- Exact/conservative/Lite-to-Standard/material-false-negative: `<counts by host>`
- Strict-Lite cases dependent on a removable gate: `<count by host>`
- Unresolved wrong-path cases: `<count>`
- Unresolved removal-dependent cases: `<count>`

For every wrong-path or removal-dependent case, include sanitized case ID, later fact/signal/gate,
consequence, disposition, and whether a new batch is required. Any unresolved instance is NO-GO.

## 5. Installed-host behavior smoke

| Host | Installed digest matched | Smokes | Mode questions | Classification agents | Live changes | Telemetry blockers | Result |
|---|---|---:|---:|---:|---:|---:|---|
| Claude | `<yes/no>` | `<n>` | `<n>` | `<n>` | `<n>` | `<n>` | `<result>` |
| Codex | `<yes/no>` | `<n>` | `<n>` | `<n>` | `<n>` | `<n>` | `<result>` |

## 6. Host-stratified paired A/B shadow-tax benchmark

For each proposed host provide a separate table. Do not pool host strata.

### `<host>`

- A revision: `2d2be39c01c9d19819acb0c658f07d06b06931a7`
- B revision: `<candidate SHA>`
- Generated and installed digest verified: `<yes | no>`
- Total pairs: `<n>`
- Both reached G7: `<n>`
- A-only stop / B-only stop / both stop: `<counts>`
- Successful-G7 rate A/B: `<rates>`

| Metric on matched successful-G7 pairs | A | B | Delta | Margin | Result |
|---|---:|---:|---:|---:|---|
| Median time-to-G7 seconds | `<v>` | `<v>` | `<%>` | `≤ +5%` | `<result>` |
| p90 time-to-G7 seconds | `<v>` | `<v>` | `<%>` | `≤ +10%` | `<result>` |
| Median tokens/usage | `<v>` | `<v>` | `<%>` | `<predeclared>` | `<result>` |
| Median tool calls | `<v>` | `<v>` | `<v>` | `<predeclared>` | `<result>` |
| Median files read | `<v>` | `<v>` | `<v>` | no broad scan | `<result>` |
| User questions | `<v>` | `<v>` | `<v>` | `0 classification-only` | `<result>` |
| Subagent dispatches | `<v>` | `<v>` | `<v>` | `0 classification-only` | `<result>` |

A B-only stop, lower B successful-G7 rate, unavailable required metric, or failed margin fails this host.

## 7. Predeclared quality and user burden by host

| Host | B-only critical defects | Median score delta | B worse by ≥1 | B≤2 while A≥4 | Blocker-rate delta | Summary-size delta | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Claude | `<n>` | `<v>` | `<%>` | `<n>` | `<v>` | `<%>` | `<result>` |
| Codex | `<n>` | `<v>` | `<%>` | `<n>` | `<v>` | `<%>` | `<result>` |

Required margins per proposed host: zero B-only critical defects, median score delta at least -0.25, no
more than 10% of pairs worse by one point or more, zero B≤2 when A≥4, no blocker-rate increase, zero
classification-only questions or approval steps, and no more than 10% median approval-summary growth.

## 8. Cohort-level potential value in wall-clock seconds

Calculate separately for every proposed host using all enrolled eligible cycles in the prevalence
denominator.

| Host | Enrolled cycles | Final strict-Lite Run-qualified cycles | Strict-Lite prevalence | Median removable seconds | Weighted removable benefit/cycle | Median shadow-tax seconds | Promotion/recovery seconds/cycle | Expected cost/cycle | Ratio | Net seconds/cycle | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Claude | `<n>` | `<n>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<result>` |
| Codex | `<n>` | `<n>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<result>` |

The common unit is seconds. Weighted removable benefit must be at least 2× expected cost, expected net
seconds per enrolled cycle must be positive, and no benefit may depend on a third Standard topology.
These are design estimates, not actual Lite performance evidence.

## 9. Phase 2 boundary

A GO recommendation must propose only:

```text
strict Lite
    or, on uncertainty or new risk
existing Full Assurance
```

- Standard remains observation-only: `<yes | no>`
- User mode selection absent: `<yes | no>`
- Additional mode question absent: `<yes | no>`
- Full Assurance fallback monotonic: `<yes | no>`
- Pilot disable leaves shadow and Full Assurance usable: `<yes | no>`
- Binary reversibility result: `<pass | fail | unevaluable>`

## 10. Limitations and next action

- Unavailable measurements: `<list>`
- Sampling and host limitations: `<list>`
- Remaining uncertainty: `<list>`
- Next action: `<restart batch | stop | open separate Phase 2 design review>`

Even a GO report only says a bounded pilot design is worth reviewing. Phase 2 must measure actual
end-to-end Time to Trusted Change before broader activation.
