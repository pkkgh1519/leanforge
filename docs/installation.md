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

## Verify the install

After installation, the command palette should expose these commands:

| Command | Purpose |
|---|---|
| `Leanforge:Prime` (`/leanforge:prime`) | Turn intent into a reviewed executable design contract. |
| `Leanforge:Run` (`/leanforge:run`) | Execute the approved contract with evidence gates. |
| `Leanforge:Set` (`/leanforge:set`) | Onboard an existing codebase into the project harness. |
| `Leanforge:Harness` (`/leanforge:harness`) | Design or improve reusable agent workflows and skills. |
| `Leanforge:Run TDD` (`/leanforge:run-tdd`) | Codex-only wrapper for behavior-changing work with selective TDD guidance. |

If `Leanforge:Run TDD` is absent in Claude Code, that is expected: it is a
Codex-only wrapper. The core lifecycle is still `Prime` -> `Run`.

## First successful run

Use a small, observable request first:

```text
/leanforge:prime Build a minimal booking flow for a single service business.
```

Review the generated spec, plan, and handoff. After approval, run:

```text
/leanforge:run
```

A successful run should report the implemented changes, checks run, evidence,
and project harness updates when applicable.

## Version notes

- `v1.6.8` is the current harness-authority and graph-contract release. It keeps
  durable context section-aware and rejects parseable but structurally invalid
  Execution Graph output before Run.
- `v1.6.7` remains tagged as the outcome-preservation baseline.
- `v1.6.6` remains tagged as the SDD-lite Stage 1 baseline for environments
  that explicitly pin repository tags or release versions.
- If the client does not expose version pinning, marketplace installation uses
  the version resolution behavior of that client.

## Next docs

- [Troubleshooting](troubleshooting.md)
- [Dryforge to Leanforge migration](migration-dryforge-to-leanforge.md)
