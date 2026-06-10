# Workflow Upgrade Policy

`workflow suggest` only flags repeated task evidence. It never generates workflow
artifacts itself — designing reusable workflows is delegated to the `harness` skill.

| Signal | Candidate to raise with the harness skill |
| --- | --- |
| same task `type` 3+ times | reusable team spec |
| same review/security/QA/release flow 3+ times | specialist skill |
| same blocker 2+ times | troubleshooting reference |
| quality comparison needed | benchmark pack |

`workflow suggest` groups completed task-log events by their `type` field and prints,
for each candidate:

- `workflow_candidate=<type-slug>`
- `confidence=<low|medium|high>`
- `evidence_task_ids=<id,id,id>` — the repeated `task_id` values that justify the candidate
- `delegate_to=harness skill` — the signal to hand reusable workflow design to the harness skill

This bridge does not classify domains with hardcoded keyword lists and does not write
`.agents/workflows/` or `.agents/skills/` artifacts. When a candidate recurs, invoke the
`harness` skill to design, review, and install the reusable workflow with full judgment.
