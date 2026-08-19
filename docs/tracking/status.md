# 프로젝트 상태

## 검증된 현재 상태

- **v1.9.0 semantic contract foundation:** 기존 monolithic Run orchestration을 유지하면서 route topology, external proof, failure precedence, completion reuse, concern disposition, lifecycle·review ownership, user output 의미를 작은 machine-readable kernel과 stable protected Markdown block으로 결속했다.
- **Instruction load graph:** Run의 instruction path와 activation edge를 별도 graph로 정의하고 route·overlay·phase·profile별 transitive closure를 하나의 deterministic activation path로 검증한다.
- **독립 검증 기반:** hand-authored scenario, known-opposite mutation, canonical·generated skill surface의 exact raw-byte baseline으로 semantic kernel과 load closure를 독립 검증한다.
- **Release consistency guard:** build가 Git 없이 일곱 release surface의 정확한 label을 읽고 missing·ambiguous·mismatch를 거부한다. Baseline, 본문 예시 제외, 각 mutation을 focused 10개 test로 검증했다.
- **명시적 Run TDD 호출:** Codex canonical/generated metadata에 implicit invocation 금지가 일치한다.
- **Generated parity CI:** build 뒤 tracked drift, untracked output, 전체 unittest, whitespace를 순서대로 차단한다.

## 남은 확정 목표

1. **v1.9.1 block-preserving split:** v1.9.0 계약을 기준으로 core·worktree·parallel·external·failure overlay를 분리한다. Split 전후 의미, 재귀 load closure budget, 독립 행동 review를 통과해야 한다.

이 목표는 다음 확정 결과지만 현재 구현을 자동 승인하지 않는다. v1.9.1은 검증된 v1.9.0 foundation을 보존해야 한다.

## 미래 방향

- 실제 Claude Code·Codex host에서 별도 승인 후 20회 behavior smoke로 deterministic contract 외의 host 동작을 관찰한다.
- Token·latency 개선을 주장할 필요가 생길 때만 100회 반복 측정을 사용한다. 반복 측정은 deterministic gate를 대체하지 않는다.

## 차단 사항

현재 확인된 제품 blocker는 없다. 다음 확정 개발 목표는 v1.9.1 block-preserving split이며, 새 Prime delta에서 실행 범위를 승인한 뒤 시작한다.
