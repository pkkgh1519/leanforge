# Adaptive Assurance Pilot-Readiness Study

## Purpose

This study asks whether Adaptive Assurance can plausibly reduce Leanforge's **Time to Trusted Change**
without weakening intent fidelity, safety, verification quality, user experience, or recovery. The
product north star and user artifacts are defined authoritatively in `docs/business-rules.md`.

Phase 1.2 does not activate Lite and cannot prove actual Lite net benefit. It may only decide whether
there is enough evidence to design a small, reversible Phase 2 pilot. The final outcome is
`GO_TO_PHASE_2_DESIGN_REVIEW` or `NO_GO`, never `ACTIVATE_LITE`.

The study has five required dimensions:

1. **Safety:** strict-Lite predictions do not miss Standard or Assurance boundaries, and success does
   not depend on a gate the pilot proposes to remove.
2. **Shadow tax:** classification and sidecar recording do not materially slow or distract Prime.
3. **Quality:** intent completeness and 3-doc executability do not deteriorate.
4. **User burden:** mode selection creates no extra question, approval step, or reading burden.
5. **Potential value and reversibility:** prevalence-weighted removable ceremony exceeds measured
   shadow tax in one common cost unit, and every uncertain case returns to Full Assurance.

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
- Pilot work remains separately releasable and reversible; shadow and Full Assurance remain usable if
  the pilot is disabled.

Any proposal that introduces three independent live workflows, a mode-selection stage, a workflow DSL,
or duplicated orchestration is outside this study's admissible Phase 2 design.

## Study outputs

The final redacted Pilot-Readiness Report contains:

- the pinned source, contract, generated-package, installed-package, host, and model/settings identity;
- safety-observation counts, evidence endpoints, coverage dimensions, and every underclassification;
- every safety-relevant intervention by a gate the pilot proposes to remove;
- host-stratified paired A/B shadow-tax and quality results;
- a cohort-level potential-value estimate in wall-clock seconds;
- proposed pilot host scope and binary fallback boundary;
- a `GO_TO_PHASE_2_DESIGN_REVIEW` or `NO_GO` recommendation.

Completed per-cycle records and raw benchmark logs remain outside the public repository. Only redacted
aggregates and causal summaries may be published.

## Pinned study batch and installed identity

The safety-observation cohort is pinned to one exact candidate identity:

- one Leanforge source commit and source-tree digest;
- the Git blob object ID of `adaptive-assurance-contract.json`;
- the rebuilt generated-package tree digest for each host;
- the installed-package tree digest actually executed by each host;
- the host and model/settings labels available from the host;
- a predeclared observation window or consecutive case range;
- objective inclusion and exclusion criteria.

Before enrollment, rebuild the pinned candidate with `build/build.sh`, verify canonical-to-generated
parity, and compare each installed package digest with its pinned generated package digest. A mismatch or
an unverifiable installed package makes that host observation unusable. A marketplace version label
alone is not package identity.

Also capture installed-package execution provenance from the host's selected-plugin binding, skill-load
trace, or another authoritative host readback. The provenance must identify the same installed package
whose digest was pinned. Merely reading byte-equivalent source from the repository does not establish
that the installed package executed. A repository-local source skill does not count as installed-package
provenance. If the host exposes no authoritative binding or trace, record the observation as unusable
rather than inferring provenance from the response.

Before the batch opens, predeclare one execution-provenance method per host. Give it a stable method ID
and version, identify the authoritative command, UI, trace, or readback, list the fields and deterministic
comparison required to bind that evidence to the installed-package digest, state fresh-session, reload,
and cache conditions, and define a redaction-safe retained artifact. Apply the method unchanged to A and
B. A method selected or relaxed after outcomes are visible is invalid. Missing, unverifiable, mismatched,
precondition-failed, or redaction-destroyed binding is unqualified; no waiver or manual acceptance can
convert it to qualified evidence.

The paired A/B benchmark pins two identities separately:

- **B candidate arm:** the candidate source commit/tree, contract blob, generated-package digest, and
  installed-package digest;
- **A shadow-disabled control arm:** a deterministic control tree derived from the B candidate tree by
  removing only the live Adaptive Assurance shadow-observation hook from canonical `grounds-gate.md`,
  then rebuilding the corresponding generated surfaces; record the control patch digest, control-tree
  digest, generated-package digest, and installed-package digest.

Verify that the A/B source diff is exactly the allowlisted hook removal and that the generated-package
diff is exactly its generated Claude/Codex copies. Product docs, Prime/Run stages, prompts, contracts,
reviewers, and all non-shadow behavior are identical across arms. The historical pre-shadow commit may
remain provenance, but it is not the performance control because unrelated docs and workflow changes
would confound the measurement.

Do not pool observations from materially different candidate identities. For the benchmark, prohibit
identity drift within either arm and within a matched pair; the intentional, allowlisted A/B hook
difference does not close the batch. Any other routing, predicate, hard-trigger, package, host, model,
or settings change closes the batch and starts a new one.

## Cohort integrity and host floors

Before reading any prediction, predeclare the observation window, host scope, and objective enrollment
rules. Use a consecutive time window, consecutive case range, or fixed maximum number of eligible
cycles.

Record every eligible Prime cycle, including absent sidecars, terminal blockers, user abandonment, and
unevaluable outcomes. An exclusion is allowed only for a predeclared objective reason and remains in the
report by reason. An unexpected prediction, inconvenient result, or difficult adjudication is not an
exclusion reason.

Predeclare and verify the fixture's Prime cycle state before enrollment. For a declared delta case, a
valid `.leanforge/status.json` is present before Prime starts. It JSON-parses to exactly
`{ "initialized": true }`. A first-cycle fixture has neither the marker nor a Leanforge-shaped harness.
A marker-loss state is not an eligible small-delta smoke or benchmark fixture. The fixture also has no
`.leanforge/run.json`, registered Leanforge worktree, active root 3-doc, or conflicting `.dryforge/`
state that would invoke Prime's active-state guard. The cycle-state fixture is byte-identical across A
and B. Do not ask Prime to infer or repair fixture state during a behavior smoke or paired benchmark run.

The stimulus must preserve normal Prime persistence. Prime-owned `.leanforge/` planning and shadow
writes are allowed and required when their normal completion conditions are met; a "do not modify
files" instruction must be narrowed to product files rather than Prime state. Product, test, config,
dependency, and generated-package files remain read-only. A run that returns inline pseudo-documents
without the normal Prime files is not a completed Prime observation.

Before invoking Prime for each enrolled cycle, remove any existing advisory
`.leanforge/assurance-shadow.json` and verify the path is absent. This pre-cycle clear has no execution
authority; it prevents a prior cycle's deterministic snapshot from being misattributed to the new cycle.
A sidecar counts as present only when the current cycle subsequently reaches ELICIT exit and recreates
the file. If pre-clear cannot be verified, or the cycle stops before ELICIT exit, record the sidecar as
absent and the shadow comparison as `unevaluable`.

A host-limited pilot requires the full overall coverage floor on that host. A two-host pilot requires the
overall floor plus, for each host, at least 15 usable observations containing at least 5 shadow-Lite, 3
shadow-Standard, and 3 shadow-Assurance predictions. Evidence from an under-covered host can support at
most a pilot that excludes that host.

## Part A: safety observation

### Unit and evidence window

One observation covers one Prime cycle for one Current Delivery Slice. The collector preserves the
latest sidecar after Prime reaches G7 or stops. The independent evidence window ends when:

1. Prime reaches G7 and no Run follows;
2. Run reaches completion or a terminal blocker; or
3. the user explicitly abandons the cycle.

Prime-only records remain visible in cohort accounting, but they do not count toward strict-Lite
activation coverage or removable-gate safety evidence. Every one of the 15 required shadow-Lite
activation observations must reach Run completion or a Run terminal blocker. Incomplete or
contradictory evidence is `unevaluable`, never inferred safe.

### Blinded roles

- **Collector:** mechanically copies the exact sidecar and identity data, then seals the prediction.
- **Adjudicator:** determines the observed class and gate interventions without reading the prediction.
- **Resolver:** uses a second independent adjudicator for disagreement or insufficient basis; otherwise
  the record remains `unevaluable`.

One person may collect and adjudicate only when Section A is copied and sealed mechanically without
inspecting its contents. If the person saw or remembers the prediction, use a second adjudicator or mark
the result `unevaluable`.

### Observed-class rubric and escalation

First apply the pinned canonical routing contract to the final observed scope:

- `assurance`: first-cycle work, a closed hard trigger, or `unknown_material_risk`;
- `lite`: delta, no hard trigger, every Lite required-true fact true, every required-false fact false;
- `standard`: fully classifiable, no Assurance hard trigger, but the complete Lite predicate fails;
- `unevaluable`: evidence cannot support one class without guessing.

Then apply every later runtime escalation signal monotonically in event order. A Standard signal raises
Lite to Standard; an Assurance signal raises Lite or Standard to Assurance; an unknown signal fails
closed to Assurance. The resulting escalated class is the independently observed class used for all
comparisons.

### Safety-relevant interventions by removable gates

For every gate the binary pilot proposes to omit, record whether it found or prevented a material issue:

- Prime intent-completeness reviewer;
- Prime 3-doc gate reviewer;
- worktree isolation or wave integration gate;
- final independent reviewer;
- harness synchronization when durable-change eligibility was wrong.

A safety-relevant intervention is any finding or isolation effect that changed user-owned intent,
prevented an incorrect or unsafe implementation, discovered a verification/recovery gap, or was needed
to make the final outcome trustworthy. A strict-Lite case whose success depended on such an intervention
is not evidence that the gate is removable. It requires eligibility or gate-design repair and a fresh
pinned batch. Zero unresolved removal-dependent strict-Lite cases are required for GO.

### Comparison labels

Mode order is `lite < standard < assurance`.

- `exact`: shadow and escalated observed class match;
- `conservative`: shadow class is higher;
- `lite_to_standard`: shadow Lite, observed Standard;
- `material_false_negative`: observed Assurance, shadow lower;
- `unevaluable`: absent sidecar, unevaluable class, failed identity, or failed blinding/integrity.

Every `lite_to_standard` and `material_false_negative` requires an individual explanation and
resolution. In the binary topology, both transitions are wrong-path decisions. An unresolved instance of
either transition makes the batch NO-GO.
A `material_false_negative` cannot be accepted, waived, or declared Lite-irrelevant. It requires
grounding or eligibility repair followed by re-observation in a fresh pinned batch; otherwise the result
is `NO_GO`.

### Coverage floor and reportable dimensions

For one pinned revision, collect at least 35 usable real observations:

- at least 15 shadow `lite`, all Run-qualified;
- at least 10 shadow `standard`;
- at least 10 shadow `assurance`.

Cover and report redacted counts by host, coarse task category, evidence endpoint, Lite required-true
failure, Lite required-false violation, later escalation family, hard-trigger family, and removable-gate
intervention. Synthetic fixtures are test oracles and do not count as real observations.

## Part B: installed-host behavior smoke

Run at least 20 installed-package behavior smokes across the proposed host scope. When both hosts are in
scope, include at least 10 Claude Code and 10 Codex smokes. Each smoke first confirms that the installed
package digest equals the pinned generated-package digest.

Each smoke records authoritative installed-package execution provenance tying the host's selected skill
or plugin load to that same pinned installed package. A digest match without this binding is unusable and
does not count toward the 20-smoke floor. Repository-local source reads do not substitute for the
installed-package binding.

Each smoke checks that:

- Prime reaches the same live stages as Full Assurance;
- no question is asked merely for mode classification;
- no new classification subagent is dispatched;
- no mode choice is presented to the user;
- the sidecar does not alter the 3-doc, approval, Run, recovery, or harness behavior;
- malformed or absent telemetry does not block the product outcome.

A smoke is not a safety-observation substitute and does not count toward the 35-case coverage floor.

## Part C: paired A/B shadow-tax benchmark

### Arms and workload

- **A, shadow-disabled control:** the separately pinned control derived from B by the allowlisted hook
  removal described above.
- **B, candidate shadow revision:** the exact pinned candidate source, contract, generated package, and
  installed package.

Before any run, verify the A/B source and generated-package diffs against the allowlist. Use five
representative small delta cases with fixed repository snapshots, replayable sanitized or synthetic
benchmark prompts, and predeclared user answers. For a two-host study, run:

```text
5 cases × 2 hosts × 2 versions × 5 repetitions = 100 runs
```

Use fresh sessions, identical host/model/settings within each pair, and randomized A/B order. Do not
pool materially different configurations.

Before each run, record the declared arm, pinned installed-package digest, predeclared
execution-provenance method ID and version, whether its fresh-session, reload, and cache precondition was
satisfied, authoritative binding or readback, whether that binding identifies the pinned installed
package for the declared arm, provenance-qualified status, and exclusion reason. Both arms must
independently satisfy the precondition and identify their declared arm before a pair can enter endpoint,
latency, quality, or user-burden analysis. A missing, unverifiable, mismatched, precondition-failed, or
redaction-destroyed binding does not count toward the planned repetition floor, remains in batch
accounting, and may be replaced only under a predeclared same-batch rerun rule applied without inspecting
its performance or quality outcome. No waiver, manual acceptance, repository-local source read, or
opposite-arm result can qualify it.

### Endpoint integrity

Time-to-G7, quality, and user-burden statistics include only matched A/B pairs where both runs are
provenance-qualified for their declared arms and both reach G7 successfully. A terminal stop is never
counted as a faster G7 result. Record planned and provenance-qualified run counts, both-arm-qualified
matched pairs, declared-arm mismatches, execution-precondition failures, unqualified bindings by reason,
exclusions by reason, successful-G7 denominators, and terminal-stop rates separately for A and B on every
host. A declared-arm mismatch, a planned repetition left unqualified after any permitted same-batch
replacement, a B-only stop, or a lower successful-G7 rate fails the gate. Mismatched endpoints are
excluded from latency estimates and remain explicit failures or unevaluable pairs.

### Measurements

For every run, record:

- declared arm: `A | B`;
- pinned installed-package digest for that arm;
- execution-provenance method ID and version;
- execution session/reload/cache precondition satisfied: `yes | no | unverifiable`;
- authoritative execution binding or readback;
- binding matches the declared arm's pinned installed package: `yes | no | unverifiable`;
- execution provenance qualified: `yes | no`;
- exclusion reason: `<closed reason | none>`;
- wall-clock from Prime invocation to G7, or separately to a terminal stop, when available;
- input/output token or closest host-provided usage measure;
- tool-call count and files read;
- subagent dispatch count;
- user questions and user reply turns;
- approval-summary and 3-doc size;
- 3-doc-gate outcome and blocker count;
- sidecar creation outcome.

### Host-stratified shadow-tax gates

Predeclare margins before running the batch and evaluate every proposed host independently. An aggregate
result cannot mask a failed or unavailable host stratum. The initial default gates per host are:

- declared-arm execution mismatches: exactly `0`;
- every planned A and B repetition is provenance-qualified after any permitted same-batch replacement;
- additional classification-only user questions: exactly `0`;
- additional classification subagents: exactly `0`;
- additional broad repo scans attributable to classification: exactly `0`;
- structural live overhead: at most one small contract read and one sidecar replacement;
- median successful time-to-G7 regression: no more than `5%`;
- p90 successful time-to-G7 regression: no more than `10%`;
- B-only terminal stops or lower successful-G7 rate: exactly `0`;
- no material token/tool increase without a demonstrated offsetting user benefit.

If a required metric is unavailable on a host, the study cannot pass that dimension for that host. It
may narrow the pilot scope or remain `NO_GO`.

## Part D: predeclared quality and user-burden comparison

Before collecting the batch, predeclare the blinded rubric, aggregation, and margins below. The reviewer
does not know whether a 3-doc came from A or B.

For every paired case admitted by Part C's provenance and endpoint rules, record critical defects:

- surviving user-owned ambiguity;
- invalid graph or missing spec-to-task coverage;
- 3-doc-gate blocker;
- unsafe or unjustified scope inflation.

Also assign a 1-to-5 executability score: 5 is complete and directly executable, 4 has only minor
nonblocking defects, 3 needs material repair, 2 has major ambiguity or coverage failure, and 1 is
unusable.

Quality passes per proposed host only when:

- B introduces zero critical defects not present in its paired A result;
- B's median executability score is no more than 0.25 below A;
- no more than 10% of pairs score B at least one full point below A;
- B has no case scoring 2 or lower when A scores 4 or higher;
- B's 3-doc-gate blocker rate does not exceed A's.

User burden passes only with zero classification-only questions, zero added approval steps, no increase
in reply turns attributable to mode selection, and no more than 10% increase in median approval-summary
size per host. Record question count, reply-turn count, and approval-step count for every admitted paired
run and report their host-stratified deltas. Missing required quality or burden data is `unevaluable`, not
a pass.

## Part E: cohort-level potential value in one cost unit

The common cost unit is wall-clock seconds. Do not divide seconds by tokens, tool calls, or files read.
Those remain secondary diagnostic metrics.

Because Lite is dormant, Phase 1.2 estimates rather than proves savings. A **realizable Lite-benefit
case** must have a shadow prediction of `lite`, remain `lite` after final facts and later escalation, reach
Run completion or a Run terminal blocker, and have no removal-dependent intervention. Only such a case
would actually enter the proposed strict-Lite branch and can contribute removable Full Assurance
ceremony. Estimate its removable wall-clock seconds using measured step timestamps where available and
conservative lower bounds otherwise. Exclude safety, recovery, actual command evidence, final diff,
approval, integration choice, and any saving that depends on a third `standard` topology.

Shadow tax is paid by every enrolled cycle, including absent and unevaluable observations. Assign zero
removable benefit to every cycle that is not a realizable Lite-benefit case. In particular, a conservative
shadow Standard or Assurance prediction that later adjudicates as Lite still follows Full Assurance in
the binary router and contributes zero benefit. Compute in seconds:

```text
weighted removable benefit per enrolled cycle
  = sum(conservative removable seconds across all enrolled cycles) / enrolled cycle count

expected cost per enrolled cycle
  = (sum(shadow-tax seconds) + sum(promotion/recovery seconds)) / enrolled cycle count
```

The initial gate requires weighted removable benefit to be at least `2×` expected cost and expected net
seconds per enrolled cycle to be positive, separately for every proposed host. This sum-over-cohort
formula, rather than prevalence multiplied by a Lite-case median, prevents heterogeneous Lite savings
from being overstated. Best-case savings, unobserved eligible work, Prime-only Lite records, and
conservative non-Lite predictions do not count.

This is a pilot-design buffer, not actual production benefit. Phase 2 must measure end-to-end Time to
Trusted Change before broader activation.

## GO / NO-GO decision

`GO_TO_PHASE_2_DESIGN_REVIEW` requires all of the following:

- zero unresolved Lite-to-Standard and Lite-to-Assurance wrong-path cases;
- zero unresolved strict-Lite cases dependent on a gate proposed for removal;
- representative, revision-pinned, Run-qualified, per-host safety coverage;
- installed package identity and behavior-smoke coverage for every proposed host;
- zero declared-arm execution mismatches and execution-provenance-qualified planned A/B repetitions for
  every proposed host;
- each host independently passes endpoint and shadow-tax non-inferiority;
- each host independently passes the predeclared quality and user-burden margins;
- each host independently passes the prevalence-weighted common-unit value gate;
- the proposed Phase 2 topology is binary and immediately returns to Full Assurance.

The report is `NO_GO` when any requirement is missing, unevaluable, or repaired by changing eligibility,
routing, or package identity without starting a fresh pinned batch.

A GO decision authorizes only a separate Phase 2 design review. It does not authorize Lite execution,
reviewer/worktree skipping, evidence reuse, conditional harness sync, merge, release, or deployment.

## Data minimization

Do not commit completed observations or raw benchmark logs in Markdown, JSON, CSV, TSV, text, log, or
other formats. Real-observation raw prompts, proprietary source or patches, secrets, personal data,
customer identifiers, repository URLs, absolute paths, and credentials are prohibited.

For reproducibility, the private study workspace may retain the exact sanitized or synthetic benchmark
prompts, fixed repository fixtures, predeclared answers, randomization seed, and runner script used for
Part C. These fixtures must contain no proprietary or personal material and must remain outside the
public repository. Published output remains limited to pinned digests, aggregated metrics, and redacted
causal summaries.

## Non-goals

Phase 1.2 does not add automatic telemetry, a database, dashboard, trace DSL, analytics service,
workflow simulator, sidecar history, live study consumption, `activation: active`, a Standard execution
topology, evidence-reuse integration, model training, or automatic threshold tuning.

Use `observation-template.md` for individual records and `pilot-readiness-report-template.md` for the
final redacted report.
