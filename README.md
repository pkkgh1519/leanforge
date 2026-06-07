<a id="top"></a>

<div align="center">

<img src="https://dryforge.vercel.app/assets/icon-1024.png" width="84" height="84" alt="dryforge" />

# dryforge

### Describe it once. Ship _exactly_ that.

Your agent works like a senior developer — an all-in-one harness that keeps every step honest, from project design to running code.

[Website](https://dryforge.vercel.app) · [한국어](https://github.com/fn-opt/dryforge/blob/main/README_KO.md)

</div>

**Install** — Claude Code

```
/plugin marketplace add fn-opt/dryforge
/plugin install dryforge
```

Codex

```
codex plugin marketplace add fn-opt/dryforge
codex plugin add dryforge@dryforge
```

<sub>Requires `git` and Claude Code or Codex.</sub>

---

## It doesn't cage. It points.

Same model, better results. Instead of micromanaging the agent, dryforge lays down a solid basis for judgment and blocks only the ways things go off the rails — pulling the model's full power through. It sets a **floor, not a ceiling**: a better model just gets you better output.

- **Criteria, not rules.** "If X, do Y" rules cage a model. dryforge gives it a sound basis to judge for itself — rules bind, good criteria free.
- **It wakes the model's potential.** Many tools shackle the agent with procedure — "AI can't be trusted" — and end up suppressing its real skill. dryforge doesn't cap the ceiling, so the model's best comes through. The better the model, the better the result.
- **Boundaries, not control.** You approve the intent; inside that boundary the agent decides freely. That's *bounded autonomy*, not a leash.
- **"Looks done" doesn't pass.** Completion is judged by captured evidence from actually running it — checked by an independent, adversarial view whose job is to find the holes, not by the author's own feeling.
- **Verification scales with risk.** No uniform ceremony forced on every task. Risky work is verified thickly, trivial work lightly — exactly as much as it needs.
- **Ask, don't guess.** Anything not derivable from the intent is brought back to you, not decided unilaterally. One guess is worse than one pause.

---

## A project that has a system

dryforge doesn't just leave code behind. It records your project's structure, rules, decisions — and the **reasons** behind them — as real documents, building a system that lasts. That living document set is the **project harness**.

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

- **Context survives sessions.** A new conversation reads the harness first and continues knowing the whole project — no re-explaining from zero.
- **The "why" is kept, not just the "what."** Decisions are recorded with their rationale, so intent doesn't quietly get reversed and the same debate doesn't repeat.
- **It stays in sync with the code.** The harness is updated as you work and reconciled against reality — documents never rot into fiction.
- **It works without dryforge.** The harness is standard `CLAUDE.md` / `AGENTS.md` files. Any agent reads it and stays grounded. You're not locked in.

---

## Same prompt, different code

Why does that shared context matter so much? Ask for the same thing in two sessions and you get two different answers. Not because the model is weak — because it's *strong*. With nothing to anchor to, a capable model re-reasons everything from scratch every time. The smarter the model, the wider the spread. People think differently today than yesterday, too.

<table>
<tr>
<td><sub>session 1</sub>

```js
function sortUsers(list) {
  return list.sort((a, b) =>
    a.name.localeCompare(b.name))
}
```
</td>
<td><sub>session 2</sub>

```js
const sorted = [...users].sort(
  (a, b) => a.name > b.name ? 1 : -1
)
```
</td>
</tr>
</table>

The answer is simple — hand the strong model the **same context, every time**. That's exactly what the harness is, and that's dryforge.

---

## However you start, `go` finishes

What you bring decides the door — an **idea**, **design docs**, or **existing code**. **`ready`** and **`set`** both lead into **`go`**; **`migration`** is a one-time on-ramp for code that already runs.

```
  ready ─┐
         ├──▶  go  ──▶  working software + the project harness
  set  ──┘

  migration  ──▶  existing code → the harness   (one-time onboarding)
```

| What you bring | Command | What it does |
|---|---|---|
| **An idea in your head** | `/dryforge:ready` | A senior-level brainstorm asks until nothing is ambiguous and turns a vague idea into a complete design — recommending a stack if you have none, scaled to your project. |
| **Design docs you've written** | `/dryforge:set` | Spec, plan, or notes — from any tool. `set` reads them, points out what's missing, asks, and shapes them into something executable. *(Documents, not a codebase — for that, see `migration`.)* |
| **→ both converge on** | `/dryforge:go` | Builds from the plan with zero waste: many tasks at once in a pre-computed order, the risky parts verified more thoroughly. → working software **+** the project harness. |
| **Code that already runs** | `/dryforge:migration` | Reads your existing codebase and generates the project harness automatically — surfacing even the intent you never wrote down. A one-time on-ramp: after that, add or improve features with `ready` / `set` → `go`. |

---

## License

MIT

<div align="center"><sub><a href="#top">↑ back to top</a> · ready / set / go</sub></div>
