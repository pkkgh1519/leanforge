# Adaptive Assurance Pilot-Readiness Report

> Report one pinned study batch using redacted aggregates. This report may authorize a Phase 2 design
> review, never Lite activation.

## 1. Decision

- Recommendation: `<GO_TO_PHASE_2_DESIGN_REVIEW | NO_GO>`
- B candidate source commit/tree and contract blob: `<exact identities>`
- B generated/installed package digest by host: `<values>`
- A shadow-disabled control patch/tree digest: `<exact identities>`
- A generated/installed package digest by host: `<values>`
- A/B allowlisted source and generated diff verified: `<yes | no>`
- Predeclared execution-provenance method ID/version and binding/precondition rule by host: `<values>`
- A/B executed-package binding and precondition verified by host: `<yes | no>`
- Proposed pilot host scope: `<claude | codex | both | none>`
- Proposed topology: `<strict Lite vs existing Full Assurance | none>`
- Rationale: `<safety, tax, quality, burden, value, reversibility>`

## 2. Product gate summary

| Gate | Claude | Codex | Overall |
|---|---|---|---|
| Safety and wrong-path | `<result>` | `<result>` | `<result>` |
| Removable-gate intervention | `<result>` | `<result>` | `<result>` |
| Installed identity and smoke | `<result>` | `<result>` | `<result>` |
| A/B arm execution provenance | `<result>` | `<result>` | `<result>` |
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
A material false negative has only two valid dispositions: fixed and re-observed in a fresh pinned
batch, or `NO_GO`. It cannot be accepted, waived, or marked not Lite-relevant.

## 5. Installed-host behavior smoke

| Host | Provenance method ID/version | Installed digest matched | Execution provenance qualified | Total smokes | Usable smokes | Mode questions | Classification agents | Live changes | Telemetry blockers | Result |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| Claude | `<value>` | `<yes/no>` | `<yes/no>` | `<n>` | `<n>` | `<n>` | `<n>` | `<n>` | `<n>` | `<result>` |
| Codex | `<value>` | `<yes/no>` | `<yes/no>` | `<n>` | `<n>` | `<n>` | `<n>` | `<n>` | `<n>` | `<result>` |

Only provenance-qualified smokes count toward the 20-smoke floor.

## 6. Host-stratified paired A/B shadow-tax benchmark

For each proposed host provide a separate table. Do not pool host strata.

### `<host>`

- A control patch/tree digest: `<values>`
- A generated/installed package digest: `<values>`
- B candidate source/tree/contract identity: `<values>`
- B generated/installed package digest: `<values>`
- A/B allowlisted hook-only diff verified: `<yes | no>`
- Execution-provenance method ID/version and binding/precondition rule: `<predeclared value>`
- Planned A runs / provenance-qualified A runs: `<counts>`
- Planned B runs / provenance-qualified B runs: `<counts>`
- Declared-arm mismatches A/B: `<counts>`
- Execution session/reload/cache precondition failures A/B: `<counts>`
- Unqualified execution provenance A/B by reason: `<redacted counts>`
- Exclusions by reason: `<redacted counts>`
- Total planned pairs: `<n>`
- Both-arm-qualified matched pairs: `<n>`
- Both provenance-qualified and reached G7: `<n>`
- A-only stop / B-only stop / both stop: `<counts>`
- Successful-G7 rate A/B over provenance-qualified runs: `<rates>`

| Metric on both-arm-qualified matched successful-G7 pairs | A | B | Delta | Margin | Result |
|---|---:|---:|---:|---:|---|
| Median time-to-G7 seconds | `<v>` | `<v>` | `<%>` | `≤ +5%` | `<result>` |
| p90 time-to-G7 seconds | `<v>` | `<v>` | `<%>` | `≤ +10%` | `<result>` |
| Median tokens/usage | `<v>` | `<v>` | `<%>` | `<predeclared>` | `<result>` |
| Median tool calls | `<v>` | `<v>` | `<v>` | `<predeclared>` | `<result>` |
| Median files read | `<v>` | `<v>` | `<v>` | no broad scan | `<result>` |
| User questions | `<v>` | `<v>` | `<v>` | `0 classification-only` | `<result>` |
| Subagent dispatches | `<v>` | `<v>` | `<v>` | `0 classification-only` | `<result>` |

Only pairs whose A and B runs independently satisfy the predeclared session/reload/cache precondition and
match their declared arm and pinned installed package may enter the table. A declared-arm mismatch, a
planned run left unqualified after any permitted same-batch replacement, a B-only stop, lower B
successful-G7 rate, unavailable required metric, or failed margin fails this host. Any replacement must
follow the predeclared rule without inspecting performance or quality outcomes. No waiver, manual
acceptance, repository-local source read, or opposite-arm result may qualify a run.

## 7. Predeclared quality and user burden by host

Use only Part 6's both-arm-qualified matched successful-G7 comparison set.

| Host | B-only critical defects | Median score delta | B worse by ≥1 | B≤2 while A≥4 | Blocker-rate delta | Reply-turn delta | Approval-step delta | Summary-size delta | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Claude | `<n>` | `<v>` | `<%>` | `<n>` | `<v>` | `<v>` | `<v>` | `<%>` | `<result>` |
| Codex | `<n>` | `<v>` | `<%>` | `<n>` | `<v>` | `<v>` | `<v>` | `<%>` | `<result>` |

Required margins per proposed host: zero B-only critical defects, median score delta at least -0.25, no
more than 10% of pairs worse by one point or more, zero B≤2 when A≥4, no blocker-rate increase, zero
classification-only questions, zero added approval steps or mode-attributable reply turns, and no more
than 10% median approval-summary growth.

## 8. Cohort-level potential value in wall-clock seconds

Calculate separately for every proposed host using every enrolled eligible cycle in the denominator.
Assign zero removable benefit to every nonqualifying cycle.

| Host | Enrolled cycles | Realizable shadow-Lite→observed-Lite cycles | Sum removable seconds | Weighted removable benefit/cycle | Sum shadow-tax seconds | Sum promotion/recovery seconds | Expected cost/cycle | Ratio | Net seconds/cycle | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Claude | `<n>` | `<n>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<result>` |
| Codex | `<n>` | `<n>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<v>` | `<result>` |

The common unit is seconds. Weighted removable benefit is the sum of conservative removable seconds
across all enrolled cycles divided by enrolled cycles, with zero benefit assigned unless the shadow
prediction is Lite, the escalated observed class remains Lite, the case is Run-qualified, and no
removal-dependent intervention occurred. Expected cost uses the summed shadow and promotion/recovery seconds over the same denominator.
Benefit must be at least 2× cost, net seconds/cycle must be positive, and no benefit may depend on a
third Standard topology. These are design estimates, not actual Lite performance evidence.

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
