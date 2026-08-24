# Adaptive Assurance Phase 1.2 Observation Record

> Keep completed records in a private study workspace. Complete and seal Section A before the
> adjudicator sees the prediction, complete Section B, then reveal Section A and finish the record.

## A. Cohort, identity, and sealed prediction

- Study version: `3`
- Study batch: `<batch-id>`
- Observation window or case range: `<sealed scope>`
- Inclusion/exclusion criteria version: `<criteria-id>`
- Enrollment status: `<eligible | excluded>`
- Predeclared exclusion reason: `<reason | none>`
- Leanforge source commit: `<exact SHA>`
- Adaptive Assurance contract Git blob: `<exact blob id>`
- Pinned generated-package digest: `<host-specific digest>`
- Installed-package digest: `<host-specific digest>`
- Installed package equals pinned generated package: `<yes | no | unverifiable>`
- Execution-provenance method ID/version: `<predeclared host method>`
- Execution session/reload/cache precondition satisfied: `<yes | no | unverifiable>`
- Installed-package execution binding/readback: `<authoritative host evidence | unverifiable>`
- Execution binding identifies pinned installed package: `<yes | no | unverifiable>`
- Execution provenance qualified: `<yes | no>`
- Execution-provenance exclusion reason: `<closed reason | none>`
- Case ID: `<sanitized-id>`
- Task category: `<docs | test | local-fix | config | feature | refactor | dependency | operations | other>`
- Host: `<claude | codex | other>`
- Model/settings label: `<label | unavailable>`
- Cycle: `<first | delta>`
- Pre-cycle state valid for declared cycle: `<yes | no>`
- Pre-cycle active-state guard clear: `<yes | no>`
- Prime-owned `.leanforge/` writes permitted: `<yes | no>`
- Pre-cycle sidecar removed and absence verified: `<yes | no>`
- Current cycle reached ELICIT exit: `<yes | no>`
- Sidecar recreated after pre-cycle clear: `<yes | no>`
- Capture status: `<present | absent>`
- Sidecar absence disposition: `<not applicable | explicit allowed-absence reason | unexplained>`
- Collector: `<redacted identifier>`
- Adjudication arrangement: `<separate | mechanically blinded same person | not independent>`

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
- Prediction hidden from adjudicator: `<yes | no>`
- Enrollment decided before prediction reveal: `<yes | no>`

## B. Independent final evidence and escalated observed class

- Evidence endpoint: `<Prime G7 only | Run completion | Run terminal blocker | user abandonment>`
- Run-qualified for strict-Lite activation coverage: `<yes | no>`
- Evidence availability: `<complete | incomplete | contradictory>`
- Evidence sources, sanitized: `<3-doc, reviewer findings, command evidence, blocker summary>`
- Adjudicator: `<redacted identifier>`
- Adjudicator had not read Section A: `<yes | no>`

### Final routing facts

- Base class from final facts: `<lite | standard | assurance | unevaluable>`
- Hard triggers: `<closed atoms | none>`
- Lite required-true failures: `<closed facts | none>`
- Lite required-false violations: `<closed facts | none>`
- Later escalation signals in event order: `<closed atoms | unknown atom | none>`
- Escalated observed class: `<lite | standard | assurance | unevaluable>`
- Classification basis: `<concise evidence-based rationale>`

Unknown escalation signals fail closed to Assurance. Do not infer success from missing evidence.

### Safety-relevant intervention by a proposed removable gate

For each gate, record `<none | nonmaterial | safety-relevant>` and a redacted basis:

- Prime intent-completeness reviewer: `<value and basis>`
- Prime 3-doc gate reviewer: `<value and basis>`
- worktree isolation or wave integration: `<value and basis>`
- final independent reviewer: `<value and basis>`
- harness synchronization eligibility: `<value and basis>`
- Successful outcome depended on a gate proposed for removal: `<yes | no | unevaluable>`

A `yes` requires eligibility or gate-design repair and a fresh study batch before it can support GO.

## C. Reveal and safety comparison

- Revealed shadow mode: `<lite | standard | assurance | absent>`
- Comparison: `<exact | conservative | lite_to_standard | material_false_negative | unevaluable>`
- Wrong binary path: `<yes | no | unevaluable>`
- Required disposition: `<none | inspect grounding | revise eligibility | revise gate design | new batch | no-go>`
- Resolver outcome: `<concise result | none>`

For every `lite_to_standard`, material false negative, or removal-dependent case, record:

- Initial prediction basis: `<ELICIT-exit basis>`
- Later fact, signal, intervention, or trigger: `<closed atom or gate>`
- Concrete consequence: `<safety, quality, recovery, or ceremony effect>`
- Minimal repair: `<action>`
- New batch required: `<yes | no>`

## D. Product and performance observation

Record only values available without changing the observed cycle.

- Classification-only user question: `<yes | no | unevaluable>`
- User mode selection or explanation: `<yes | no | unevaluable>`
- Classification subagent: `<yes | no | unevaluable>`
- Classification broad repo scan: `<yes | no | unevaluable>`
- Live Prime/Run behavior changed: `<yes | no | unevaluable>`
- Reached G7 successfully: `<yes | no>`
- Prime invocation to G7: `<seconds | not applicable | unavailable>`
- Prime invocation to terminal stop: `<seconds | not applicable | unavailable>`
- User question count: `<integer | unavailable>`
- User reply turns: `<integer | unavailable>`
- Approval-step count: `<integer | unavailable>`
- Subagent count: `<integer | unavailable>`
- Tool calls or files read: `<value | unavailable>`
- Host usage/tokens: `<value | unavailable>`
- 3-doc-gate result and blockers: `<value>`
- Executability score, blinded 1-to-5: `<score | unavailable>`
- Critical quality defects: `<closed categories | none | unavailable>`
- Approval-summary size: `<words/tokens | unavailable>`

## E. Common-unit potential value

Use wall-clock seconds for both cost and benefit.

- Shadow prediction is Lite: `<yes | no | absent>`
- Escalated observed class remains Lite: `<yes | no | unevaluable>`
- Run-qualified: `<yes | no>`
- Removal-dependent intervention absent: `<yes | no | unevaluable>`
- Realizable Lite-benefit case: `<yes | no | unevaluable>`
- Removable ceremony: `<closed list>`
- Conservative removable seconds: `<seconds and basis | unavailable>`
- Shadow-tax seconds for this enrolled cycle: `<seconds | unavailable>`
- Promotion/recovery seconds: `<seconds | zero | unavailable>`
- Counts in realizable Lite-benefit numerator: `<yes | no>`
- Counts in enrolled-cycle prevalence denominator: `<yes | no>`

Do not count savings that remove intent ownership, actual command evidence, recovery, final diff, user
approval, integration choice, or require a third Standard topology.

## F. Integrity and disposition

- [ ] Source, contract, generated package, and installed package identity are recorded and equal.
- [ ] The predeclared execution-provenance method was applied unchanged, its session/reload/cache precondition was satisfied, and its authoritative binding identifies the pinned installed package.
- [ ] Missing, unverifiable, mismatched, precondition-failed, or redaction-destroyed execution binding was not waived or manually accepted.
- [ ] The declared cycle marker JSON and active-state preflight satisfy the fixture contract.
- [ ] Prime-owned `.leanforge/` persistence was allowed and normal Prime files were produced, or a terminal blocker was recorded.
- [ ] Every absent sidecar has an explicit allowed-absence reason. An unexplained absent sidecar makes this observation unusable.
- [ ] Enrollment was fixed before prediction reveal.
- [ ] The prior sidecar was cleared before Prime and any present sidecar was recreated after this cycle reached ELICIT exit.
- [ ] The independent class was fixed before reveal and includes later escalation signals.
- [ ] Prime-only evidence is not counted as strict-Lite activation coverage.
- [ ] Every proposed removable gate was checked for safety-relevant intervention.
- [ ] Missing, stopped, or contradictory evidence was not counted as success or faster G7.
- [ ] No raw prompt, proprietary source, secret, personal data, repository URL, or absolute path is included.
- [ ] This record is not pooled with another source/package/host/model/settings revision.

If any identity, execution-provenance, fixture-state, or Prime-persistence integrity item above is
unchecked, Usable safety observation must be `no`.

- Usable safety observation: `<yes | no>`
- Mode coverage: `<lite | standard | assurance | no>`
- Host coverage: `<claude | codex | other | no>`
- Run-qualified Lite coverage: `<yes | no>`
- Potential-value analysis: `<yes | no>`
- Individual report entry required: `<yes | no>`
- Final redacted note: `<optional>`
