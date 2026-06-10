# Team Examples

## Research pipeline

```text
research-orchestrator -> evidence-reviewer -> synthesis-reviewer
```

Artifacts:

```text
_workspace/01_scope_summary.md
_workspace/02_evidence_table.md
_workspace/03_synthesis.md
docs/harness/research/team-spec.md
```

## Producer-reviewer for documentation

```text
docs-producer -> docs-reviewer -> docs-producer repair
```

Artifacts:

```text
_workspace/01_docs_draft.md
_workspace/02_docs_review.md
_workspace/03_docs_final.md
```

## Fan-out/Fan-in code review

```text
security_position
correctness_position
testability_position
maintainability_position
synthesis
decision
```

Artifacts:

```text
_workspace/01_position_security.md
_workspace/01_position_correctness.md
_workspace/01_position_testability.md
_workspace/01_position_maintainability.md
_workspace/02_review_synthesis.md
_workspace/03_review_decision.md
```

## Expert pool for product work

Specialists:

- market-research
- technical-architecture
- risk-reviewer
- copy-editor

Routing:

- invoke market-research only when user asks about users, competitors, or positioning
- invoke technical-architecture only when implementation or system design is in scope
- invoke risk-reviewer whenever privacy, security, legal, or high-stakes claims are present
- invoke copy-editor after content exists
