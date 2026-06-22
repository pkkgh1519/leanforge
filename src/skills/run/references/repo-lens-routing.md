# repo-lens-routing.md — repo-local review/explore lenses

Use this reference only after the normal `Run` execution rules have selected a review or diagnostic
phase. A repo-local lens is a skill generated for one repository's repeated risks.
It helps `Run` inspect the result; it never owns execution.

## Authority boundary

`Run` keeps execution authority. A repo-local skill is a review/explore/checklist lens, not
an implementer. It may sharpen review criteria, point at repository-specific evidence, or explore a
failure, but the orchestrator still owns scheduling, worktrees, merge-gates, completion gates,
fix-dispatch, user escalation, harness updates, and archive/marker lifecycle.

Hard stops:

- A repo-local lens MUST NOT replace implementer dispatch.
- A repo-local lens MUST NOT manage worktrees.
- A repo-local lens MUST NOT run the merge gate or decide that a merge is safe.
- A repo-local lens MUST NOT manage `.leanforge/run.json`, `.leanforge/status.json`, archives, or
  legacy `.dryforge` migration state.
- A repo-local lens MUST NOT read .leanforge active docs or legacy .dryforge active docs; pass the
  needed spec slice, changed files, diff or commit range, and verification evidence inline.
- A repo-local lens MUST NOT broaden the task beyond the active spec.

## Allowed phases

Use repo-local lenses only in these phases:

1. **final review** — add a matching repo-local skill checklist or reviewer lens to the ordinary
   final reviewer dispatch.
2. **conditional spec-review** — when the existing review policy triggers, add a matching lens for
   the risky surface being reviewed.
3. **failure exploration** — after a gate fails, use a read-heavy repo-local skill to
   investigate likely repository-specific causes before fix-dispatch.

Do not use a repo-local lens for ordinary implementation, wave scheduling, scaffold ownership,
worktree lifecycle, merge-gate decisions, or status tracking.

## Discovery and selection

Look for repo-local skills under `.agents/skills/` whose description or `## Leanforge Run usage`
section maps to the current changed scope.

Selection rules:

- Prefer zero lenses for small mechanical changes.
- Prefer one matching lens; use at most two when the changed scope genuinely spans two independent
  risk surfaces.
- If selection is ambiguous, skip the lens and rely on the normal final review.
- If a lens asks for missing context, provide a bounded inline slice; do not let it fetch active
  `.leanforge` or legacy `.dryforge` task docs directly.

## Inputs supplied by Run

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

The orchestrator triages the result under the normal `Run` review and fix policy.
