# 소비자 인터페이스 계약

## 공통 식별자와 접근

Plugin identity는 `leanforge`, 배포 저장소는 `pkkgh1519/leanforge`다. Claude Code와 Codex의 command는 사용자가 명시적으로 호출하는 대화형 쓰기 기능이다. 제품은 HTTP API, background service, event stream을 제공하지 않으며 별도 인증 token을 발급하지 않는다. 설치와 저장소 접근 권한은 각 호스트 및 Git provider가 소유한다.

## Command 카탈로그

### Prime

- **호출:** Claude Code와 Codex의 `/leanforge:prime`.
- **입력:** 자연어 목표, 기존 설계 문서, 메모, 저장소 증거의 조합.
- **출력:** 사용자 검토를 위한 의도·요구사항·실행 순서 계약과 중요한 미확정 결정 질문.
- **오류:** Git 저장소가 아니거나, 자료 간 중요한 충돌이 사용자 결정 없이 해소될 수 없거나, 실행 계약의 graph가 유효하지 않으면 실행 준비 완료를 주장하지 않는다.

### Run

- **호출:** Claude Code와 Codex의 `/leanforge:run`.
- **입력:** 사용자가 승인한 실행 계약, 현재 Git branch/commit/worktree 사실, 프로젝트 검증 명령.
- **출력:** feature branch의 구현 commit, 실행한 명령과 exit code, review·integration 결과, 사용자에게 남은 통합 선택.
- **오류:** 승인 계약 부재·불일치, malformed dependency graph, active state 충돌, child의 `BLOCKED`/`NEEDS_CONTEXT`, 검증 실패, 미처분 concern은 완료가 아니라 중단 또는 사용자 질문으로 반환한다.

### Set

- **호출:** Claude Code와 Codex의 `/leanforge:set`.
- **입력:** 기존 저장소의 코드·문서와 코드로 알 수 없는 사용자 결정.
- **출력:** 두 호스트의 동일한 프로젝트 진입 지침, 프로젝트 문서, 의미 있는 module별 작업 지침.
- **오류:** 기존 프로젝트 지침과 새 구조가 충돌하거나 사용자만 결정할 수 있는 제품 규칙이 비어 있으면 덮어쓰지 않고 disposition 또는 답변을 요청한다.

### Run TDD

- **호출:** Claude Code와 Codex의 `/leanforge:run-tdd`.
- **입력:** Run과 같은 승인 계약. 관찰 가능한 행동 변경 task에는 acceptance behavior와 검증 seam이 필요하다.
- **출력:** Run 결과에 행동 단위 RED→GREEN→refactor와 acceptance evidence를 추가한다.
- **오류:** Run 자체의 precondition이 실패하면 래퍼도 실패한다. 행동 test가 구현 세부 문자열, skipped test, 약화된 assertion에 의존하면 acceptance evidence로 인정하지 않는다. 문서·단순 설정·mechanical 작업에는 가짜 RED 단계를 만들지 않는다.

## Codex 호출 정책

Codex의 Prime, Run, Set, Run TDD metadata는 `policy.allow_implicit_invocation: false`다. Host 또는 agent가 사용자의 명시적 command 없이 이 workflow를 자동 시작해서는 안 된다. Canonical metadata와 generated package에서 이 값이 다르면 배포 계약 위반이다.

## Version 계약

현재 candidate manifest version은 `1.8.2`다. 소비자가 보는 README 제목, CHANGELOG 첫 entry, Claude·Codex canonical/generated manifest는 같은 version이어야 한다. Version label이 없거나 둘 이상이거나 서로 다르면 build가 non-zero로 종료하며 해당 package는 릴리스 후보가 아니다.
