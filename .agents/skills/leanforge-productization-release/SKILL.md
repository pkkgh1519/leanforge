---
name: leanforge-productization-release
description: "Use when preparing, reviewing, or shipping a Leanforge productization or release batch, including GitHub releases, tags, About metadata, README quickstarts, CI, install/troubleshooting/migration docs, examples, support docs, PR hygiene, and post-merge validation. Use for Leanforge repository release checklists and recurring productization roadmap execution."
---

# Leanforge Productization Release

Use this skill to ship Leanforge productization work without losing release
hygiene. Keep it scoped to this repository unless the user explicitly asks to
create a global skill.

## Operating stance

- Prefer small PR batches over one broad productization PR.
- Treat `main` as the release baseline.
- Do not rewrite release history or move existing tags without explicit approval.
- Use draft PRs by default, then mark ready only after review and passing checks.
- Keep official docs neutral and product-grade; do not include persona, internal
  conversation context, or speculative claims.
- Do not claim validation unless it ran. If blocked, state the exact blocker and
  strongest substitute evidence.

## Standard batch order

1. Release surface:
   - verify tags and GitHub Release;
   - update repository About description, homepage, and topics;
   - confirm release notes explain compatibility and validation.
2. First-run surface:
   - README badges;
   - install commands;
   - verify-install section;
   - first successful run path.
3. User support docs:
   - installation;
   - troubleshooting;
   - rename or migration guidance;
   - README links.
4. Examples:
   - workflow examples before generated sample apps;
   - copy-paste prompt bodies;
   - expected decision and evidence shape.
5. Operations docs:
   - contributing;
   - security policy;
   - support process.
6. Optional polish:
   - social preview;
   - screenshots;
   - richer demos.

## Preflight

Before editing:

1. Check local branch and status.
2. Sync `main` from origin.
3. Create a focused branch, for example:
   - `productize/quickstart-ci`
   - `productize/docs-install-troubleshooting`
   - `productize/example-booking-system`
   - `productize/operations-and-release-skill`
4. Inspect relevant files before changing them.
5. State the intended PR scope and files likely to change.

## Release and GitHub surface checklist

Use live GitHub checks when the user has approved external side effects:

- `gh release view <tag>` before creating or editing a release.
- `gh release create` only when the tag exists and no release exists.
- `gh repo view --json description,homepageUrl,repositoryTopics` before editing
  About metadata.
- `gh repo edit` only for the intended description, homepage, and topics.

Do not invent release validation. Use actual test output, CI runs, local E2E
reports, or clearly labeled substitute evidence.

## Documentation checklist

For each doc batch:

- Keep commands consistent with README:
  - `/leanforge:prime`
  - `/leanforge:run`
  - `/leanforge:set`
  - `/leanforge:harness`
  - `/leanforge:run-tdd` for Codex only
- Keep marketplace source as `pkkgh1519/leanforge`.
- Keep plugin identity as `leanforge`.
- Avoid legacy URLs and old owner paths.
- Link from README and README_KO when the doc is user-facing.
- Make examples workflow-level unless the user explicitly asks for maintained
  sample application code.

## Validation checklist

Run the relevant checks before committing:

```text
python -m unittest discover -s tests -v
git diff --cached --check
```

Also run a markdown link-target check for changed README/docs/examples files.
Search changed docs for forbidden legacy strings:

```text
fn-opt/dryforge
fn-opt/leanforge
dryforge.vercel.app
Website (legacy URL)
/leanforge:herness
harness:*
```

## PR checklist

Before opening or merging a PR:

1. Stage only intended files.
2. Review `git diff --cached --stat` and `git diff --cached --name-only`.
3. Commit with a concise message.
4. Push the focused branch.
5. Open a draft PR with:
   - summary;
   - why;
   - validation.
6. Wait for GitHub Actions.
7. Review PR metadata: files, checks, mergeability, and commits.
8. Mark ready and merge only after checks pass and scope matches the plan.
9. Sync local `main` after merge.

## Completion report

Report:

- PRs created or merged;
- branch and commit IDs;
- files changed;
- validation run locally and in CI;
- any remaining manual tasks, such as GitHub social preview.
