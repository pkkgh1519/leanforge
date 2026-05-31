# dryforge

*[한국어](./README_KO.md)*

> Say what you want to build. Two commands later, it's built.

```
/plugin marketplace add fn-opt/dryforge
/plugin install dryforge
```

## Two paths, same result

Whatever your starting point, dryforge gets you to solid, working code.

### Path 1 — Start from an idea

```
/dryforge:ready    →    /dryforge:go
```

You have an idea but no documents. `ready` talks with you — asks the right questions
about what matters, handles what it can figure out from your code — and writes the spec
and plan itself. Then `go` builds it.

### Path 2 — Start from documents

```
/dryforge:set    →    /dryforge:go
```

You already have a spec and plan — hand-written, or from another tool.
Wrong file paths, missing pieces, code that doesn't match reality.
`set` validates them against your actual codebase, fixes what's broken,
fills what's missing, and makes them execution-ready. Then `go` builds it.

## What it looks like

```
You:  /dryforge:ready I want to add notifications.
      Let users know when someone replies to their post.

       dryforge reads your codebase and starts a conversation.
       Not a checklist. Just the questions that matter.

       "Should notifications go out in real time, or batched?
        Real-time means adding WebSocket infrastructure.
        Batched works with your current stack — a periodic job
        that sends digest emails.
        Which makes more sense for your users?"

       You answer. It writes the spec and the plan.

You:  /dryforge:go

       Up to 8 tasks in parallel, each in its own isolated git worktree.
       Spec review per task. Integration gate per wave.
       Code review on the merged result.

       When something's ambiguous, it asks — instead of guessing
       and building the wrong thing.
```

## How is this different?

If you've given an agent a big task before, you've probably seen this:

- It starts coding before understanding what you actually want.
  Halfway through, you realize a critical decision was never discussed.
- It follows the same ceremony on everything — full TDD on a config change,
  triple review on a one-liner. It's following procedure, not adapting
  to the task.
- It fills the plan with code that's already stale by execution time.
  The agent ends up fighting its own plan.
- Tasks that could run in parallel go one by one, because no one
  computed which depends on which.

dryforge splits the work into two stages to fix this:

**Before building** — figure out what to build first.
Ask deeply. Write the spec. Compute dependencies. Determine what can run in parallel.

**While building** — work from a clean session, following the plan.
Parallel agents in isolated worktrees. Verification sized to the task.
When something's ambiguous, it escalates to you instead of papering over it.

The spec is the ground truth. Everything flows from it.

## Commands

### `/dryforge:ready <goal>`

Start from an idea. It reads your code, asks the questions that matter, and
writes the spec and plan. Design decisions get explored deeply.
What it can derive from the code, it handles on its own.

### `/dryforge:set <spec> <plan>`

Start from documents. It reads your code and finds what's wrong — broken paths,
missing pieces, a plan that doesn't match reality. Fixes it, computes the
dependency graph, and makes it ready for execution.

### `/dryforge:go`

Builds it. Start a fresh session (`/clear`) and run this.
Parses the dependency graph into waves, spins up parallel agents in isolated
git worktrees, runs spec review and integration gates, and asks before
merging to main.

## Requirements

- **git** — uses git worktrees for isolation. No repo? It offers `git init`
  so you can run locally.
- **Claude Code**

## License

MIT
