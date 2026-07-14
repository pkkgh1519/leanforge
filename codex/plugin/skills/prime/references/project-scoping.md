# project-scoping.md — first-cycle CALIBRATE (project character → depth profile)

The calibration step of the first-cycle ELICIT loop (no harness exists yet). Before deepening any
axis, establish the project's **identity, scale, and constraints** — its character — which then sets
the *depth floor* of every foundation axis the loop will close (domain, technical, and beyond). Loaded
and run only in the first cycle. (It is not a separate phase that must finish before the rest — it
seeds the floor; the loop then closes the axes in gap-driven order, see `elicitation.md`.)

**Floor, not ceiling.** This sets the floor and the guardrails; how you reach the user's confirmed
read of the project is your judgment.

## The mechanism — your judgment + user confirmation

Do **not** freeze scope from the user's opening description. A project's real character emerges
through dialogue, and you update your read in real time as it does (it started as "a personal
note-taker" but a workspace/sharing feature appears → re-read it as a collaboration tool). Before the
loop deepens into the foundation axes, present your final read explicitly and get the user to confirm
it.

Flow: **tentative read → dialogue → update → final presentation → user confirmation.**

- Form a tentative read from the opening description.
- Through dialogue, pin the project's purpose, audience, scale, and hard constraints — updating the
  read as new character surfaces.
- Before leaving calibration, present: *"This project is [character] at [scale]. I'll take the domain
  to [depth] and the technical decisions to [depth]."* — and get confirmation before deepening the
  axes.

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
bound every later decision. These are user-held; ask for them, don't assume them.

## Completion bar

Calibration is done when the project's character and the depth direction are **confirmed by the
user**, so the loop can deepen the foundation axes against that floor. An unconfirmed read is not a
basis for design — present and confirm before proceeding.

## Universality guard

Stack-agnostic. Project character, scale, and constraints are described in the project's own terms,
discovered at runtime — no stack is assumed and no fixed catalog of "project types" is imposed.
