# Adaptive Assurance Pilot-Readiness Study

## Purpose

This study asks whether Adaptive Assurance can plausibly reduce Leanforge's **Time to Trusted Change**
without weakening intent fidelity, safety, verification quality, user experience, or recovery. The
product north star and user artifacts are defined authoritatively in `docs/business-rules.md`.

Phase 1.2 does not activate Lite and therefore cannot prove actual Lite net benefit. It can only decide
whether there is enough evidence to design a small, reversible Phase 2 pilot. The final study outcome is
`GO_TO_PHASE_2_DESIGN_REVIEW` or `NO_GO`, never `ACTIVATE_LITE`.

The study has five required dimensions:

1. **Safety:** strict-Lite predictions do not miss Assurance material risk.
2. **Shadow tax:** classification and sidecar recording do not materially slow or distract Prime.
3. **Quality:** intent completeness and 3-doc executability do not deteriorate.
4. **User burden:** mode selection creates no extra question, approval step, or reading burden.
5. **Potential value and reversibility:** enough real work could benefit from a binary Lite pilot, and
   every uncertain case can return monotonically to the existing Full Assurance path.

A classifier can be accurate and still fail this study if its fixed cost outweighs the ceremony it may
later remove.

## Product and topology constraints

Adaptive Assurance is an internal transmission, not a user-facing mode chooser.

- The user never selects `lite | standard | assurance`.
- Classification uses only facts already grounded by Prime and does not justify an extra repo scan,
  subagent, user question, approval, or document.
- The first live pilot has only two execution paths: **strict Lite** and **existing Full Assurance**.
- `standard` remains an observational label. It does not become a third live orchestration in Phase 2.
- A newly discovered risk promotes monotonically to the existing Full Assurance path. The same cycle
  never drops back to Lite.
- Pilot work must remain separately releasable and reversible; shadow and Full Assurance remain usable
  if the pilot is disabled.

Any proposal that introduces three independent live workflows, a mode-selection stage, a workflow DSL,
or duplicated orchestration is outside this study's admissible Phase 2 design.

## Study outputs

The final redacted Pilot-Readiness Report contains:

- the pinned router and contract revision;
- safety-observation counts and every underclassification disposition;
- the paired A/B shadow-tax benchmark;
- quality and user-burden comparisons;
- a conservative estimate of removable ceremony versus measured shadow tax;
- proposed pilot host scope and binary fallback boundary;
- a `GO_TO_PHASE_2_DESIGN_REVIEW` or `NO_GO` recommendation.

Completed per-cycle records and raw benchmark logs remain outside the public repository. Only redacted
aggregates and redacted underclassification summaries may be published.

## Pinned study batch

Every batch is pinned to:

- one exact Leanforge commit;
- the Git blob object ID of `adaptive-assurance-contract.json`;
- the host and model/settings labels available from the host;
- a predeclared observation window or consecutive case range;
- objective inclusion and exclusion criteria.

Do not pool observations or benchmark runs from materially different router, contract, host, model, or
settings revisions. Any change to routing code, contract vocabulary, Lite predicates, hard triggers, or
shadow grounding closes the batch and starts a new one. Earlier records remain historical evidence but
do not satisfy the new batch's coverage gate.

## Cohort integrity

Before reading any prediction, predeclare the observation window, host scope, and objective enrollment
rules. Use a consecutive time window, consecutive case range, or fixed maximum number of eligible
cycles.

Record every eligible Prime cycle, including absent sidecars, terminal blockers, user abandonment, and
unevaluable outcomes. An exclusion is allowed only for a predeclared objective reason and remains in the
report by reason. An unexpected prediction, inconvenient result, or difficult adjudication is not an
exclusion reason.

If a future pilot is intended for both Claude Code and Codex, usable observations and overhead evidence
must represent both hosts. Evidence from one host can support at most a host-limited pilot.

## Part A — safety observation

### Unit and evidence window

One observation covers one Prime cycle for one Current Delivery Slice. The collector preserves the
latest sidecar after Prime reaches G7 or stops. The independent evidence window ends when:

1. Prime reaches G7 and no Run follows;
2. Run reaches completion or a terminal blocker; or
3. the user explicitly abandons the cycle.

Incomplete or contradictory evidence is `unevaluable`, never inferred safe.

### Blinded roles

- **Collector:** mechanically copies the exact sidecar, records the pinned revision, and seals the
  prediction.
- **Adjudicator:** determines the final observed class from the final 3-doc, independent reviewer
  findings, actual Run evidence, and terminal blockers without reading the prediction.
- **Resolver:** uses a second independent adjudicator for disagreement or insufficient basis; otherwise
  the record remains `unevaluable`.

One person may collect and adjudicate only when Section A is copied and sealed mechanically without
inspecting its contents. If the person saw or remembers the prediction, use a second adjudicator or mark
the result `unevaluable`.

### Observed-class rubric

Apply the pinned canonical contract to the final observed scope:

- `assurance`: first-cycle work, a closed hard trigger, or `unknown_material_risk`;
- `lite`: delta, no hard trigger, every Lite required-true fact true, every required-false fact false;
- `standard`: fully classifiable, no Assurance hard trigger, but the complete Lite predicate fails;
- `unevaluable`: evidence cannot support one class without guessing.

The adjudicator may use later evidence unavailable at ELICIT exit but must not rewrite what the shadow
predictor knew. The study compares two observation times.

### Comparison labels

Mode order is `lite < standard < assurance`.

- `exact`: shadow and observed class match;
- `conservative`: shadow class is higher;
- `lite_to_standard`: shadow Lite, observed Standard;
- `material_false_negative`: observed Assurance, shadow lower;
- `unevaluable`: absent sidecar, unevaluable observed class, or failed blinding/integrity.

Every `lite_to_standard` and `material_false_negative` requires an individual explanation and
resolution. Aggregate percentages never hide an underclassified case.

### Coverage floor

For one pinned revision, collect at least 35 usable real observations:

- at least 15 shadow `lite`;
- at least 10 shadow `standard`;
- at least 10 shadow `assurance`.

Cover local reversible deltas, multiple tasks/write areas, verification gaps, durable changes,
runtime-service changes, first cycle, and representative hard-trigger families. Synthetic fixtures are
test oracles and do not count as real observations.

## Part B — installed-host behavior smoke

Run at least 20 installed-package behavior smokes across the proposed host scope. When both hosts are in
scope, include at least 10 Claude Code and 10 Codex smokes.

Each smoke checks that:

- Prime reaches the same live stages as Full Assurance;
- no question is asked merely for mode classification;
- no new classification subagent is dispatched;
- no mode choice is presented to the user;
- the sidecar is advisory and does not alter the 3-doc, approval, Run, recovery, or harness behavior;
- malformed or absent telemetry does not block the product outcome.

A smoke is not a safety-observation substitute and does not count toward the 35-case coverage floor.

## Part C — paired A/B shadow-tax benchmark

### Versions

- **A — pre-shadow Full Assurance:** `2d2be39c01c9d19819acb0c658f07d06b06931a7`.
- **B — candidate shadow revision:** the exact commit and contract blob pinned by the batch.

The comparison measures the cost of adding shadow classification while both versions still execute the
same Full Assurance product flow.

### Workload and repetition

Use five representative small delta cases with fixed repository snapshots, replayable prompts, and
predeclared user answers. Include documentation/test/local-fix/config or similarly low-blast cases where
a fixed classification tax would be most visible.

For a two-host study, run:

```text
5 cases × 2 hosts × 2 versions × 5 repetitions = 100 runs
```

Use fresh sessions, the same available host/model/settings within each pair, and randomized A/B order.
Do not pool materially different model or host configurations. Record unavailable telemetry as
unavailable rather than reconstructing it.

### Measurements

For every run record, when the host exposes the value:

- wall-clock from Prime invocation to G7 or terminal stop;
- input/output token or closest host-provided usage measure;
- tool-call count and files read;
- subagent dispatch count;
- number of user questions and user reply turns;
- approval-summary and 3-doc size;
- 3-doc-gate outcome and blocker count;
- sidecar creation outcome.

The benchmark itself is offline study work and must not add user-facing steps to normal Prime.

### Shadow-tax gates

Predeclare margins before running the batch. The initial default gates are:

- additional classification-only user questions: exactly `0`;
- additional classification subagents: exactly `0`;
- additional broad repo scans attributable to classification: exactly `0`;
- structural live overhead: at most one small contract read and one sidecar replacement;
- median time-to-G7 regression: no more than `5%`;
- p90 time-to-G7 regression: no more than `10%`;
- no material increase in token/tool cost without a demonstrated offsetting user benefit.

If a required metric is unavailable on a host, the report cannot claim that dimension passed for that
host. It may narrow the proposed pilot scope or remain `NO_GO`.

## Part D — quality and user-burden comparison

Use a blinded reviewer who does not know whether a 3-doc came from A or B. Compare:

- surviving user-owned ambiguity;
- spec completeness and unwanted scope inflation;
- graph validity and spec↔task coverage;
- 3-doc-gate blocker rate;
- amount the user must read to approve the same outcome;
- question count, reply turns, and approval steps.

B must show no material quality deterioration and no mode-induced user burden. A faster run with weaker
intent fidelity is not a product improvement; a safer-looking run with extra internal questions is also
not a product improvement.

## Part E — potential-value estimate

Because Lite is dormant, Phase 1.2 estimates rather than proves savings. For each observed strict-Lite
candidate, identify the exact ceremony a binary pilot proposes to omit while preserving the hard
boundaries. Use measured Full Assurance step costs when available and conservative bounds otherwise.

The estimate must:

- exclude safety, recovery, actual command evidence, final diff, approval, and integration choice;
- exclude any saving that depends on a third `standard` execution topology;
- subtract measured shadow tax and expected promotion/recovery cost;
- report uncertainty and avoid treating best-case savings as expected value.

The initial potential-value gate requires the conservative median removable-ceremony estimate to exceed
the measured median shadow tax by at least `2×`. This is a pilot-design buffer, not a claim of actual
production benefit. Phase 2 must measure real end-to-end Time to Trusted Change before any broader
activation.

## GO / NO-GO decision

`GO_TO_PHASE_2_DESIGN_REVIEW` requires all of the following:

- zero unresolved shadow Lite → observed Assurance cases;
- every underclassification individually explained and dispositioned;
- representative, revision-pinned safety coverage;
- installed-host smoke coverage for the proposed host scope;
- shadow-tax non-inferiority gates pass;
- no material 3-doc quality deterioration;
- no additional mode-induced user burden;
- conservative potential value exceeds measured shadow tax;
- the proposed Phase 2 topology is binary and can immediately return to existing Full Assurance.

The report is `NO_GO` when any requirement is missing, unevaluable, or repaired by changing the router
without starting a fresh pinned batch.

A GO decision authorizes only a separate Phase 2 design review. It does not authorize Lite execution,
reviewer/worktree skipping, evidence reuse, conditional harness sync, merge, release, or deployment.

## Data minimization

Do not commit completed observation records or raw benchmark logs to the public repository. Record only
sanitized identifiers, pinned revisions, exact shadow payloads, derived classes, aggregated metrics, and
redacted causal summaries.

Do not record raw prompts, proprietary source or patches, secrets, personal data, customer identifiers,
repository URLs, absolute paths, or credentials. Private evidence pointers remain in the private study
workspace.

## Non-goals

Phase 1.2 does not add:

- automatic telemetry upload, database, dashboard, trace DSL, analytics service, or workflow simulator;
- a new sidecar schema or observation history under `.leanforge/`;
- live consumption of study records by Prime or Run;
- `activation: active`, a Lite execution route, or a Standard execution topology;
- evidence-reuse integration or changes to `RUN-COMPLETION-REUSE`;
- model training or automatic threshold tuning.

Use `observation-template.md` for individual records and `pilot-readiness-report-template.md` for the
final redacted decision report.
