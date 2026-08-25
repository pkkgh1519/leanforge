# orchestration.md — wave lifecycle (force-load)

The mechanics behind the SKILL's per-wave flow: scheduling, dispatch constraints, status handling,
context budget, and failure handling. Loaded for the whole run. The wave lifecycle is a proven
scaffold — keep its structure and the safety constraints; use judgment inside each step.

<!-- leanforge:run-load {"from":"run/references/orchestration.md","to":"run/references/implementer-prompt.md","kind":"prompt_load","phase":"dispatch","activation_contract_id":"RUN-ROUTE-TOPOLOGY","optional":false} -->
<!-- leanforge:run-load {"from":"run/references/orchestration.md","to":"run/references/spec-review-prompt.md","kind":"prompt_load","phase":"conditional_review","activation_contract_id":"RUN-REVIEW-TOPOLOGY","optional":false} -->
<!-- leanforge:run-load {"from":"run/references/orchestration.md","to":"run/references/reviewer-prompt.md","kind":"prompt_load","phase":"conditional_review","activation_contract_id":"RUN-REVIEW-TOPOLOGY","optional":false} -->
<!-- leanforge:run-load {"from":"run/references/orchestration.md","to":"run/references/reviewer-prompt.md","kind":"prompt_load","phase":"final_review","activation_contract_id":"RUN-REVIEW-TOPOLOGY","optional":false} -->

## Reporting principle

User-facing output follows `RUN-OUTPUT-SEMANTICS` in `SKILL.md`. Internal operations (merge, gate,
worktree lifecycle, branch cleanup, dependency install) produce **no text output**. Output tokens are
direct cost.

## Verification Plan

Before the first wave, write a compact verification plan in the orchestrator's working notes:

- command set and purpose
- which commands can run independently in parallel
- which commands are cheap per-wave gates
- which commands are expensive and reserved for the completion gate unless risk demands earlier use
- whether the project supports affected-only filtering for intermediate gates

The plan prevents re-deciding verification every wave. Independent commands may run in parallel as
long as each exit code is captured separately. The completion gate remains the full safety net.
