# grounds-gate.md — ELICIT question filter for generated candidates

A source-difference candidate from DECOMPOSE or a probe-generated "unsaid" candidate from ELICIT's
re-measurement becomes a **confident question** only if it clears this gate. The detectors
deliberately raise more than survives (they are liberal on purpose); this gate is what keeps the
dialogue from degrading into generic "have you thought about concurrency?" spray that fatigues the
user. ELICIT applies this one standard to candidates from either detector.

## The three grounds (state all three, per site)

A candidate is a confident question only if you can state **all three**:

1. **The specific site** — the exact requirement / code path / endpoint / entity it lands on (not
   "X in general").
2. **Why it remains unresolved** — use the branch that matches the candidate:
   - **For a probe-generated gap:** give a positive argument that the spec, the plan, the code, the
     harness, or a framework/convention default does not already handle it. "Might be missing" or
     "unclear" is not enough; actively rule out existing coverage.
   - **For a source-difference candidate:** give a positive argument that source or section authority,
     scope, time horizon, and settled context neither reconcile the claims nor determine which governs
     the exact site. The fact that one or both claims are already recorded is evidence to compare, not
     proof that the opposition is covered or resolved.
3. **The concrete consequence** if it is left unaddressed.

If you cannot ground all three, do **not** raise it as a confident question.

## Asymmetric default

**Insufficient grounds → not a confident question.** This is the inverse of a keep-by-default pass:
escalate only what you can ground. The candidate-specific "why unresolved" test (ground 2) is where
most candidates die — it removes probe false positives and harmless source variance while keeping
grounded structural gaps and normative conflicts.

A source-difference candidate for which authority, scope, time horizon, and settled context fail to
resolve the claims, and that is materially incompatible at the same site with a concrete consequence,
satisfies the source-difference form of ground 2. It **must not be demoted merely because** one or both
claims appear in the harness, code, input, or an attached document.

## A load-bearing gap candidate may NOT be *silently* dropped (anti-evasion)

The drop default exists to suppress **noise** — not to let the agent route a load-bearing gap it does
not want to ask around ELICIT's exit bar (`elicitation.md` — "no guess survives"). That exit only
governs candidates that *became questions*; a candidate killed here never reaches it. So a lazy agent
could under-argue ground ② ("a framework default probably covers this") to drop a load-bearing
dimension before the bar ever sees it. **Close that route:** when the dropped probe candidate is on a
**load-bearing dimension the decision-surface accounting raised** (`elicitation.md`), the drop is
**not silent** — it must be **recorded in the spec as that dimension's
`N/A — covered by [the ground-② argument]`** (e.g. "Concurrency: N/A — the framework's transaction
default serializes these writes"). This converts a silent suppression into an auditable, falsifiable
claim the independent 3-doc-gate can check against the code. Dropping noise stays silent; dropping a
load-bearing dimension leaves evidence.

## Two tiers (so the gate never silently buries a real gap or conflict)

- **Confident questions** — grounded on all three. These are the questions you actually ask (ordered
  by leverage, each carrying a recommended default — see `elicitation.md` for the recommend-first
  rule).
- **Low-confidence candidates** — probe gaps that fail the existing-coverage branch, or source
  differences lacking enough evidence to establish material incompatibility or consequence. Hold them
  briefly for a quick scan; do not press them as blocking.

The low-confidence tier recovers the rare real-but-hard-to-ground item the gate would otherwise drop,
so the asymmetric default never *silently* buries a real gap or conflict.

## Universality guard

Stack-agnostic. The three grounds and the two tiers apply to any candidate in any stack; what counts
as a framework default, a convention, or applicable section authority is discovered from the project
at runtime, never assumed here.

## Adaptive Assurance shadow observation

At the **ELICIT exit**, after every user-owned ambiguity has been settled or explicitly dispositioned,
load `adaptive-assurance-contract.json` once and record an advisory **ELICIT-exit prediction** in
`.leanforge/assurance-shadow.json`.

This prediction is the current Prime cycle's replaceable snapshot, not a final 3-doc or Run outcome
and not an observation history. Before deriving it, remove any existing sidecar. Any later return to
ELICIT must replace the snapshot at the next ELICIT exit; later reviewer, planning, and Run outcomes
are compared separately when evaluating shadow observations.

Use only facts already grounded by ORIENT/ELICIT plus the closed contract vocabulary. Do **not** ask the
user a question merely to improve this shadow classification. If a material risk cannot be classified,
record `unknown_material_risk`, which routes the shadow result to `assurance`. If a complete record
cannot be derived and validated, leave the sidecar absent; do not ask the user or block Prime merely
to preserve shadow telemetry.

The record is deterministic and contains exactly:

```json
{
  "schema_version": 1,
  "shadow_only": true,
  "cycle": "first | delta",
  "mode": "lite | standard | assurance",
  "reasons": ["<closed decision_reasons atom>"],
  "hard_triggers": ["<closed hard trigger names>"],
  "missing_lite_required_true": ["<closed fact names>"],
  "violated_lite_required_false": ["<closed fact names>"],
  "harness_sync": true
}
```

After validating the complete record, write it atomically under `.leanforge/`; never incrementally edit
the destination. Omit timestamps or environment-specific paths. `harness_sync` is advisory only: first
cycle is always `true`; on a delta it is `true` only when a closed durable-change trigger is present.

**Shadow means no authority.** This record must not change Prime's stage sequence, question policy,
independent reviewers, 3-doc contents, user approval, Run routing/worktrees, verification topology,
recovery behavior, or the live harness update policy. The current Full Assurance behavior remains
authoritative until a later release explicitly activates an adaptive route.
