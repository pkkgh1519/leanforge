# Adaptive Assurance: shadow foundation and Strict Lite alpha handoff

## Purpose

Leanforge currently applies almost the same high-assurance lifecycle to small deltas and high-risk
changes. Adaptive Assurance explores whether the same trusted-change outcome can be reached with less
unnecessary ceremony for strictly eligible local, reversible work.

The product goal is defined by `business-rules.md`: minimize **Time to Trusted Change** while preserving
intent fidelity, safety, actual verification evidence, recovery, user approval, and integration choice.
Mode classification, sidecars, reviewers, and worktrees are internal means rather than product outcomes.

## Philosophy

The model chooses methods inside a narrow set of durable boundaries. The harness owns user intent,
permissions, irreversible operations, recovery, and executable evidence. It should not prescribe every
reading, dispatch, worktree, or review step when the risk does not earn that cost.

The operating rule is:

> no user-owned ambiguity survives; repository-derivable and reversible technical choices belong to
> the executing model.

Adaptive Assurance must not improve classifier accuracy by creating new user questions, repo scans,
subagents, approval steps, or a second orchestration. An accurate classifier whose fixed cost makes small
Prime cycles slower is not a product improvement.

## Closed shadow routing

`adaptive-assurance-contract.json` defines the closed advisory router:

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
ambiguity has been settled. The hook lives in the already-loaded `grounds-gate.md` reference and loads
only the small closed JSON contract.

The sidecar is an ELICIT-exit prediction for the current Prime cycle, not a final 3-doc or Run outcome
and not an observation history. Prime removes any prior snapshot before deriving the new one. If it
cannot complete and validate the closed record, it leaves the sidecar absent without changing the Full
Assurance flow or asking the user merely for shadow telemetry.

The shadow result has no execution authority. It cannot alter Prime stages, questions, independent
reviews, 3-doc output, user approval, Run routing/worktrees, verification topology, recovery, integration
choice, or the current harness update policy.

## Strict Lite alpha contract

`adaptive-assurance-lite-pilot.json` now defines a separately reviewed Strict Lite alpha canary with
`activation: default_off`. The canary is inert unless the internal activation file is present and exact.

The prospective Lite route keeps the existing Prime→Run 3-doc interface and hard execution boundaries,
while identifying ceremony that a strictly eligible local reversible delta may not earn:

- Prime keeps normal preconditions, a thin existing 3-doc, and explicit user approval.
- Run keeps Git preflight, interrupted-run recovery guards, contract/graph validation, targeted task
  verification, one full completion verification, declared runtime smoke, final diff check, actual
  command/exit evidence, and user integration choice.
- Strict Lite alpha omits only the Prime intent-completeness reviewer and a proven no-op harness
  synchronization. It keeps the 3-doc gate, existing direct route, full completion verification, final
  independent review, recovery, and user integration choice.
- Any discovered scope, verification, external-state, recovery, security/data, destructive, or
  user-intent risk promotes monotonically to the existing Full Assurance path.

These reductions are available only behind the default-off internal canary activation file.

## First activation topology

The first live activation, if separately approved, must be binary:

```text
strict Lite
    or, on any uncertainty/new risk
existing Full Assurance
```

`standard` remains an observation label and does not become a third live workflow. The user never
selects a mode. A three-topology orchestration, workflow DSL, or duplicated mode-specific Prime/Run is
outside the approved direction until a separate net-benefit case is proven.

## Phase 1.2 pilot-readiness study

The full research protocol is intentionally outside `docs/`, because Leanforge Prime reads project docs
on delta work and the study machinery must not become recurring product context.

- Protocol: `../research/adaptive-assurance/pilot-readiness-study.md`
- Per-cycle worksheet: `../research/adaptive-assurance/observation-template.md`
- Final report template: `../research/adaptive-assurance/pilot-readiness-report-template.md`

Phase 1.2 evaluates the following together:

1. zero unresolved Lite-to-Standard or Lite-to-Assurance wrong-path decisions after later escalation;
2. strict-Lite activation evidence is Run-qualified and does not depend on a gate proposed for removal;
3. installed Claude/Codex package digests match the pinned generated packages;
4. every proposed host independently passes endpoint-safe shadow-tax and predeclared quality margins;
5. mode selection adds no user question, approval step, subagent, broad scan, or reading burden;
6. prevalence-weighted removable seconds exceed shadow plus promotion/recovery cost by at least 2×;
7. a binary, monotonic Full Assurance fallback remains explicit and reversible.

The study uses revision-pinned real observations, installed-host behavior smokes, and a paired A/B
benchmark whose control is derived from the same candidate tree with only the live shadow hook disabled. Its output is
`GO_TO_PHASE_2_DESIGN_REVIEW` or `NO_GO`. It never activates Lite.

## Durable-memory policy

A first cycle always needs project memory. For a future adaptive delta, harness synchronization should
be required only when durable project knowledge changes: architecture, public or durable contracts,
dependencies, modules, operations, or security rules. Small internal fixes should leave lightweight
per-change evidence instead of rewriting durable project documents merely because a cycle occurred.

This policy is still advisory in the live workflow.

## Evidence reuse

A prior verification may be reused only when the prior outcome is green and base SHA, verification set,
environment fingerprint, and relevant-scope hash are exactly equal. Missing, empty, or unequal values
forbid reuse.

This rule is dormant and cannot replace or weaken the existing `RUN-COMPLETION-REUSE` contract. Any
future integration must add constraints to the existing Run meaning rather than create a competing
weaker authority.

## CI history requirement

The v1.9.0 exact-byte predecessor baseline reads raw Git blobs from an older commit. CI therefore uses
a full-history checkout (`fetch-depth: 0`); a shallow checkout cannot satisfy that release gate
reliably.

## Current activation boundary

The Strict Lite alpha canary is **default off** and internal. When enabled for a qualifying delta, it:

- skips only Prime's intent-completeness reviewer;
- reuses the existing direct Run route rather than adding a route;
- keeps completion verification, runtime smoke, final independent review, recovery, approval, and
  integration ownership;
- skips harness synchronization only after proving no durable project knowledge changed;
- promotes monotonically to Full Assurance on uncertainty or new risk.

This candidate does not claim Time to Trusted Change improvement. Broader or default activation remains
closed until installed-host paired measurement demonstrates net benefit and preserved safety.
