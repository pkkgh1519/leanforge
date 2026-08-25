<a id="top"></a>

<div align="center">

# Leanforge v1.9.0

### From a software goal to a reviewed, verified change ready to integrate.

[![CI](https://github.com/pkkgh1519/leanforge/actions/workflows/ci.yml/badge.svg)](https://github.com/pkkgh1519/leanforge/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/pkkgh1519/leanforge)](https://github.com/pkkgh1519/leanforge/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Leanforge asks only for decisions the user owns, turns them into an approval-ready
change contract, then implements and verifies the result. You receive the actual
change, evidence, remaining risks, and a user-owned integration choice.

[Repository](https://github.com/pkkgh1519/leanforge) · [Release notes](https://github.com/pkkgh1519/leanforge/releases) · [한국어](https://github.com/pkkgh1519/leanforge/blob/main/README_KO.md)

</div>

---

## 60-second start

### Install

**Claude Code**

```
/plugin marketplace add pkkgh1519/leanforge
/plugin install leanforge
```

**Codex**

```
codex plugin marketplace add pkkgh1519/leanforge
codex plugin add leanforge@leanforge
```

<sub>Requires `git` and Claude Code or Codex.</sub>

<sub>Distribution: the marketplace source is `pkkgh1519/leanforge`; the installed plugin identity is `leanforge` and the user-facing product is Leanforge.</sub>

### Verify installation and invoke the skills

**Claude Code** exposes these commands:

- `Leanforge:Prime` (`/leanforge:prime`)
- `Leanforge:Run` (`/leanforge:run`)
- `Leanforge:Set` (`/leanforge:set`)
- `Leanforge:Run TDD` (`/leanforge:run-tdd`) — optional

**Codex** exposes bundled skills, not plugin-defined `/leanforge:*` slash commands. In Codex CLI,
open `/skills` or type `$` and select the Leanforge skill. Use `$prime`, `$run`, `$set`, or
`$run-tdd` when the skill name is unambiguous. In the ChatGPT desktop Codex surface, select the
corresponding Leanforge skill from the installed plugin/skill picker, then start a new chat after
installation or an update.

### First successful run

1. Start with a small, observable request.

   Claude Code:

   ```text
   /leanforge:prime Build a minimal booking flow for a single service business.
   ```

   Codex CLI:

   ```text
   $prime Build a minimal booking flow for a single service business.
   ```

2. Review the approval summary and inspect the contract details that carry product decisions.
3. Execute the approved contract with `/leanforge:run` on Claude Code or `$run` on Codex.
4. Expect four clearly labeled result sections: **Change**, **Verification**, **Remaining risk**, and **Integration**.

### Use Leanforge when

- A prompt is underspecified enough that hidden defaults would be expensive.
- Multiple files, agents, or phases need a reviewed execution contract.
- Decisions and evidence must survive the current chat session.
- You want a recoverable local workflow instead of a one-shot agent run.

### More docs

- [Installation](docs/installation.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Dryforge to Leanforge migration](docs/migration-dryforge-to-leanforge.md)
- [Examples](examples/README.md), including a [completed trusted-change package](examples/trusted-change-package/README.md)
- [Contributing](CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Security](SECURITY.md)

---

## Every prompt is underspecified

"Build a booking system" reads like a requirement. It's a goal statement
— the requirement-level decisions are all still open: booking-to-service
cardinality, the lifecycle of bookings whose service is retired, whether
cancellation releases the slot or holds it.

An agent does not stop at those gaps. It resolves each one inline with a
plausible default and ships code that compiles, runs, and demos cleanly.
*One booking = one service* is now load-bearing schema with no decision
record behind it; the cost surfaces months later as a migration, the day
packages become a feature.

**Prompts carry intent. Implementations are fixed by decisions.** An
unsupervised agent makes every decision you never saw — and reports none
of them.

The second failure compounds the first: **nothing persists.** Whatever
was decided lives in the session transcript, and the transcript dies
with the session. The next session re-derives project state from code
alone — and code encodes outcomes, not rationale. The result is
structural drift: settled questions re-litigated, invariants
re-implemented incompatibly, conventions diverging module by module.

Leanforge intervenes at both points: the open decisions are enumerated
**before code exists**, and every resolution is recorded with its
rationale **at the path every future session reads first**.

---

## Three skills: design, execute, onboard

```
  Leanforge:Prime <INPUT> ──▶ Leanforge:Run ──▶ verified change + evidence + integration choice
                              └─ Leanforge:Set (one-time onboarding)
```

| Skill | Consumes | Produces |
|---|---|---|
| `Leanforge:Prime` | a software goal, documents, or notes | an approval-ready change contract |
| `Leanforge:Run` | the approved contract | the verified change, evidence, remaining risks, and integration choice |
| `Leanforge:Set` | an existing codebase | durable project context for future changes (one-time) |

---

## Leanforge:Prime — from intent to executable spec

`Leanforge:Prime` accepts arbitrary input — a one-line idea, a requirements
document generated by another tool, scattered notes, or nothing but a
hunch. All of it enters with the same status: **material under
challenge, not ground truth.** A document's existence is no evidence of
the design conversation behind it. Conflicts inside the input become
questions, not silent picks; embedded code fragments are reduced to the
behavioral contract they encode — inputs, outputs, invariants — rather
than carried forward as implementation.

From that material, `Leanforge:Prime` enumerates the decisions the design is
obligated to answer — stated or not — and gives each an explicit disposition:
**settled by your current request, derived from authoritative repository evidence
for an unchanged fact, reasoned as not applicable, recorded as tunable, or asked.**
Silent load-bearing defaulting is not a disposition.

Question volume is bounded by construction:

- Explicit requirements and constraints in the current request → never re-confirmed.
- Derivable from previous answers or unchanged repository evidence → never asked.
- A genuinely inapplicable dimension → recorded as `N/A` with a reason.
- A tuning value inside a confirmed mechanism → defaulted, recorded as
  tunable.
- Every question leads with a recommendation — accepting it is one
  keypress.
- Domain questions carry an open *"none of these"* — your domain
  knowledge outranks the option list.

On a project's first Leanforge cycle, `Leanforge:Prime` always writes a durable Project
Foundation, but it does not force a foundation interview. Existing code, manifests, tests, docs, and
the user's constraints can ground the current project character, domain, stack, and conventions. It
asks only for a load-bearing user-owned decision that remains unresolved; greenfield or materially
unfixed projects still receive the deeper domain and technical design conversation.

Before the result reaches you, it passes independent review by an agent
that did not author it — checking that nothing you said was dropped or
distorted, and that the artifact is executable as written. Your approval
is the only event that makes it final.

---

## Leanforge:Run — execution that only passes on evidence

`Leanforge:Run` consumes the approved contract and owns all git state from that
point.

**Scheduling.** The plan carries an explicit dependency graph. `Leanforge:Run`
validates it — cycles, dangling references, coverage gaps — before any
git mutation; a malformed graph fails fast as a producer defect, not
something to patch at execution time. Independent tasks execute
concurrently, each implementer in an isolated git worktree, and re-enter
through a merge gate that verifies the branch actually advanced and the
diff touches its declared surface. Implementer self-reports carry no
weight.

**Verification is risk-proportional.** A mechanical rename and a
payment-path change do not get the same ceremony. High-risk tasks
receive independent review against the spec slice and the raw diff —
never the implementer's summary, which is how reviewers get anchored.

**Gates, end to end.**

- Each parallel wave ends with the project's verification suite running
  against the merged base — the first point at which cross-task
  interactions exist.
- Completion re-runs full verification and adds **runtime smoke**: a
  spec-declared service must boot and answer a live request. *Compiles*
  and *works* are different claims.
- A verification that cannot be evaluated — the command died before
  asserting anything — is a failure, not an inferred pass.

**Escalation is synchronous.** A blocked task halts and waits for your
answer. It does not assume one and build on top of it.

**Git stays yours.** Existing projects execute on a feature branch; main
is never written directly, and final integration — merge, PR, manual —
is never autonomous. A dirty working tree or unpushed commits abort the
run before it starts.

When everything passes, `Leanforge:Run` writes or updates the project harness,
runs one final independent review across the full change, and archives
the design contract under `.leanforge/` for future cycles. If a run stops
before approval or archive completion, `.leanforge/run.json` preserves the
coarse recovery state so the next agent can resume or abandon deliberately.

---

## Leanforge:Set — onboarding an existing codebase

A one-time conversion, not a task runner. `Leanforge:Set` scans the
codebase, then elicits precisely what code cannot attest: a code path
shows what an auth check *does*, not whether that is the *entire
policy*. The elicitation is risk-weighted — what is inferable and cheap
to get wrong is inferred; what is inferable but expensive to get wrong
is confirmed with you: domain invariants, security boundaries, the
business model behind the checks.

Questions arrive in plain language — *"if this changes, must that change
with it?"* — and answers are compiled back into precise rules. It
generates the full harness, leaves the commit to you, and exits. From
then on, the project runs on `Leanforge:Prime` → `Leanforge:Run`.

---

## Anatomy of a cycle

`Leanforge:Prime` → `Leanforge:Run` is one pipeline with exactly two approval points — both
yours. Everything between them runs autonomously.

```
Prime  decompose input → resolve every open decision → write the contract
          → independent review → ▶ your approval

Run    validate the graph → execute in parallel waves → integration gates
          → runtime smoke → write/update the harness → final review
          → ▶ your approval → archive the contract [→ optional: ops sync]
```

What `Leanforge:Prime` leaves on disk is a three-document **design contract** in
`.leanforge/`:

- **spec** — the authority on *what*: behavior rules, invariants, API
  surface, every edge case with an explicit disposition, and the
  verifications the result must pass.
- **plan** — the blueprint for *how*: per-task behavior contracts and
  the dependency graph `Leanforge:Run` schedules from.
- **handoff** — the governing document: how the three relate, and the
  hard gates no step may cross.

The contract is self-contained by construction — written so a future
agent can act on it without the conversation that produced it. Decisions
that cannot be re-derived from code carry their reasoning inline. The
authority hierarchy is explicit: when spec and code disagree, spec wins.
When the spec itself looks wrong, the agent does not patch it — it comes
back to you.

After `Leanforge:Run` completes, the contract is archived under `.leanforge/`,
cycle by cycle — a durable record of what was decided, when, and why.
Active work remains visible through root `.leanforge/{handoff,spec,plan}.md`
and interrupted execution state is guarded by `.leanforge/run.json`.

Legacy state compatibility: repositories created before the Leanforge rename may still contain
`.dryforge/`. Leanforge treats `.leanforge/` as canonical. If only `.dryforge/` exists and it has no
active `run.json`, active root 3-doc, or `worktrees/`, `Run`/`Set` migrate it to `.leanforge/` and
record `.leanforge/migration.json`. Active legacy runs are never migrated automatically; finish,
resume, or abandon them first.

---

## What persists — the project harness

```
your-project/
├── CLAUDE.md                  # entry point for Claude Code — identity + work rules
├── AGENTS.md                  # entry point for Codex — identical content
├── docs/
│   ├── architecture.md        # composition: components, flow, dependencies
│   ├── business-rules.md      # domain logic: entities, invariants, edge cases
│   ├── security.md            # policy: protected assets, access, audit
│   ├── standards.md           # the rules: hard gates, conventions, boundaries
│   ├── engineering-notes.md   # hard-won knowledge: traps, mechanisms, checklists
│   ├── operations.md          # how to run it: setup, build, deploy
│   ├── contracts.md           # external interface contracts
│   └── tracking/
│       ├── status.md          # where the project stands vs. its full scope
│       ├── decisions/         # decision records — what was chosen, and why
│       └── findings.md        # known unresolved problems
└── <module>/AGENTS.md         # per-module scope, boundaries, invariants
```

- **Session-independent context.** A new conversation reads the harness
  and resumes with the architecture, the rules, and their reasons in
  scope. Re-explaining is not part of the workflow.
- **Rationale is first-class.** What was chosen *and why* — so intent is
  not quietly reversed, and settled debates stay settled.
- **Maintained, not appended.** Updates reconcile in both directions:
  work that invalidates an existing statement corrects it. The harness
  tracks reality or it gets fixed.
- **Zero lock-in.** Standard `CLAUDE.md` / `AGENTS.md`. The generated
  docs contain no Leanforge vocabulary and no proprietary format — any
  agent reads them. Delete Leanforge tomorrow; the asset stays.

---

## Where it sits

Plenty of tools touch planning or orchestration. The difference is in
what each one trusts.

- **vs. a bare agent** — a strong model with no anchor re-derives
  everything each session, and the stronger the model, the wider it
  roams. Leanforge supplies the same decisions and the same rationale,
  every session.
- **vs. spec generators & plan modes** — they organize what you said.
  Leanforge enumerates what you *didn't* say — and challenges incoming
  documents instead of formatting them.
- **vs. prescriptive workflows** — "if X, do Y" rulebooks cost the same
  ceremony forever and cap quality at their author's foresight. Leanforge
  pins contracts and floors, and leaves the ceiling open — model
  upgrades translate directly into output upgrades.
- **vs. parallel orchestrators** — parallelism without grounded intent
  ships the wrong thing faster. Leanforge parallelizes only downstream of
  an approved spec, and merges only what survives the gates.
- **vs. status dashboards** — many track events after execution.
  Leanforge tracks *decisions* — the reasoning, the open questions, and the
  gates that were enforced. Execution logs tell you what happened; the
  design contract lets the next agent re-derive intent.

---

## Not a cage. A compass.

- **Floor, not ceiling.** Leanforge fixes interface contracts and the
  procedural skeleton; conclusions stay with the model. Prescriptive
  rules cap a tool at their author's foresight — a floor means a better
  model yields a better result, automatically.
- **Bounded autonomy.** You approve the intent; inside that boundary the
  agent decides freely. Autonomy means executing approved intent — never
  setting intent on its own.
- **Ask, don't guess.** Anything not derivable from your intent comes
  back as a question — synchronously, before proceeding. One guess costs
  more than one pause.

---

## Platform notes

- **Explicit invocation only.** The core lifecycle never auto-triggers.
  Nothing runs unless you call it.
- **One source, two platforms.** Claude Code and Codex artifacts build
  from the canonical `src/skills/` tree into committed `claude/` and
  `codex/plugin/` bundles. The build checks plugin version parity and shared
  reference-file parity before release.
- **The three lifecycle commands** (`Prime`, `Run`, `Set`) are the complete
  core lifecycle surface. Both bundles also expose the optional `Run TDD` wrapper.
- **Requirements.** `git`, and Claude Code or Codex.

---

## When not to use it

- **A one-line fix doesn't need a design conversation.** Leanforge
  front-loads cost — elicitation, verification — to eliminate rework.
  That trade pays on features and projects, not on typo fixes.
- **git is required.** The execution discipline is built on branches and
  worktrees.
- The time spent answering questions is recovered in execution — and
  again in every later cycle that reads the harness instead of asking
  you.

---

## License

MIT

<div align="center"><sub><a href="#top">↑ back to top</a> · Prime / Run / Set</sub></div>
