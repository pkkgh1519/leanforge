# Harness Authority and Execution Graph Validation Follow-up

## Objective

Close two gaps found after the v1.6.7 outcome-preservation release:

1. the harness is sometimes described as one project-wide constraint even though its sections carry
   different authority, and Remaining/Future directions are non-executable context;
2. Prime can emit YAML that parses but does not match the rigid Execution Graph schema, leaving Run
   with a producer-side defect that must stop before execution.

## Design invariants

- The harness is a durable project record and operating context, not one undifferentiated constraint.
- Confirmed current invariants, contracts, approved decisions, and applicable operating rules constrain
  active work.
- Remaining may record a confirmed target commitment, but it is not current-cycle execution authority.
- Future directions are neither current commitments nor present implementation constraints.
- Prime alone translates a qualifying future direction into a narrow present-tense spec rule or hard
  gate; Run never infers one from status context.
- The Execution Graph schema, risk enum, dependency semantics, scheduler, and Run fail-closed behavior
  remain unchanged.

## Current Delivery Slice

Make the smallest contract correction that:

- replaces whole-harness/whole-doc constraint wording with section-authority wording;
- makes Prime validate the exact Execution Graph contract rather than merely accepting parseable YAML;
- adds regressions for the authority distinction and the known keyed-task malformed shape;
- regenerates Claude and Codex surfaces from canonical source.

## Non-goals

- no new workflow stage, user interview, gate dispatch, machine field, or Foundation section;
- no new runtime YAML parser, scheduler behavior, graph key, or risk value;
- no redesign of Remaining/Future classification;
- no direct edit to generated surfaces or installed plugin caches;
- no release, tag, remote push, or installed-copy update in this patch step.

## Authored file set

- `src/skills/run/references/harness-format.md`
- `src/skills/set/references/harness-format.md`
- `src/skills/run/references/harness-lifecycle.md`
- `src/skills/set/SKILL.md`
- `src/skills/prime/SKILL.md`
- `src/skills/prime/references/3-doc-gate.md`
- `tests/test_prime_outcome_preservation_contract.py`
- `tests/fixtures/prime-model-output/invalid-keyed-task-plan.md`
- this roadmap

Generated Claude/Codex counterparts are build outputs.

## Work sequence

### Phase 1 — Red contracts

Add focused assertions that fail while:

- the whole harness or all `docs/` are called a project constraint;
- section-specific authority and the Remaining/Future non-authorization rule are absent;
- Prime claims only that the graph parses;
- the known `task_1: {depends, risk}` root shape is not represented as an invalid regression case.

### Phase 2 — Minimal contract correction

Change only the owning contracts. Keep the existing detailed Future-direction guards and Run's
fail-closed consumer contract intact.

### Phase 3 — Build and deterministic validation

- run the focused contract test;
- run the full unittest suite;
- run `build/build.sh` and shared-reference parity checks;
- inspect the generated diff and run whitespace validation.

### Phase 4 — Behavioral evidence

In a fresh-session delta scenario, keep an unrelated Future direction unchanged without reopening
strategy or adding compatibility work. In a fresh Prime scenario, inspect the emitted `plan.md` and
require one fenced graph whose root contains `tasks` as a list plus `regen_barriers`; each task carries
`id`, `depends`, and optional valid `risk`. A merely parseable keyed-task root fails.

## Acceptance criteria

1. No owning contract calls the whole harness or all current `docs/` one project constraint.
2. The contract explicitly applies constraints only to normative records at their declared authority.
3. Remaining and Future directions do not authorize the current cycle or act as present constraints;
   Future directions remain non-commitments.
4. Run and Set shared harness-format sources remain byte-identical.
5. Prime requires exact graph-contract validation, not syntax parsing alone.
6. The known keyed-task root is locked as a rejected regression shape without adding a runtime parser.
7. Source, Codex, and Claude surfaces remain synchronized and the full suite passes.
8. Fresh behavioral evidence covers both unrelated-Future delta behavior and generated-plan shape.

## Validation record — 2026-07-15

- Focused outcome-preservation tests passed 14/14; the full repository suite passed 50/50.
- The official release build aligned v1.6.8 across all four manifests and CHANGELOG and preserved all three shared-reference parity checks.
- Prime, Run, and Set passed skill validation; whitespace and universal safety scans reported no
  finding.
- A fresh blind graph lane read only the patched canonical Prime contract and emitted one task (`T1`)
  under a `tasks` list with `depends: []`, `risk: RISKY`, and `regen_barriers: []`. It rejected a
  top-level `task_1:` mapping as invalid even though that shape is parseable YAML.
- A separate fresh blind delta lane treated an unrelated read-only-mobile Future direction as
  non-executable context while scoping a desktop-help typo fix. It reopened no strategy decision and
  added no mobile task, compatibility abstraction, dependency, or current constraint.

These blind lanes are prompt-level behavioral evidence against the patched canonical source. They do
not claim an installed-plugin or end-to-end Run execution test; release and installed-copy validation
are tracked separately from this semantic-patch evidence.
