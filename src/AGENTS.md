# Canonical skill source

## 범위

`src/skills/`는 Prime, Run, Set, Run TDD의 공통 Markdown 계약과 reference를 소유한다. Claude/Codex manifest, host interface metadata, 생성 패키지, repository release 문서는 이 모듈의 소유가 아니다.

## 경계

- 공통 행동 의미는 이 디렉터리에서 수정한다. `claude/`와 `codex/plugin/`의 대응 파일을 직접 고치지 않는다.
- Host별 권한·표시 이름·호출 정책을 공통 계약에 섞지 않는다. 공통 의미가 아닌 차이는 `platform/` 입력 또는 build-time injection으로 남긴다.
- Prime은 승인 계약 생산, Run은 실행, Set은 기존 프로젝트 온보딩, Run TDD는 Run의 선택적 TDD 래퍼라는 역할을 서로 침범하지 않는다.

## 불변조건

- Run↔Set의 `harness-format.md`와 `harness-review.md`, Run↔Prime의 `foundation-format.md`는 각 쌍이 byte-identical이어야 한다.
- Execution graph는 producer가 소유하고 consumer는 유효한 graph만 실행한다. Consumer가 dependency나 regeneration barrier를 임의로 재설계해서는 안 된다.
- 승인 전 입력은 검토 재료이며 실행 권위가 아니다. 평가 불가능한 결과나 미처분 concern은 성공이 아니다.
- Run TDD는 Run보다 우선하지 않으며 관찰 가능한 행동 변경이 아닌 작업에 가짜 RED 단계를 요구하지 않는다.

## 구현 패턴

공통 규칙은 한 owning `SKILL.md` 또는 reference에 두고, 여러 skill이 실제로 독립 패키징해야 하는 reference만 명시적 물리 사본으로 유지한다. Dispatch prompt는 task 계약, worktree pin, verification, structured return을 완결된 형태로 전달하며 child가 사용자에게 직접 묻거나 다시 위임하지 않게 한다.

## 테스트

변경한 규칙의 소비 경로를 검증하는 가장 가까운 `tests/test_*_contract.py`를 실행한다. Shared reference 변경은 build parity, graph/recovery 변경은 malformed·interrupted·failure mutation, dispatch 변경은 host별 fresh-leaf·capacity·merge gate assertion을 포함해야 한다. 문자열 존재만으로 행동 성공을 주장하지 않는다.
