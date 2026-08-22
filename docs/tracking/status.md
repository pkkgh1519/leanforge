# 프로젝트 상태

## 검증된 현재 상태

- **v1.9.0 semantic contract foundation:** 기존 monolithic Run orchestration을 유지하면서 route topology, external proof, failure precedence, completion reuse, concern disposition, lifecycle·review ownership, user output 의미를 작은 machine-readable kernel과 stable protected Markdown block으로 결속했다.
- **Instruction load graph:** Run의 instruction path와 activation edge를 별도 graph로 정의하고 route·overlay·phase·profile별 transitive closure를 하나의 deterministic activation path로 검증한다.
- **독립 검증 기반:** hand-authored scenario, known-opposite mutation, canonical·generated skill surface의 exact raw-byte baseline으로 semantic kernel과 load closure를 독립 검증한다.
- **Adaptive Assurance shadow foundation:** Prime은 ELICIT exit에서 Lite·Standard·Assurance advisory prediction을 `.leanforge/assurance-shadow.json`에 기록한다. 이 snapshot은 실행 권위가 없고 Full Assurance 흐름을 바꾸지 않는다.
- **Shadow observation integrity:** sidecar는 현재 Prime cycle의 교체 가능한 ELICIT-exit prediction으로 한정된다. 새 record가 완성되지 않으면 이전 snapshot을 현재 결과로 남기지 않으며, closed Lite fact partition과 `unknown_material_risk` fail-closed 경계를 검증한다.
- **Phase 1.2 observation study protocol:** shadow prediction을 숨긴 상태에서 최종 3-doc·review·Run 증거로 observed class를 독립 판정하고, redacted manual worksheet로 exact·conservative·underclassification·unevaluable 결과를 기록한다. 완료 record는 공개 저장소에 커밋하지 않는다.
- **Release consistency guard:** build가 Git 없이 일곱 release surface의 정확한 label을 읽고 missing·ambiguous·mismatch를 거부한다. Baseline, 본문 예시 제외, 각 mutation을 focused test로 검증했다.
- **명시적 Run TDD 호출:** Codex canonical/generated metadata에 implicit invocation 금지가 일치한다.
- **Generated parity CI:** build 뒤 tracked drift, untracked output, 전체 unittest, whitespace를 순서대로 차단한다.

## 남은 확정 목표

1. **Adaptive Assurance Phase 1.2 실행:** 최소 35개의 usable real observation을 수집하되 shadow Lite 15건 이상, Standard 10건 이상, Assurance 10건 이상을 포함한다. 부재·unevaluable record는 성공으로 세지 않고 별도 보고한다.
2. **Bounded Lite activation review:** zero unresolved Lite-to-Assurance cases, 모든 underclassification의 개별 disposition, 대표 coverage, shadow로 인한 추가 사용자 질문·live workflow 변경 없음이 확인된 뒤에만 별도 reviewed release를 설계한다. Observation study 자체는 activation 권위가 아니다.
3. **v1.9.1 block-preserving split:** v1.9.0 계약을 기준으로 core·worktree·parallel·external·failure overlay를 분리한다. Adaptive Assurance activation과 같은 릴리스에 묶지 않으며, split 전후 의미·재귀 load closure budget·독립 행동 review를 따로 통과해야 한다.

각 목표는 현재 구현을 자동 승인하지 않는다. Lite activation과 block-preserving split은 각각 독립된 사용자 승인과 release review를 요구한다.

## 미래 방향

- 실제 Claude Code·Codex host에서 별도 승인 후 behavior smoke로 deterministic contract 외의 host 동작을 관찰한다.
- Phase 1.2의 redacted aggregate report가 준비된 뒤에만 Lite eligibility 조정 또는 Phase 2 route 설계를 논의한다.
- Token·latency 개선을 주장할 필요가 생길 때만 반복 측정을 사용한다. 반복 측정은 deterministic gate나 관측 연구의 독립 판정을 대체하지 않는다.

## 차단 사항

현재 Full Assurance 제품 흐름에 확인된 blocker는 없다. 다만 Lite activation gate는 Phase 1.2 coverage와 zero unresolved Lite-to-Assurance 조건을 충족하고 별도 reviewed release가 승인될 때까지 의도적으로 닫혀 있다.
