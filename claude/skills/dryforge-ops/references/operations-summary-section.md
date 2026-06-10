# Operations Summary Section

Canonical agent operations summary path:

```text
.agents/ops/operations.md
```

Project operations docs such as `docs/operations.md` are preserved separately and are not updated by dryforge-ops.

Use marker comments and replace only the marked block:

```markdown
<!-- dryforge-ops:start -->
## Dryforge 실행 상태

| 항목 | 현재 상태 | 다음 액션 |
| --- | --- | --- |
| Active 3문서 | `<state>` | active면 dryforge go 전후 control-plane 동기화 |
| 최신 archive | `<path>` | after-go evidence 연결 확인 |
| status marker | `<state>` | initialized 여부 확인 |
| 최근 검증 | `<command/exit>` | 실패 또는 누락이면 재검증 |
| 반복 workflow 후보 | `<domain/type>` | workflow 승격 검토 |
<!-- dryforge-ops:end -->
```

If an unmarked `## Dryforge 실행 상태` section exists, replace that section once and add markers. Never append duplicate headings.
