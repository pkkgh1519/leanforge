# Installation

Leanforge is distributed from the GitHub repository `pkkgh1519/leanforge`.
The installed plugin identity is `leanforge`; the user-facing product name is
Leanforge.

## Requirements

- `git` available on `PATH`
- Claude Code or Codex
- A repository workspace for normal Leanforge use

Leanforge commands rely on git-aware project state. If a target project is not a
git repository yet, Leanforge may ask you to initialize one before execution.

## Claude Code

Add the marketplace source, then install the plugin:

```text
/plugin marketplace add pkkgh1519/leanforge
/plugin install leanforge
```

## Codex

Add the marketplace source, then install the plugin:

```text
codex plugin marketplace add pkkgh1519/leanforge
codex plugin add leanforge@leanforge
```

## Verify the install and invoke the skills

### Claude Code

The command palette should expose:

| Skill | Claude Code command | Purpose |
|---|---|---|
| `Leanforge:Prime` | `/leanforge:prime` | Turn intent into a reviewed executable design contract. |
| `Leanforge:Run` | `/leanforge:run` | Execute the approved contract with evidence gates. |
| `Leanforge:Set` | `/leanforge:set` | Onboard an existing codebase into the project harness. |
| `Leanforge:Run TDD` | `/leanforge:run-tdd` | Optional wrapper around `Run` with selective TDD discipline. |

### Codex

Codex plugins bundle skills; they do not create `/leanforge:*` slash commands. In Codex CLI, use
`/skills` or type `$` to select the installed Leanforge skill. When names are unambiguous, mention
`$prime`, `$run`, `$set`, or `$run-tdd` directly. In the ChatGPT desktop Codex surface, select the
corresponding skill from the installed plugin/skill picker. Start a new session after installation or
an update.

`Leanforge:Run TDD` is optional on both hosts; the core lifecycle is `Prime` -> `Run`. See
[when to use it](troubleshooting.md#when-to-use-leanforgerun-tdd-instead-of-leanforgerun).

To test an unreleased branch in Codex, do not treat the checked-out source or a version label as proof
of execution. Use the commit-pinned, reversible local marketplace procedure in
[Test an exact local Codex candidate](local-candidate-testing.md), then verify the active cache path
against the generated package digest before running Prime or Run.

## First successful run

Use a small, observable request first. On Claude Code:

```text
/leanforge:prime Build a minimal booking flow for a single service business.
```

On Codex CLI, select the Leanforge Prime skill with `/skills` or use:

```text
$prime Build a minimal booking flow for a single service business.
```

Review the approval summary and the contract details that carry product decisions. After approval,
use `/leanforge:run` on Claude Code or `$run` on Codex.

A successful run reports four clearly labeled sections in the user's language:
**Change**, **Verification**, **Remaining risk**, and **Integration**. The sections contain the actual
result, captured evidence, unverified scope or concerns, and the user-owned merge, PR/push, or
branch-handoff choice. A terminal blocker uses the same sections to preserve partial state, prove the
stop, name the blocker, and state that the result is not ready to integrate.

## Version notes

- `v1.8.1` tightens the `Run TDD` policy: seams are fixed before the first test of a task, and
  tautological assertions are rejected as tests and as AC evidence.
- `v1.8.0` packages `Leanforge:Run TDD` for Claude Code, generated from the same canonical
  source as the Codex wrapper. Behavior and content are unchanged; only availability widens.
- `v1.7.1` restores parallel wave execution on Claude Code. That host queues children
  without exposing a capacity preflight, so `Run` no longer degrades a ready wave to one
  child at a time; it dispatches the wave in parallel, bounded only by a limit you set.
  Codex admission behavior is unchanged.
- `v1.7.0` compresses the Prime and Run instructions, makes Codex leaf dispatch and
  `fork_turns: "none"` explicit, sizes batches from host-aware live runtime slots,
  restores the full completion and post-gate cleanup contracts, makes Run TDD
  self-contained, and removes the optional Harness meta-skill. Other execution
  semantics remain aligned with v1.6.9.
- `v1.6.9` remains tagged as the Prime source-difference materiality baseline. It keeps
  harmless or authority-resolved source variance from becoming strategy questions
  while retaining grounded questions for unresolved current normative conflicts.
- `v1.6.8` remains tagged as the harness-authority and graph-contract baseline.
- `v1.6.7` remains tagged as the outcome-preservation baseline.
- `v1.6.6` remains tagged as the SDD-lite Stage 1 baseline for environments
  that explicitly pin repository tags or release versions.
- If the client does not expose version pinning, marketplace installation uses
  the version resolution behavior of that client.

## Next docs

- [Troubleshooting](troubleshooting.md)
- [Dryforge to Leanforge migration](migration-dryforge-to-leanforge.md)
