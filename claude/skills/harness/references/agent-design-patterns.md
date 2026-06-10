# Agent Design Patterns

Use the smallest pattern that preserves correctness, reviewability, and reuse.

## Pipeline

Use when every phase depends on the previous artifact.

Typical shape:

```text
scope -> draft -> review -> repair -> final
```

Portable Codex implementation:

- one orchestrator skill
- deterministic handoff files
- one role owner per phase
- reviewer reads the previous phase artifact before approving the next phase

Avoid Pipeline when independent work can be safely split and compared.

## Fan-out/Fan-in

Use when independent branches can gather evidence or produce alternatives before synthesis.

Portable Codex implementation:

- parent agent defines branch prompts and output schema
- parent agent may spawn bounded repo-local or global workers when branches are independent
- each branch writes `_workspace/{phase}_position_{branch}.md`
- final synthesis compares agreements, conflicts, evidence quality, and open risks

Avoid Fan-out/Fan-in when branches are not truly independent.

## Expert Pool

Use when only a subset of specialists should be invoked for a request.

Portable Codex implementation:

- team spec lists specialists and trigger criteria
- orchestrator chooses only relevant skills
- unused specialists are not loaded or invoked
- routing decisions are recorded in `_workspace/{phase}_routing.md` for complex cases

Avoid Expert Pool when every request always uses every role.

## Producer-Reviewer

Use when output quality risk is high and a separate review lens helps.

Portable Codex implementation:

- producer writes the artifact
- reviewer checks against explicit criteria
- producer repairs only findings that are concrete and in scope
- review loop is bounded, usually one or two passes

Avoid Producer-Reviewer when the review would only restate style preferences.

## Supervisor

Use when work units change dynamically.

Portable Codex implementation:

- supervisor owns backlog and assignment rules
- each work unit has owner, output path, and done condition
- reassignment is explicit
- no hidden recursive delegation

Avoid Supervisor when a fixed pipeline is enough.

## Hierarchical Delegation

Use when the work naturally decomposes into layers.

Portable Codex implementation:

- top-level orchestrator decomposes into sub-goals
- at most one downstream coordination layer by default
- child-level outputs are file-based and summarized for integration
- recursion depth is justified in the team spec

Avoid Hierarchical Delegation when it creates routing complexity without quality gain.

## Pattern selection checklist

Ask:

1. Can a single skill do this well?
2. Is sequential dependency real?
3. Are branches independent enough to split?
4. Is there a high-risk artifact that needs review?
5. Does the backlog change during execution?
6. Does the domain have natural hierarchy?
7. Will the chosen pattern reduce ambiguity or merely add ceremony?

Select the first pattern that answers the quality risk with the least durable machinery.
