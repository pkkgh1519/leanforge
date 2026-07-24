# evidence-grounding-scout.md — optional ORIENT evidence collection (not review)

Use this reference only for Prime's **optional evidence-grounding scout**. It is a **Prime-only
optional ORIENT evidence scout** and **does not change Set's inline-only contract**. This is evidence
collection, not review; the review gates are `intent-completeness` and `3-doc-gate`.

## Purpose

The scout is **read-only repo-evidence QA** **after ORIENT**. It exists to collect missed repository
evidence signals when main Prime has already performed the cheap-map read but still has material
uncertainty.
It does not build intent, review intent, or review the 3-doc. It does not replace ORIENT,
DECOMPOSE, ELICIT, SPEC, PLAN, HANDOFF, intent-completeness, or the 3-doc-gate.

## Trigger

Dispatch only when all are true:

- the **main ORIENT cheap-map completed**;
- **material uncertainty** remains;
- a small, read-only repository evidence pass could change the task's scope, risk, validation path, or
  source-difference handling.

## Skip

Do not dispatch for:

- **skip for greenfield** work where there is no meaningful repository evidence to inspect;
- **simple documentation-only** work;
- **small deltas** whose affected surface and verification command are already obvious;
- cases where **ORIENT already has sufficient evidence**.

## Dispatch contract

- **Admission and isolation.** Apply Prime's action-local live-slot admission contract immediately
  before dispatch. On Codex, create one non-delegating leaf with `fork_turns: "none"` explicitly.
- **Read-only.** The scout inspects files and commands only as evidence. It does not write, edit,
  commit, install, run Sets, or perform implementation.
- **Evidence pointers only.** Return compact path/line/command pointers and why each pointer matters.
  Do not return a rewritten brief, spec, plan, or decision.
- **main Prime remains the authority.** The main Prime session must re-check cited evidence inline
  before using it.
- **must not set product intent**.
- **must not write the spec**.
- **must not design the plan**.
- **must not make decisions**.
- **must not ask the user**. If user input may be needed, return the evidence for DECOMPOSE to preserve
  as a candidate; ELICIT alone decides whether it becomes a question.
- **No recursive delegation**.
- **One dispatch max** per Prime run.

## Return shape

Return a concise structured list with:

- inspected paths and any relevant command slices;
- evidence claims tied to exact source paths or commands;
- **source difference candidate** items when repository evidence appears to disagree with input or
  harness context;
- **verify command candidate** items when a likely validation command or missing validation path is
  found;
- **likely blast-radius candidate** items when evidence suggests affected files, contracts, or
  registration points beyond the user's initial phrasing;
- unknowns or uncertainty that should be routed to **DECOMPOSE or ELICIT**;
- explicit scope limits: what was not inspected.

## Main-session handling

Main Prime must treat the scout output as untrusted evidence pointers, not as conclusions. Re-open only
the cited files/commands inline, then:

- feed source differences into DECOMPOSE as candidates;
- ask user-owned uncertainty in ELICIT;
- record verify-command decisions in SPEC;
- discard any scout claim that cannot be re-grounded from cited evidence.

## Hard prohibitions

- This is **not a Run repo-local lens**.
- **do not invoke harness-generated repo-local skills**.
- Do not create or modify repo-local skills, subagents, harness files, or Leanforge lifecycle state.
- Do not execute Run, Set, or any implementation workflow.
