# Adaptive Assurance: shadow foundation and dormant Lite pilot

## Purpose

Leanforge currently applies almost the same high-assurance lifecycle to small deltas and high-risk
changes. This branch introduces deterministic advisory routing and a dormant Lite pilot without yet
changing the existing Prime or Run execution topology. The goal is to prove proportional assurance
before any safety gate is actually removed.

## Philosophy

The model chooses methods inside a narrow set of durable boundaries. The harness owns user intent,
permissions, irreversible operations, recovery, and executable evidence. It should not prescribe every
reading, dispatch, worktree, or review step when the risk does not earn that cost.

The operating rule is:

> no user-owned ambiguity survives; repository-derivable and reversible technical choices belong to
> the executing model.

## Closed routing

`adaptive-assurance-contract.json` defines the closed shadow router:

1. A first cycle routes to `assurance`.
2. Any closed hard trigger routes to `assurance`.
3. A delta routes to `lite` only when every required fact is present and the full Lite predicate holds.
4. Every other known case routes to `standard`.
5. Unknown contract fields and hard triggers are errors. Unknown runtime escalation signals fail closed
   to `assurance`.
6. Escalation is monotonic. A later signal can raise assurance but never lower it.

The Python router and shadow runner under `tools/` are development/test oracles, not packaged runtime
dependencies.

## Live shadow observation

Prime records an advisory `.leanforge/assurance-shadow.json` at the ELICIT exit, after user-owned
ambiguity has been settled. The hook lives in the already-loaded `grounds-gate.md` reference so it adds
no new Markdown reference load. It loads only the small closed JSON contract.

The sidecar is an ELICIT-exit prediction for the current Prime cycle, not a final 3-doc or Run outcome
and not an observation history. Prime removes any prior snapshot before deriving the new one. If it
cannot complete and validate the closed record, it leaves the sidecar absent without changing the
Full Assurance flow or asking the user merely for shadow telemetry. A later return to ELICIT replaces
the snapshot at its next exit; later reviewer, planning, and Run outcomes are compared separately.

The record schema, routing predicate, and decision-reason vocabulary are closed and timestamp-free.
The grounded fact classification still belongs to Prime; the shadow result has no execution authority.
It cannot alter Prime stages, questions, independent reviews, 3-doc output, user approval, Run
routing/worktrees, verification topology, recovery, or the current harness update policy.

## Phase 1.2 observation study

The manual study protocol lives in `adaptive-assurance-observation-study.md`; its copyable worksheet is
`adaptive-assurance-observation-template.md`.

The study preserves the ELICIT-exit prediction, independently adjudicates the final observed class
without reading that prediction, and reveals the shadow result only after the independent class is
fixed. It records exact, conservative, Lite-to-Standard, material-false-negative, and unevaluable
comparisons. A missing or contradictory record is not success, and every underclassified case receives
an individual disposition.

Each study batch uses one pinned Leanforge commit and contract blob. Router, predicate, vocabulary, or
grounding changes start a new batch rather than inheriting coverage from observations produced by a
different contract.

The protocol does not activate Lite or change live Prime or Run behavior. No completed observation
record belongs in this public repository. Records remain in a redacted private study workspace; only
redacted aggregates and underclassification summaries may be reported back.

A Phase 2 design review remains blocked until the study reaches representative coverage, has zero
unresolved Lite-to-Assurance cases, and receives a separate explicit activation decision.

## Durable-memory policy

A first cycle always needs project memory. For a future adaptive delta, harness synchronization should
be required only when durable project knowledge changes: architecture, public or durable contracts,
dependencies, modules, operations, or security rules. Small internal fixes should leave lightweight
per-change evidence instead of rewriting durable project documents merely because a cycle occurred.

This policy is still advisory in the live workflow.

## Evidence reuse

A prior verification may be reused only when the prior outcome is green and all of these values are
exactly equal:

- base SHA
- verification set
- environment fingerprint
- relevant-scope hash

Any missing, empty, or unequal value forbids reuse.

## Dormant Lite pilot

`adaptive-assurance-lite-pilot.json` describes the smallest useful Lite route while keeping
`activation: shadow`.

The prospective Lite route intentionally keeps the existing Prime→Run 3-doc interface and the hard
execution boundaries, while removing ceremony that a strictly eligible local reversible delta does not
earn:

- Prime keeps normal preconditions, a thin existing 3-doc, and explicit user approval, while skipping
  the two independent Prime reviewers and asking only user-owned decisions.
- Run keeps Git preflight, interrupted-run recovery guards, and contract/graph validation.
- Run executes directly without a worktree.
- Run performs targeted task verification and exactly one full completion verification; reusable
  evidence must satisfy the exact identity contract.
- Runnable services still receive the declared runtime smoke.
- The independent final reviewer is skipped, but the orchestrator still performs a final diff check.
- Harness synchronization is skipped only because Lite eligibility excludes durable project changes.
- User integration choice remains mandatory.
- Any discovered scope, verification, external-state, recovery, security/data, destructive, or
  user-intent risk promotes monotonically to Standard or Assurance before completion.

None of these Lite reductions are live yet.

## CI history requirement

The v1.9.0 exact-byte predecessor baseline reads raw Git blobs from an older commit. CI therefore uses
a full-history checkout (`fetch-depth: 0`); a shallow checkout cannot satisfy that release gate
reliably.

## Current activation boundary

This branch still does **not**:

- skip either Prime reviewer in live execution;
- change Run route topology;
- reduce task, integration, completion, smoke, or final-review gates;
- make harness synchronization conditional in the live workflow;
- alter recovery or user approval behavior;
- make study records execution authority.

The next step is to complete the Phase 1.2 observation study and hold an independent activation review.
Only a later, separately reviewed release may introduce a bounded Lite pilot. That release must remain
explicitly reversible and preserve monotonic escalation back to the existing Full Assurance path.
