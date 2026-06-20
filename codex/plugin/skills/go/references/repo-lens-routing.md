# repo-lens-routing.md — repo-local review/explore lenses

Use this reference only after the normal `go` execution rules have selected a review or diagnostic
phase. A repo-local lens is a skill or custom agent generated for one repository's repeated risks.
It helps `go` inspect the result; it never owns execution.

## Authority boundary

`go` keeps execution authority. A repo-local skill or agent is a review/explore/checklist lens, not
an implementer. It may sharpen review criteria, point at repository-specific evidence, or explore a
failure, but the orchestrator still owns scheduling, worktrees, merge-gates, completion gates,
fix-dispatch, user escalation, harness updates, and archive/marker lifecycle.

Hard stops:

- A repo-local lens MUST NOT replace implementer dispatch.
- A repo-local lens MUST NOT manage worktrees.
- A repo-local lens MUST NOT run the merge gate or decide that a merge is safe.
- A repo-local lens MUST NOT manage `.dryforge/run.json`, `.dryforge/status.json`, or archives.
- A repo-local lens MUST NOT read .dryforge active docs; pass the needed spec slice, changed files,
  diff or commit range, and verification evidence inline.
- A repo-local lens MUST NOT broaden the task beyond the active spec.

## Allowed phases

Use repo-local lenses only in these phases:

1. **final review** — add a matching repo-local skill checklist or reviewer lens to the ordinary
   final reviewer dispatch.
2. **conditional spec-review** — when the existing review policy triggers, add a matching lens for
   the risky surface being reviewed.
3. **failure exploration** — after a gate fails, use a read-heavy repo-local skill or custom agent to
   investigate likely repository-specific causes before fix-dispatch.

Do not use a repo-local lens for ordinary implementation, wave scheduling, scaffold ownership,
worktree lifecycle, merge-gate decisions, or status tracking.

## Discovery and selection

Look for repo-local skills under `.agents/skills/` whose description or `## Dryforge go usage`
section maps to the current changed scope. Optional Codex custom agents may exist under
`.codex/agents/`; prefer them only for read-heavy reviewer/explorer work where an independent thread
adds value.

Selection rules:

- Prefer zero lenses for small mechanical changes.
- Prefer one matching lens; use at most two when the changed scope genuinely spans two independent
  risk surfaces.
- Prefer skills before custom agents. Skills add a checklist; custom agents add another thread.
- Prefer read-only custom agents for exploration or review.
- If selection is ambiguous, skip the lens and rely on the normal final review.
- If a lens asks for missing context, provide a bounded inline slice; do not let it fetch active
  `.dryforge` task docs directly.

## Inputs supplied by go

When a lens is used, provide only the context it needs:

- changed files
- relevant spec slice
- hard gates that apply to the surface
- diff or commit range
- verification commands and captured exit codes
- known failure output for failure exploration

## Output expected from a lens

A repo-local lens returns:

- blocking findings with evidence and fix direction
- advisory findings
- missing evidence
- uncertainty or scope limits

The orchestrator triages the result under the normal `go` review and fix policy.
