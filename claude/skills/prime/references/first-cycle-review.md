# first-cycle-review.md — the foundation-sufficiency rubric (shared)

The rubric for one question: *is the spec + Project Foundation deep enough to be the foundation of the
whole project?* Adversarial stance — find the holes, don't bless the work. Used **only in the first
cycle**, in **two places** that share this one rubric:

- **ELICIT (generative)** — the first-cycle loop (`elicitation.md`) presses against this floor *during
  dialogue*, while the user is present to fill a gap.
- **3-doc-gate (independent)** — the foundation-sufficiency pass (`3-doc-gate.md`) judges the
  *written* Foundation against this same rubric, from a fresh session that never saw the dialogue
  (the A=A backstop).

Both use the failure modes and floor below; they differ only in *when* and *with what session access*.

**Floor, not ceiling.** The failure modes and floor are the floor; how hard you press each is
risk-proportional judgment.

## Failure modes to hunt

- **Domain too shallow** — entity *names* present, but rules / invariants / edge-case dispositions
  missing. A concept without its four facts (what it is / does / cannot do / how it ends) is a name,
  not a model.
- **Domain too narrow** — a core applicable feature/entity is missing after the producer's evidence-backed breadth inventory. The absence of a ceremonial "are there others?" question is not itself a defect.
- **Technical grounding invalid** — a new/changed load-bearing choice remains open, or an unchanged fact is
  claimed repository-grounded without authoritative evidence. Do not require user confirmation for a
  preserved existing stack merely because this is the first Leanforge cycle.
- **Security disposition invalid** — an applicable security surface has only a generality, or `N/A` is
  asserted without a concrete reason.
- **Question inflation** — the workflow asks Prime-versus-direct mode, repeats a settled choice, or routes a
  repository-grounded/trivial fact back to the user.
- **Scoping mismatch** — the design is heavier or lighter than the project's confirmed character.
- **Outcome erosion** — Project identity or Future scope silently narrows, replaces, or invents the
  user-confirmed outcome or meaningful target state.
- **Execution leakage** — project-wide or future context appears in `spec.md`, `plan.md`, or the
  Execution Graph as current requirements, tasks, dependencies, abstractions, or compatibility work.
- **Vague modifiers remain** — "appropriately," "if needed," "as suitable" still present.

## Floor

- Every applicable domain concept meets `project-design-domain.md`'s depth floor or carries a reasoned
  `N/A`.
- Every new/changed user-owned technical decision is closed by user confirmation; every preserved current
  fact is backed by repository evidence.
- **Zero** vague modifiers and **zero** avoidable user questions.
- Design depth is consistent with the evidence-grounded CALIBRATE character profile.
- **Outcome alignment** — Project identity and Future scope preserve the confirmed outcome and target
  at the altitude the user confirmed, without adding unconfirmed strategy.
- **Non-leakage** — `spec.md`, `plan.md`, and the Execution Graph contain only the Current Delivery
  Slice; Foundation content is never implementation authorization.

## On a miss — reopen the foundation gap, don't self-fill

A finding here is one of two kinds:
- **Internally resolvable** (a vague modifier you can concretize from what's already on the record, an
  altitude slip) → fix it.
- **A gap only the user can fill** (a missing domain rule, an unsettled technical decision, a security
  policy) → **do not auto-fill it.** Auto-filling a foundation gap bakes a guess into the whole
  project.
  - If found by ELICIT (during dialogue): **reopen the foundation gap in the loop** — add it to the
    open-set and ask, in its mode (domain = extract, technical = present).
  - If found by the 3-doc-gate (after the docs are written): the orchestrator relays it to the user
    and reopens ELICIT for that gap only → updates SPEC/Foundation (`3-doc-gate.md`).

## Universality guard

Stack-agnostic. The rubric checks depth, breadth, and decision-closure — never conformance to a stack.
What counts as a domain rule or a technical decision is whatever this project is, judged at runtime.
