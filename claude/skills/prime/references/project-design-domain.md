# project-design-domain.md — first-cycle DESIGN (domain model)

Realize the project's **domain model** from the user and authoritative existing-project evidence.
The user owns desired new or changed behavior; code, tests, and docs may ground current behavior the user
asked to preserve. Never let repository evidence overrule explicit user intent, but never re-ask an
unchanged, test-backed rule merely because Leanforge has no harness yet. The domain floor below is what
the ELICIT loop must close on the domain axis; depth follows the project character and the actual slice.
Order is gap-driven, not a fixed phase after technical.

**Floor, not ceiling.** You already know how to hold a domain conversation. This file does **not**
script it — it blocks the failure modes you fall into and lays the depth/breadth floor. The ceiling
is open: how you lead, in what order, is your judgment.

## Asymmetric depth — but domain is always deep

Spend depth where the domain is core; go light on the peripheral (don't fatigue the user). **But:**
even when CALIBRATE judged the project "small," do **not** compromise the *accuracy* of a domain rule.
A small project has *fewer* rules, not *shallower* ones — each rule still meets the depth floor below.

## Failure modes and guardrails

- **Surface-skimming.** Receiving a feature's name is the *start*, not the end. Dig until the
  feature's rules are at a verifiable level — keep pressing past the label.
- **Missing implicit rules.** Don't capture only what the user said aloud. For *every* identified
  concept, confirm its **lifecycle** (created → changes → destroyed) and its **exceptions** (what
  happens off the normal path). The unspoken rules live in those two places.
- **Accepting vagueness.** No vague modifiers ("appropriate," "suitable," "as needed") survive into
  the spec. Dig until each is concrete.
- **Implementation bleed.** Use no implementation terms in domain design. Not "how is it stored" but
  "what must happen." The domain is behavior, not mechanism-of-storage.
- **Rule fabrication.** A new or changed product rule must come from the user's words or be one the
  user confirmed. An unchanged current rule may be grounded by authoritative code/tests/docs when the
  user explicitly preserves current behavior. Never infer desired future behavior from implementation.
- **Domain-term confusion.** Where the same word means different things in different contexts,
  distinguish and pin each meaning explicitly.

## Depth floor

- Every applicable identified concept has the facts its lifecycle requires: **what it is / what it
  does / what it cannot do / what happens when it ends**. For a stateless value or pure transformation,
  non-applicable lifecycle fields are recorded `N/A` with a concrete reason rather than turned into a
  user question.
- Every rule is convertible to a test case (state it so a test is derivable from the rule alone).
- No vague modifier ("appropriately," "if needed") remains in the spec.
- Mechanism, not just outcome: "when condition A and condition B hold simultaneously, transition to
  state X," not "becomes state X." Each "must" paired with its "must not."

## Breadth guard (against laziness / premature closure)

Depth and breadth are independent — meeting the depth floor on the concepts you found does **not**
mean you found them all. Perform an explicit internal breadth inventory over the requested slice, nearby
repository surface, actors, values, states, and colliding concepts. A user-facing breadth question is
required **only** when that inventory leaves a concrete load-bearing entity/feature/rule user-owned and
unresolved. A narrow existing-repository change whose affected domain is closed by the request and code may
finish with zero questions. The disposition and evidence, not the existence of a ceremonial "are there
others?" question, prove breadth.

## Cross-validation (interactions between concepts)

Per-concept lifecycle checks don't surface the edges where two concepts *meet*. Check the
interactions and dependencies between identified concepts: when concept A changes, what is its
effect on concept B? The edge cases that bite live at those junctions — a lifecycle pass on each
concept in isolation will miss them.

## What this produces

A domain model captured at the evidence-aware depth/breadth floor above: applicable entities and
their relationships, state transitions, calculation logic, explicit edge dispositions, and domain-term
definitions. For an established repository, record the durable domain supported by authoritative evidence
and the current task; do not interrogate the user about unrelated hypothetical future features merely to
make the Foundation look project-wide. *This task's* WHAT lives in `spec.md`; the Foundation remains
non-executable context. `Run` later turns the durable model into `business-rules.md`.

## Universality guard

Stack-agnostic. "Entity," "state," "rule" are domain concepts, not stack artifacts; the actual
domain is whatever the user describes, drawn out at runtime. No framework or storage technology is
named in domain design.
