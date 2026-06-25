# Leanforge SDD-lite Stage 1 Roadmap

## Objective

Apply a minimal SDD-lite Stage 1 upgrade to Leanforge without changing its core lifecycle, parallel execution model, or harness strategy.

The upgrade strengthens behavior-changing work only:

1. Acceptance Criteria to Verification Evidence traceability
2. Behavior-first test evidence
3. Ceremony budget review

## Non-goals

- Do not redesign Leanforge around SDD.
- Do not add Workboard support.
- Do not add committed spec snapshots.
- Do not change greenfield scaffold or vertical-slice policy.
- Do not change `.leanforge/` git tracking policy.
- Do not change `Leanforge:Set` for this stage.
- Do not force the new matrix for documentation-only, mechanical, formatting-only, or scaffold-only work.

## Scope

### Prime

Prime owns producing the acceptance/evidence contract.

Required changes:

- Add an `Acceptance & Evidence Matrix` to `spec.md` when the requested work changes observable behavior.
- Keep the matrix compact and omit it for non-behavioral work; use a short non-matrix verification note instead.
- Express each acceptance criterion as externally observable behavior.
- Map each acceptance criterion to a verification command or verification strategy and expected evidence.
- State unresolved or unavailable verification explicitly instead of treating it as pass.

### Run

Run owns executing and auditing the contract.

Required changes:

- Require implementers to report evidence against relevant acceptance criteria when the spec provides the matrix.
- Treat missing AC evidence as unfinished behavior, not as a reporting detail.
- Reject file existence, source string checks, symbol existence, skipped tests, weakened assertions, or swallowed exceptions as sufficient evidence for behavior ACs.
- Add final-review lenses for evidence integrity and ceremony budget.

### Run TDD

Run TDD remains a thin wrapper over Run.

Required changes:

- Keep selective TDD only for behavior-changing work.
- Derive tests from observable behavior and ACs when available.
- Preserve vertical red-green-refactor; do not batch all tests first.
- Reject implementation-detail tests, skipped tests, and weakened assertions as AC evidence.

## Design rules

- Prime writes the contract; Run consumes it; reviewers verify traceability.
- Add concise instructions at existing authority points rather than broad new workflows.
- Prefer short bullet rules and compact examples over long templates.
- Keep `Set` out of scope unless a later stage explicitly turns these rules into durable project policy.
- Treat ceremony review as a justification check, not an automatic deletion order.

## Acceptance criteria for this branch

| AC | Observable behavior | Verification | Expected evidence |
|---|---|---|---|
| AC-01 | Prime instructions require a compact Acceptance & Evidence Matrix for behavior-changing specs only. | Unit/contract test over source and generated skill surfaces. | Test exits 0 and finds matrix terms in Prime surfaces. |
| AC-02 | Run implementer/reviewer instructions require AC evidence and reject shallow evidence. | Unit/contract test over source and generated skill surfaces. | Test exits 0 and finds evidence-integrity guard terms in Run surfaces. |
| AC-03 | Run reviewer instructions include ceremony budget checks without requiring automatic removal. | Unit/contract test over source and generated skill surfaces. | Test exits 0 and finds ceremony-budget terms in Run reviewer surfaces. |
| AC-04 | Run TDD reinforces behavior-first AC-derived tests while remaining subordinate to Run. | Unit/contract test over Codex run-tdd surface. | Test exits 0 and finds behavior-first guard terms in run-tdd. |
| AC-05 | Generated Claude and Codex plugin surfaces match canonical sources after build. | Existing surface parity tests. | Tests exit 0. |
| AC-06 | Version metadata remains consistent after the patch release bump. | Build script version parity guard. | Build exits 0 with matching v1.6.6 manifests and changelog. |

## Implementation phases

1. Document this roadmap before editing skill behavior.
2. Patch Prime output-format/spec-writing instructions.
3. Patch Run implementer and reviewer prompts.
4. Patch Codex-only Run TDD wrapper.
5. Add focused contract tests for Stage 1 terms and non-goals.
6. Bump patch version to v1.6.6.
7. Run build to regenerate platform surfaces.
8. Run the repository tests.

## Risk controls

- Keep all new rules conditional on behavior-changing work.
- Do not introduce new scripts or dependencies.
- Do not change execution graph semantics.
- Do not change worktree or recovery mechanics.
- Do not edit generated plugin surfaces directly; regenerate them from source/platform inputs.
