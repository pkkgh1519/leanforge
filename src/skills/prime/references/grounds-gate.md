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
