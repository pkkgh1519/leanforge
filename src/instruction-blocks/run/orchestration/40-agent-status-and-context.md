
## Agent status protocol

Each **dispatched** implementer returns one status (orchestrator-direct sequential work has none —
the orchestrator knows its own state):

| Status | Meaning | Orchestrator response |
|---|---|---|
| `DONE` | complete, self-checks pass | merge (review per policy — the single final review, or a mid-run spec-review if it triggers) |
| `DONE_WITH_CONCERNS` | complete, but flags something | record the concern; weigh at final review (or mid-run spec-review if review policy triggers it) |
| `NEEDS_CONTEXT` | missing info to proceed | provide the missing context, re-dispatch |
| `BLOCKED` | cannot proceed (conflict, ambiguity) | analyze; walk the bounded escalation ladder (below), then **escalate to the user** |

**Bounded escalation ladder** (for `BLOCKED` / `NEEDS_CONTEXT`): **attempt 1** — re-dispatch with
more context (the missing slice, the resolved ambiguity); **attempt 2** — re-dispatch with an
upgraded model; if it is **still BLOCKED**, **escalate to the user** with full context: what was
tried, what each attempt produced, and why it failed. The budget is bounded — do not loop
re-dispatching past the ladder.

## Context budget

- **Resident**: the 3-doc + wave schedule + accumulated per-task summaries
  (~100–200 tokens each) + spec-review verdicts (~20 tokens each).
- **Temp-load → use → drop**: authoring an implementer prompt (the relevant plan+spec slice),
  analyzing a failure (the error output). Drop after the judgment.
- **Sequential direct execution → sawtooth.** When the orchestrator implements a `MECHANICAL` /
  `NONE` task itself, it temporarily holds that task's file context. Load → implement → commit →
  **drop**; don't carry one sequential task's files into the next.
- Keep raw diffs out of the orchestrator — spec review runs in the subagent's context.
- **Watch retry bloat**: temp-loads have per-item caps but no total cap; repeated failures can
  swell the orchestrator. Compress to summaries and drop promptly.

## Per-wave step order

> **Review policy.** Default: a single **final review** after all waves merge — one subagent
> checks the full base diff for spec conformance + code quality. Mid-run spec-review is added only
> when the orchestrator judges that a **RISKY task with downstream dependents** could cascade a
> deviation. When dispatched, spec-review is always a subagent (never inline) to preserve
> independence.
