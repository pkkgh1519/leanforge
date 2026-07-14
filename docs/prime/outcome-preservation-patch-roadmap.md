# Prime Outcome-Preservation Patch Roadmap

## Objective

Prevent `Prime` from narrowing a validated user outcome for implementation convenience while keeping
`Run` focused on a small, coherent, verifiable delivery slice.

The governing invariant is:

> Preserve value; slice delivery, not intent.

Prime may broaden its understanding of the user's desired outcome and meaningful target state. That
broader understanding does not authorize broader execution: `spec.md`, `plan.md`, and the Execution
Graph cover only the Current Delivery Slice.

## Problem statement

The existing small-change and YAGNI guidance can be read as permission to shrink the design goal
itself. Repeated Prime cycles can therefore optimize for work that is easy to schedule instead of work
that meaningfully advances the user-confirmed outcome.

The correction must preserve two distinct responsibilities:

- **Design:** understand and retain the confirmed outcome and meaningful target state.
- **Delivery:** select and execute the smallest coherent, independently verifiable increment that
  advances that target or removes a named prerequisite for the next target-facing increment.

## Design decisions

1. `confirmed user outcome -> meaningful target state -> Current Delivery Slice` is an internal
   intent model, not a new staged workflow, document schema, or question script.
   If staged delivery moves requested user value outside the slice, Prime names that value and the
   consequence and obtains user confirmation; otherwise the complete requested outcome remains the
   slice.
2. YAGNI limits implementation complexity and premature commitment. It does not reduce a confirmed
   outcome or target direction.
3. The Project Foundation keeps its existing four sections. Project identity preserves the confirmed
   broader outcome and target when one exists.
4. Future scope distinguishes concrete remaining outcomes from durable future directions without
   adding a parser, YAML field, backlog, schedule, or implementation authorization.
5. A future direction may constrain the current slice only when it is user-confirmed, the current
   choice would otherwise close a costly or irreversible option, and the option can be preserved by a
   concrete present boundary without prebuilding the future capability or adding speculative
   abstraction.
6. Prime translates any qualifying future constraint into present-tense `spec.md` or handoff hard-gate
   language. `Run` never infers work or constraints from non-executable Foundation or harness future
   context.
7. Delta cycles reuse durable context and reopen product intent only when the proposed change would
   materially contradict, invalidate, narrow, or close a recorded outcome or future direction. Mere
   non-implementation is not a conflict.
8. A new outcome or future direction confirmed during a delta travels through a clearly
   non-executable handoff context update into `status.md`; it never becomes execution scope by that
   propagation.

## Current Delivery Slice

The Current Delivery Slice is the smallest coherent, independently verifiable increment that either:

- delivers observable progress toward the confirmed target; or
- removes a named prerequisite or blocker necessary for the next target-facing increment.

It may be product behavior, infrastructure, documentation, configuration, migration, or other file,
state, or external work. It must leave the project usable and internally consistent, identify its
immediate consumer and completion evidence, and must not prebuild unapproved future capability.

When no broader target is confirmed, the requested change itself may be the slice.

## Scope

### Prime producer contract

- Add the outcome-preservation invariant to `SKILL.md`.
- Refine ELICIT's user model and delta conflict rule.
- Correct CALIBRATE/YAGNI semantics.
- Make the Foundation/spec/plan boundary explicit.
- Add outcome-preservation and non-leakage checks to existing reviews.
- Update the worked example with the first-cycle Foundation boundary.

### Run and Set durable contract

- Keep Foundation and future directions non-executable.
- Map concrete remaining outcomes and future directions into distinct `status.md` meanings.
- Make both Run-created and Set-created harnesses preserve those meanings.
- Preserve ambiguous legacy remaining text without bulk migration; classify it only when evidence is
  clear or the distinction becomes relevant to a later task.
- Review future directions for both loss and accidental promotion into commitments.

### Global operating guidance

- Clarify that the smallest-change rule applies to implementation, not to shrinking an approved design
  destination.

## Non-goals

- No fifth workflow stage or mandatory strategy interview.
- No new gate, reviewer dispatch, roadmap parser, machine field, or YAML key.
- No fifth Foundation section.
- No Execution Graph, scheduler, dependency, or risk-enum change.
- No automatic expansion of small personal tools into enterprise designs.
- No speculative architecture for future directions.
- No direct edits to generated surfaces or installed plugin caches.
- No bulk migration of existing `status.md` content.

## Implementation phases

### Phase 1 — Producer semantics

Patch Prime's orchestration, ELICIT, scoping, output, Foundation, audit, and example references.

Exit criteria:

- Confirmed outcomes are not silently narrowed.
- A small request can remain the slice without a strategy interview.
- Only the current slice appears in `spec.md`, `plan.md`, and the Execution Graph.

### Phase 2 — Durable context and consumer safety

Patch the shared Foundation and harness contracts plus Run's lifecycle/orchestration wording.

Exit criteria:

- Future directions survive Foundation -> harness -> delta round-trips at the altitude confirmed by
  the user.
- Future directions remain unordered and non-executable.
- `Run` does not infer tasks, abstractions, compatibility work, or constraints from future context.

### Phase 3 — Contract verification

Add a focused repository test and regenerate Claude/Codex surfaces from `src/skills/`.

Exit criteria:

- Shared-reference byte parity passes.
- Canonical and generated surfaces contain the required guards.
- The Execution Graph contract remains unchanged.
- The full repository test suite passes.

### Phase 4 — Blind behavioral verification

Evaluate fresh-session outputs for:

1. a broad greenfield goal;
2. a small personal tool;
3. an implementation-convenience conflict;
4. a delta that does and does not threaten a recorded direction;
5. trivial documentation or bug work;
6. unrelated future value;
7. infrastructure, documentation, configuration, and migration enabling work.

Exit criteria:

- Broader value is preserved without leaking into current execution.
- Small work remains proportionate.
- Enabling work names an immediate consumer and completion evidence.
- No new workflow ceremony appears.

## Acceptance criteria

| AC | Observable result | Evidence |
|---|---|---|
| AC-01 | Prime preserves a confirmed outcome and target while limiting execution to the Current Delivery Slice. | Focused source/generated contract test plus blind greenfield scenario. |
| AC-02 | YAGNI reduces implementation machinery, not the confirmed destination. | Scoping contract assertion and implementation-convenience scenario. |
| AC-03 | Foundation retains four sections and remains non-executable. | Heading/parity assertions and generated diff review. |
| AC-04 | Future directions survive in durable context without becoming ordered remaining work. | Harness contract assertions and Foundation-to-delta round-trip. |
| AC-05 | Run infers no work or constraints from future context. | Consumer guard assertion and unrelated-future scenario. |
| AC-06 | Product, infrastructure, documentation, configuration, and migration work can form valid slices. | Slice-definition assertion and enabling-work scenario matrix. |
| AC-07 | No new workflow, parser, schema, scheduler behavior, or graph field is introduced. | Focused negative assertions and structural diff review. |
| AC-08 | Canonical, Claude, and Codex surfaces remain synchronized. | Build and full repository tests. |

## Release gate

Decide on a patch-version bump only after the canonical diff, generated surfaces, full tests, and blind
scenarios are green. Version metadata and cache propagation are release concerns; they are not used to
validate the semantic patch itself.

## Validation record — 2026-07-14

The `v1.6.7` release candidate satisfied the release gate with the following evidence:

- official build completed with four manifest/CHANGELOG versions aligned at `v1.6.7` and all three shared references byte-identical;
- focused outcome-preservation contract tests passed `11/11`, and the full repository suite passed `47/47`;
- Prime, Run, Set, and Harness passed skill validation;
- fresh-session blind checks passed for a broad greenfield outcome, a proportionate small personal/docs slice, an implementation-convenience conflict, delta conflict/no-conflict handling, an unrelated future direction round-trip, and enabling work;
- independent architecture review reported no blocker or major finding;
- no new workflow stage, parser, scheduler behavior, Foundation section, or Execution Graph field was introduced.
