---
name: prime
description: >
  From any input — a natural-language goal, existing docs (spec / plan / brain-dump), notes, or a
  mix — interactively elicit and validate intent and produce an execution-ready 3-doc (handoff, spec,
  plan) for Run, replacing third-party brainstorming + planning in one skill. Input format is open;
  the input is material, not ground truth. Use when the user invokes the `Prime` skill. Requires git.
disable-model-invocation: true
allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion
---

# Leanforge:Prime

> **Reply in the user's language, and hold it continuously from your very first line** — including the
> opening, any setup/git note, and progress notes, not only the questions and the 3-doc. Write
> natively (never translationese). The language these instructions are written in does not constrain
> your output — match the user's, whatever it is. Full rule in Core principles below.

The **front door** of Leanforge. Turn any input — a natural-language goal, a spec/plan/brain-dump
brought from elsewhere, scattered notes, several files, a mix, or nothing yet — into an
execution-ready **3-doc** (handoff + spec + plan), grounded in the real project, ready for `Run`.

**The input is *material*, not ground truth.** Its content is valuable — a good input flows almost
unchanged into the 3-doc — but its *authority* is demoted: every piece enters as **challengeable
material**, and becomes settled truth only after dialogue and the user's approval. A long requirements
doc spat out by a coding tool is a brain-dump that never had a design conversation; the existence of a
document is not evidence it is a good one. Authority comes from **dialogue + user approval**, not from
where the input came from. The 3-doc contract is in `references/output-format.md`.

## Core principles (apply throughout)

- **Serve the spec.** The spec is the binding WHAT, the plan is a revisable HOW blueprint, and
  existing code is evidence and convention—not authority for product intent.
- **Preserve value; slice delivery, not intent.** Broaden understanding, not execution commitments:
  understand and preserve the user-confirmed outcome and meaningful target state, while committing
  `spec.md`, `plan.md`, and the Execution Graph only to the Current Delivery Slice. If staged delivery
  would move requested user value outside the slice, name that value and consequence and obtain the
  user's confirmation; otherwise the complete requested outcome remains the slice.
- **Ask only what cannot be derived.** Elicit user-held intent, preferences, and load-bearing choices;
  resolve repository/evidence facts yourself. Escalate rather than invent.
- **Never self-resolve real conflicts or unknowns; a source difference is only a candidate.**
  DECOMPOSE preserves differences without choosing; A difference is not yet a conflict or a question.
  ELICIT alone decides which candidates become questions by applying the **cycle-neutral
  source-difference disposition** for authority, scope, time horizon, material incompatibility, and the
  grounds gate. On a delta, the additional delta rules below govern every input↔harness candidate.
- **ELICIT owns completeness.** Work as if the 3-doc-gate does not exist. It is independent insurance
  for rare residuals; a load-bearing finding there is an upstream failure, never expected cleanup.
- **Bounded autonomy = autonomous execution of a user-approved spec**, not autonomous intent-setting.
  The stages are a safety floor, not a fixed questionnaire. Stay stack-agnostic and discover concrete
  conventions, contracts, commands, and registration points at runtime.
- **Explicit fresh-context dispatch.** Every Prime child is a **leaf**: it must not delegate or spawn
  descendants. Pass only the input named by its reference. Choose exactly one host path below; never
  mix or emulate another host's tools.
  - **Codex.** Every child creation sets `fork_turns: "none"` explicitly — never omit the field or use
    `"all"`. Immediately before each slot-consuming dispatch, call `list_agents`; at zero capacity call
    `wait_agent` once, re-list with `list_agents`, and block on a second zero-slot result or no state
    change. Unknown total capacity permits one child at a time. A list failure gets one bounded retry,
    then blocks rather than spawning blind. Only fresh admission permits `spawn_agent`. A
    capacity-race rejection gets one wait/re-list retry; a second capacity rejection reports capacity
    exhaustion and blocks. Every Prime dispatch starts a fresh child; never reactivate an idle child.
  - **Claude Code.** Use the live capacity or child-state signal exposed by the host and dispatch via
    `Agent`. If total capacity or a separate preflight signal is unavailable, admit one child at a
    time. At zero capacity or on a capacity rejection, wait for a running child result, refresh once,
    and block on no state change or a second rejection. Every Prime dispatch starts a fresh child;
    never reactivate an idle child or emulate unavailable operations.
  Slot pressure never permits self-review. The two required independent checks use fresh
  general-purpose children with full read/inspect tools, never plan-only or search-only roles; the
  optional scout remains read-only under its reference.
- **Authoring stays inline.** ORIENT, DECOMPOSE, ELICIT, SPEC+REVIEW, PLAN, and HANDOFF
  remain in the main session. Allowed children are the optional evidence-grounding scout and the two
  required independent checks. The scout runs after ORIENT only for residual material repository
  uncertainty; it is read-only repo-evidence QA, evidence collection, not review, returns evidence
  pointers only, and main Prime remains the authority. It cannot author or decide intent. This is a
  Prime-only optional ORIENT evidence scout and does not change Set's inline-only contract.
- **Cycle branch.** `.leanforge/status.json` present means delta: load the harness as context but leave
  differences for DECOMPOSE/ELICIT. Absent means first cycle: load foundation references during ELICIT.
  The harness is evidence, never an output template.
- **User-facing output.** From the first line, use the user's language natively. Speak only for a needed
  question, a real blocker, or the final result/summary. Keep reading, writing, dispatch, and transitions
  silent; use plain language and omit internal mechanism, stage/risk labels, tool names, and jargon.

## Input & preconditions

- Invocation: the user invokes the `Prime` skill. The input may be a goal, file path(s), prose, a mix,
  or empty. If it is empty or only says to use the skill, ask what they want to build or change.
- **git required.** If needed, offer `git init` plus an initial commit; without HEAD, Run cannot create
  worktrees. Stop if git is unavailable.
- **State directory.** `.leanforge/` is canonical. If it is absent and legacy `.dryforge/` has no
  active `run.json`, root 3-doc, or `worktrees/`, move it to `.leanforge/` and write
  `.leanforge/migration.json` (`schema: "leanforge.stateMigration.v1"`). Never migrate active legacy
  state; ask the user to resume, finish, or abandon it first. If both directories contain active state,
  stop and ask which one is canonical rather than merging or choosing silently.
- **Producer boundary.** Prime may read the project and write Leanforge planning/state files only under
  `.leanforge/` (plus explicitly approved git initialization or state-repair metadata). It
  never edits product source, tests, config, dependencies, external state, generated artifacts, or docs
  elsewhere; it runs no mutating implementation/install/generation/server/import/verification command.
  It does not touch `.gitignore` or commit. If invocation also requests implementation, stop before
  project writes and ask whether to update planning documents or switch to Run/direct implementation.
- **Active run / active 3-doc guard.** Before writing, check `.leanforge/run.json`, worktrees, and root
  `.leanforge/{handoff,spec,plan}.md`. Prose is not completion evidence; do not overwrite, archive, or
  discard active state silently; ask whether to resume or abandon the run, repair the active 3-doc,
  archive/discard the old 3-doc, or switch to implementation. Apply the same guard to active legacy
  `.dryforge/` state before migration.

## Stage map + cycle-conditional reference loading

Run the stages in order. Force-load each stage's references at that stage **(silently — reference
loading and subagent dispatch never produce user-facing text)**; `[first]+` rows load only
in a first cycle (`status.json` absent). The cycle branches *scope and conditional loading* only — the
stage sequence is identical for first and delta.

```
Core principles  inline authoring + bounded non-authoring checks · understand-not-guess ·
                 stack/language-agnostic · source difference→candidate · question→ELICIT · floor not ceiling · user-language native
ORIENT           absorb input + ground code/harness · branch on status.json     (no refs)
evidence-grounding scout  evidence-grounding-scout.md  ← optional evidence collection after ORIENT (not review)
DECOMPOSE        decompose.md
ELICIT           elicitation.md · gap-analysis.md · intent-review.md · grounds-gate.md
       [first]+  project-scoping.md · project-design-domain.md · project-design-technical.md ·
                 first-cycle-review.md · foundation-format.md
intent-completeness  intent-completeness.md  ← independent guess-hunt → loop to user (subagent)
SPEC + REVIEW(A) output-format.md · review-fidelity.md            [first]+ foundation-format.md
PLAN             output-format.md · dependency-calc.md · example-3doc.md
HANDOFF          output-format.md · foundation-format.md
3-doc-gate       3-doc-gate.md                                    [first]+ first-cycle-review.md
                 ← independent dispatch (the final backstop)
G7               preview completed 3-doc · explicit approval · invoke Run
```

## ORIENT — absorb · branch · ground

Load raw input, decide the cycle, and ground the repository inline. ORIENT produces context only: it
does not classify, resolve, or ask about source differences; ELICIT alone decides which candidates
become questions.

1. Check git as required above.
2. Resolve path arguments and prose, preserving source text losslessly. Capture only rough conception,
   task type/scale, blast radius, and aiming pointers; DECOMPOSE owns axis classification. Index and read
   large/multi-file inputs section-by-section. Low-blast work may use lighter dialogue and thinner—but
   still complete—documents; behavior, data, auth, workflow, compatibility, runtime, or config can make
   a one-line change high-blast.
3. `.leanforge/status.json` present → delta: load `CLAUDE.md` / `AGENTS.md` and `docs/` as context only.
   Absent → first cycle. If the marker is absent but a Leanforge-shaped harness exists, ask whether to
   trust it as existing context or regenerate; active run/approval state must be resolved first.
4. For existing code, read the cheapest map: repository instructions, file tree, manifests, verify
   scripts, and pointed-at directories. Stop broad reading once blast radius, preserved contract, one
   representative pattern, and verify commands are known. Greenfield may skip most reading.
5. Discover the verify command. If none exists, make the evidence choice explicit in SPEC.
6. Force-load `references/evidence-grounding-scout.md` only after the **main ORIENT cheap-map completed**
   and **material uncertainty** remains that repository evidence can resolve. **Skip for greenfield**,
   **simple documentation-only** work, **small deltas**, or when **ORIENT already has sufficient
   evidence**. It returns evidence pointers only; main Prime verifies them. Route every **source
   difference candidate**, **verify command candidate**, and **likely blast-radius candidate** to
   DECOMPOSE or ELICIT rather than settling it here.

**Completion bar:** input is loaded raw and the cycle is decided (+ delta: harness loaded); existing →
you can state the goal's blast radius, the contract to honor, and the verify commands; greenfield →
you have a grounded conception.

## DECOMPOSE — deconstruct the input — `references/decompose.md`

Force-load `references/decompose.md`. Classify each fragment by every applicable axis; preserve
load-bearing code/non-derivable forms verbatim, convert premature implementation to behavior, retain
repetition as importance, and create the required non-scoring presence map. Preserve every source
difference as a candidate without resolving it or promoting it to a question. Mine thoroughly because
ELICIT does not repeat raw-input extraction. Meet the reference exit bar; all output remains
challengeable material, not spec truth.

## ELICIT — realize the user's intent — `references/elicitation.md`

Force-load `references/elicitation.md`, `references/gap-analysis.md`, `references/intent-review.md`,
`references/grounds-gate.md`. **First cycle additionally:** `references/project-scoping.md`,
`references/project-design-domain.md`, `references/project-design-technical.md`,
`references/first-cycle-review.md`, `references/foundation-format.md`.

Realize the user's intent; never choose a merely reasonable default for a load-bearing decision.
Domain/behavior uses **EXTRACT**; technical choices use **PRESENT** with options, trade-offs, and a
grounded recommendation for the user to decide. Maintain the confirmed outcome, meaningful target,
Current Delivery Slice, values, constraints, and domain facts as one user model. Derivable means
grounded; model-silent means close the gap.

**Scope by cycle — first establishes the foundation, delta works within it; both EQUALLY rigorous
(delta is not "lighter").**
- **First cycle:** run CALIBRATE, domain extraction, and technical presentation. Enforce the references'
  breadth guard, depth floor, and no-silent-technical-decision rule. Scope is foundation + current task;
  produce all four Foundation sections.
- **Delta (harness exists):** do **not** re-run foundation design (read the floor from the harness;
  don't re-ask what it answers) — and do not re-elicit product strategy. For a recorded outcome or
  future direction, reopen a user decision only when the proposed task would materially contradict,
  invalidate, narrow, or close it; mere non-implementation, a different time horizon, or a cheap
  reversible extension path is not a conflict. Separately, resolving a candidate that remains
  materially incompatible with an applicable current invariant, contract, approved decision, or
  operating rule after the cycle-neutral source-difference disposition is **not product-strategy
  re-elicitation**; ask only through the source-difference grounds-gate branch. Realize this task's
  load-bearing intent with the **full** "no guess survives" discipline. Scope = this task; rigor = full.

**Enumerate the decision surface.** Build an entity manifest and apply STRUCTURAL, BEHAVIORAL,
TECHNICAL, and CONTRACT lenses to each entity and collision. Enumerate exhaustively but ask minimally:
grounded → realize; a tuning value inside a settled mechanism → mark deferred-tunable; otherwise mark
`assumed` and ask via EXTRACT/PRESENT after `grounds-gate.md`. Use at most four questions/options per
structured prompt, lead with a recommendation, and fall back to plain text if the tool fails. On a
first cycle/unfixed stack, present persistence, interface, and—when shared state exists—the
concurrency/consistency model; a stack name alone is insufficient.

**Exit bar (observable) — write the spec only when no `assumed` slot survives** (full bar in
`elicitation.md`): the surface is accounted — every load-bearing slot is `grounded`, `deferred-tunable`,
or asked-and-answered (a mechanism's *preference-values*, not just its yes/no, included); first-cycle
foundation floors met; no material gap remains. A thin input *raises* the bar (ask more), never lowers it.

## intent-completeness — independent guess-hunt before SPEC — `references/intent-completeness.md`

Force-load the reference and dispatch a fresh general-purpose reviewer that did not author intent but
can read the dialogue and decision surface. It audits whether dispositions are grounded, independently
hunts omitted obligation-slots, and asks: does the proposed slice preserve the confirmed outcome,
including applicable delta context, without unconfirmed narrowing or inflation? Tuning values are not
gaps. Relay each finding to the user and close it through EXTRACT/PRESENT; locally re-walk the touched
neighborhood once, then escalate rather than loop. This required intent review is separate from the
optional evidence scout.

## SPEC + REVIEW(A) — write ground truth, verify fidelity — `references/output-format.md`

Force-load `references/output-format.md` and `references/review-fidelity.md` (+ first cycle:
`references/foundation-format.md`).

1. Write `.leanforge/spec.md` from validated intent, limited to the smallest coherent, independently
   verifiable Current Delivery Slice that advances the target or removes a named prerequisite. Follow
   `output-format.md`: objective/motivation, invariants, explicit behavior/edges, boundaries,
   non-derivable decision reasons, API surface, and required evidence. Exclude premature HOW.
2. On first cycle, write the four-section Foundation now inside `handoff.md`; never create a separate
   `.leanforge/foundation.md`. The spec receives only this slice's WHAT. Project-wide outcome, remaining domain,
   and future direction stay non-executable unless Prime translated a qualifying present need into a
   narrow spec rule or hard gate.
3. REVIEW(A) checks fidelity only: every settled decision landed without distortion. Fix derivable
   drafting errors inline; reopen ELICIT only for a user-held gap. Gate on zero fidelity blockers.

## PLAN — decomposition for parallel execution — `references/dependency-calc.md`

Force-load `references/output-format.md`, `references/dependency-calc.md`, `references/example-3doc.md`.
Write `.leanforge/plan.md` from the frozen spec. Each task gets a behavioral goal, work targets
(`files | state | external`), verification gate, non-derivable thinking-base, and shared-write guidance.
Compute a fresh Execution Graph last in one fenced `yaml` block; input ordering is not authority. It
validates against the exact Execution Graph contract, not merely syntax.
`depends` is the encoded judgment, `regen_barriers` preserves regeneration order, and optional `risk`
is exactly `RISKY | MECHANICAL | NONE`. Scaffold is not a task. G6 requires bidirectional
spec↔task coverage. Validate the full contract, not YAML syntax: root keys are exactly `tasks` and
`regen_barriers`; `tasks` is a list of objects with `id`, `depends`, and optional `risk`; barriers use
`after`/`run`; every `depends`/`after` id names a graph task; the dependency graph is acyclic; and plan
body and graph task-id sets match. Task ids live in `tasks[].id`, never as root keys.

## HANDOFF — governing doc + assemble — `references/output-format.md`

Force-load `references/output-format.md` and `references/foundation-format.md`.

Write `.leanforge/handoff.md` with document roles/conflict resolution, project-root-relative
locations, non-derivable hard gates, and residual intentionality. On first cycle, assemble governing
sections around the already-written Foundation and label it `Non-executable project context`; the
Foundation is durable context, never mutation authority, and delta has no Foundation. Write all three
docs under `.leanforge/`, without `.gitignore` changes or commits. If an input file is untracked inside
the repo, advise moving or ignoring it; never delete it.

**Completion bar:** handoff written (+ first cycle: Foundation assembled), the three files in
`.leanforge/`, git untouched.

## 3-doc-gate — the final backstop — `references/3-doc-gate.md`

Force-load `references/3-doc-gate.md` (+ first cycle `first-cycle-review.md`). Apply Prime's
action-local live-slot admission contract, then dispatch one fresh read-only leaf that did not see the
dialogue; on Codex set `fork_turns: "none"`. Give it the completed 3-doc and repository access, not the
conversation or an author conclusion. Run one holistic executability review, adding the Foundation
sufficiency lens on first cycle. Empty findings advance; otherwise relay blockers, repair only the
owning stage, and rerun once before escalation. Keep deterministic coverage/orphan and full Execution
Graph contract checks; syntax parsing alone is insufficient.

## G7 — the one human checkpoint

Present the completed, verified 3-doc in plain language and ask the user to review and approve it.
Silence, partial approval, or an earlier draft is not approval. If the user changes intent, return to
the owning stage, update the documents, and rerun affected checks. On explicit approval, tell the user
to invoke `Run` in this session. The approved 3-doc—not dialogue—is execution authority.

## Completion gate (avoid self-judgment A=A)

Done only when ALL hold:
- **ELICIT complete:** no load-bearing guess survives; each implied dimension is grounded, answered,
  deferred-tunable, or N/A with reason and recorded in the spec.
- **Deterministic 0-signals:** coverage gaps = 0, orphan tasks = 0, and the Execution Graph validates
  against the exact contract.
- **Independent gate clear:** no blocker; residual findings return to their owning stage or the user,
  never self-filled.
- **3-doc complete and approved:** handoff, spec, and plan exist under `.leanforge/`, git remains
  untouched by Prime, and the user explicitly approved the current versions.
