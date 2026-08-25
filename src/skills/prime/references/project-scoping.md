# project-scoping.md — first-cycle CALIBRATE (project character → depth profile)

The calibration step of the first-cycle ELICIT loop (no harness exists yet). Before deepening any
axis, establish the project's **identity, scale, and constraints** — its character — which then sets
the *depth floor* of every foundation axis the loop will close (domain, technical, and beyond). Loaded
and run only in the first cycle. (It is not a separate phase that must finish before the rest — it
seeds the floor; the loop then closes the axes in gap-driven order, see `elicitation.md`.)

**Floor, not ceiling.** This sets the floor and the guardrails; how you reach the user's confirmed
read of the project is your judgment.

## The mechanism — evidence-grounded read, confirmation only when needed

Do **not** freeze scope from the user's opening description, but do not manufacture a calibration
interview either. Form the project-character read from the user's goal **and** the existing repository.
A first cycle without a Leanforge harness can still be an established project whose purpose, audience,
scale, language, tests, and constraints are already evident.

Flow: **tentative read → repository/user evidence → update → confirm only a surviving load-bearing
ambiguity.**

- Form a tentative read from the opening description and the cheapest authoritative repository map.
- Preserve explicit user constraints; derive unchanged current facts from code, docs, manifests, tests, and
  repository instructions.
- Present the project-character read for confirmation only when changing that read would materially alter
  the Current Delivery Slice, foundation depth, or a user-owned product decision. For a closed, narrow
  change in an established repository, record the evidence-backed read silently and continue.
- Never ask the user to choose Prime/direct implementation or to confirm facts the request and repository
  already establish. Do not ask for a broader product vision, audience, or future scope when the current
  repository role and requested slice are sufficient and those answers would not change this contract.

## Project character controls depth — not a formal grade

Let the project's character *itself* be the context that sets DESIGN's depth. Do **not** assign a
formal tier (L/M/H, small/medium/large as a label). A grade becomes a **ceiling** — "it's a small
project, so design shallow" — which violates floor-not-ceiling. State the character in prose ("a
single-user local tool with no network surface and no multi-user state") and let that prose carry
the depth, so domain depth, technical-design depth, and security depth come out proportional to what
the project actually is.

## YAGNI gate — reduce machinery, not the destination

The calibration read bounds implementation complexity and the depth of decisions that must be settled
now. It does **not** cap a user-confirmed outcome or meaningful target state. Preserve the confirmed
destination; reduce only the Current Delivery Slice and the machinery needed to deliver it. Never
silently shrink or inflate the confirmed direction.

A personal tool that starts producing enterprise architecture still gets caught here. Do not prebuild
future capabilities, introduce speculative abstractions, or force strategy decisions that the current
slice does not need. If a design is heavier than the project's character warrants, surface the excess
with reasoning ("this is more infrastructure than a single-user tool needs because …") and let the
user decide — proceed if they need it, scale down if they agree it is overkill.

## Hard constraints

Capture the hard constraints — technical (a platform that must be targeted, a dependency that must
be used or avoided) and business (a deadline, a compliance boundary, a cost limit) — because they
bound every later decision. Preserve constraints stated by the user and derive existing technical limits
from authoritative repository evidence. Ask only when a material user-held constraint remains unknown; do
not ask for hypothetical constraints with no concrete site or consequence.

## Completion bar

Calibration is done when the project's character and depth direction are either **explicitly
confirmed by the user** or **grounded by the request plus authoritative repository evidence** with no
surviving load-bearing ambiguity. Confirmation is required for unresolved user-owned character or scope,
not as a ritual for an already settled existing project.

## Universality guard

Stack-agnostic. Project character, scale, and constraints are described in the project's own terms,
discovered at runtime — no stack is assumed and no fixed catalog of "project types" is imposed.
