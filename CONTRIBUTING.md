# Contributing to Leanforge

Thank you for helping improve Leanforge. This repository ships a multi-platform
plugin harness for Claude Code and Codex, so changes should preserve the contract
across source skills, generated platform surfaces, documentation, and tests.

## Development principles

- Keep changes small and reviewable.
- Preserve the existing command names and plugin identity unless the change is an
  intentional compatibility break.
- Do not weaken safety, validation, or recovery behavior to make a test pass.
- Update documentation when commands, setup, release behavior, state directories,
  or user-facing workflows change.
- Prefer focused tests for behavior and contract changes.

## Local setup

Clone the repository and work from a branch:

```text
git clone https://github.com/pkkgh1519/leanforge.git
cd leanforge
git switch -c <branch-name>
```

No package install is required for the current contract test suite.

## Validation

Run the contract tests before opening a pull request:

```text
python -m unittest discover -s tests -v
```

Also check staged whitespace before committing:

```text
git diff --cached --check
```

## Pull request checklist

Before requesting review, confirm:

- the branch is based on the latest `main`;
- the diff contains only the intended files;
- contract tests pass locally;
- GitHub Actions pass on the PR;
- docs are updated for user-facing behavior changes;
- generated platform surfaces still match their source contracts when applicable;
- release notes are prepared when the change is user-visible.

## Release-oriented changes

For productization or release work, use the repo-local
`leanforge-productization-release` skill in `.agents/skills/` as the operating
checklist. It covers release/about metadata, CI, docs, examples, and PR hygiene.

## Commit style

Use concise, descriptive commit messages. Examples:

```text
feat: add SDD-lite stage 1 guidance
docs: add installation and migration guides
docs: add booking workflow example
```

## Security-sensitive changes

Do not publish exploit details in public issues or pull requests. Follow
[SECURITY.md](SECURITY.md) for vulnerability reporting.
