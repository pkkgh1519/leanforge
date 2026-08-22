# Adaptive Assurance Phase 1.2: Shadow Observation Study

## Purpose

This study evaluates whether the Phase 1 ELICIT-exit shadow prediction is a safe basis for a later
bounded Lite pilot. It compares the prediction with an independently adjudicated class derived from
what the completed Prime and, when available, Run lifecycle actually revealed.

The study is observation only. It does not activate Lite, alter Prime or Run, select a route, skip a
reviewer or worktree, reuse verification, change harness synchronization, or influence the current
Full Assurance execution.

## Study question

The primary question is:

> Does any task predicted as `lite` later reveal an Assurance hard boundary or an unclassifiable
> material risk?

Secondary questions are:

- How often does a `lite` prediction become `standard` after the final scope is known?
- Does the router conservatively overclassify otherwise-Lite work?
- Are shadow records systematically absent or unevaluable?
- Does collecting the observation create any user question or workflow change?

## Pinned study batch

Every study batch is pinned to one exact Leanforge commit and the Git blob object ID of
`adaptive-assurance-contract.json`. Record both values on every worksheet.

Do not pool observations from different router or contract revisions. Any change to routing code,
contract vocabulary, Lite predicates, hard triggers, or shadow grounding closes the current batch and
starts a new study batch. Earlier records remain historical evidence but do not satisfy the new batch's
coverage target. This prevents a repaired router from inheriting confidence earned by a different
predicate.

## Unit of observation and evidence window

One observation covers one Prime cycle for one Current Delivery Slice. First and delta cycles are
recorded separately.

The collector preserves the latest `.leanforge/assurance-shadow.json` after Prime reaches G7 or stops;
the file represents Prime's final ELICIT-exit prediction for that cycle. The independent evidence window
ends at exactly one of these points:

1. Prime reaches G7 and no Run is performed;
2. Run reaches completion or a terminal blocker;
3. the user explicitly abandons the cycle.

A stopped or incomplete cycle is not silently treated as safe. If the available evidence cannot support
one class, the observation is `unevaluable`.

## Roles and blinded adjudication

The shadow router must not generate its own expected outcome. Separate collector and adjudicator roles
are preferred.

- **Collector:** mechanically copies the sidecar unchanged, records the pinned revision, assigns a
  sanitized `case_id`, and seals the shadow prediction before adjudication.
- **Adjudicator:** classifies the final observed work without reading the sidecar mode, reasons,
  triggers, or Lite diagnostics.
- **Resolver:** handles a disagreement or insufficient basis. A second independent adjudicator may
  resolve it; otherwise the record remains `unevaluable`.

One person may perform both collector and adjudicator roles only when Section A is copied and sealed
mechanically without inspecting its contents. If that person saw or remembers the prediction, the
adjudication is not blinded; use a second adjudicator or mark the record `unevaluable`.

## Data minimization

Completed observation records are study data, not repository product artifacts. Do not commit them to
the public Leanforge repository.

Record only the minimum derived information needed for comparison:

- the pinned Leanforge commit and contract blob object ID;
- a sanitized case identifier and coarse task category;
- the exact shadow payload;
- the independently observed class and concise basis;
- newly discovered closed facts, hard triggers, or escalation signals;
- the comparison result and required disposition.

Do not record raw prompts, proprietary source, patches, secrets, personal data, repository URLs,
customer identifiers, absolute paths, or environment-specific credentials. Evidence pointers may be
kept in a private study workspace, but the report exported from that workspace must remain redacted.

## Collection procedure

1. Run the existing Full Assurance Prime and Run behavior unchanged.
2. After Prime reaches G7 or stops, mechanically copy the sidecar into the sealed prediction section of
   the template and record the pinned commit and contract blob. If the sidecar is absent, record
   `Capture status: absent`; do not reconstruct or guess it.
3. Without reading the prediction, adjudicate the final observed class from the completed 3-doc,
   independent reviewer findings, actual Run evidence, and any terminal blocker in the evidence window.
   Apply the pinned contract revision that produced the prediction.
4. Reveal the prediction only after the observed class and rationale are fixed.
5. Assign one comparison label from the closed study labels below.
6. Record whether shadow collection itself caused any additional user question or live workflow change.
7. Preserve the record outside the public repository. The observation never changes the current cycle.

Do not ask the user a question merely to make the study record more complete. Missing study evidence
produces `unevaluable`, not a new product decision.

## Independent observed-class rubric

Use the pinned canonical Adaptive Assurance contract against the final observed scope, not the initial
shadow payload.

- `assurance`: the cycle is first-cycle work; a closed hard trigger is present; or a material risk cannot
  be classified and therefore becomes `unknown_material_risk`.
- `lite`: the cycle is a delta, no hard trigger is present, every Lite required-true fact remains true,
  and every Lite required-false fact remains false through the end of the evidence window.
- `standard`: the case is fully classifiable and known, has no Assurance hard trigger, but the complete
  Lite predicate does not hold.
- `unevaluable`: final evidence is missing, contradictory, inaccessible, or too weak to support one of
  the three classes.

An adjudicator may use later evidence that was unavailable at ELICIT exit, but must not rewrite what the
shadow predictor knew. The study compares two different observation times; it does not pretend they are
the same judgment.

## Comparison labels

Mode order is `lite < standard < assurance`.

- `exact`: shadow mode equals the independently observed class.
- `conservative`: shadow mode is higher than the independently observed class.
- `lite_to_standard`: shadow mode is `lite` and the observed class is `standard`.
- `material_false_negative`: observed class is `assurance` and the shadow mode is lower.
- `unevaluable`: the sidecar is absent, the observed class is unevaluable, or the comparison cannot be
  supported without guessing.

Every `lite_to_standard` and `material_false_negative` record requires an individual written
explanation. Aggregate percentages must not hide an underclassified case.

## Study coverage target

For one pinned router revision, the initial activation discussion requires at least 35 usable
observations:

- at least 15 shadow `lite` predictions;
- at least 10 shadow `standard` predictions;
- at least 10 shadow `assurance` predictions.

The sample should cover first cycle, local reversible deltas, multiple tasks or write areas, verification
gaps, durable changes, runtime-service changes, and representative hard-trigger families. This is a
coverage floor for an engineering decision, not a claim of statistical significance.

Absent and unevaluable records are reported separately and do not count toward the usable total.
Synthetic contract cases remain test oracles; they do not count as real shadow observations.

## Activation decision gates

The study cannot activate Lite by itself. A separate reviewed release and explicit user decision are
required even when every gate below is satisfied.

The bounded Lite pilot remains **NO-GO** when any of these holds:

- any shadow `lite` case is independently observed as `assurance`;
- a material false negative has not been explained and repaired or explicitly shown not to affect Lite;
- a `lite_to_standard` pattern reveals an unresolved systemic eligibility or fact-grounding gap;
- absent or unevaluable records prevent representative comparison;
- shadow collection caused additional user questions or changed live Prime or Run behavior;
- the coverage target is not met.

A Standard-to-Assurance material false negative also requires router investigation even though Standard
is not a Lite activation route. If an investigation changes the router or contract, start a new pinned
study batch; do not carry the old batch's coverage count forward.

Proceeding to a Phase 2 design review requires all underclassifications to be individually dispositioned,
zero unresolved Lite-to-Assurance cases, representative coverage, and explicit confirmation that the
pilot can return monotonically to the existing Full Assurance path.

## Study report

A study report contains only redacted aggregates and individually redacted underclassification
summaries:

- the pinned Leanforge commit and contract blob object ID;
- counts by shadow mode and independently observed class;
- counts by comparison label;
- sidecar absence and unevaluable counts;
- each `lite_to_standard` and `material_false_negative` case with its causal fact or trigger;
- any shadow-caused user question or workflow change;
- a `GO_TO_PHASE_2_REVIEW` or `NO_GO` recommendation.

The report must distinguish "no observed failure" from "proved safe." Small observational samples can
support a bounded pilot decision, not universal correctness.

## Non-goals

Phase 1.2 does not add:

- automatic telemetry upload, a database, dashboard, trace DSL, or analytics service;
- a new sidecar schema or observation history inside `.leanforge/`;
- live Prime or Run consumption of study records;
- `activation: active`, a Lite execution route, reviewer/worktree skipping, or conditional harness sync;
- evidence-reuse integration or changes to `RUN-COMPLETION-REUSE`;
- model training, automatic threshold tuning, or a workflow simulator.

Use `adaptive-assurance-observation-template.md` as the manual worksheet. Completed worksheets remain
outside the public repository.
