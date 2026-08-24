# 소비자 인터페이스 계약

## 제품 결과 계약

사용자가 받는 최종 결과의 권위는 `docs/business-rules.md`의 제품 북극성을 따른다. 정상 경로의 제품 산출물은 승인 가능한 의도 계약, 검증된 실제 변경, 신뢰 증거와 잔여 위험 요약, 통합 선택, 그리고 실제로 바뀐 경우에만 durable project knowledge다.

`lite | standard | assurance`, reviewer, worktree, wave, sidecar와 harness sync는 소비자 인터페이스가 아니다. 사용자는 mode를 선택하지 않으며 내부 분류를 위해 추가 질문을 받지 않는다. 내부 mechanism 변경이 사용자 질문·승인 단계·읽기 부담·Time to Trusted Change를 늘리면 인터페이스 회귀로 취급한다.

## 공통 식별자와 접근

Plugin identity는 `leanforge`, 배포 저장소는 `pkkgh1519/leanforge`다. Claude Code와 Codex의 command는 사용자가 명시적으로 호출하는 대화형 쓰기 기능이다. 제품은 HTTP API, background service, event stream을 제공하지 않으며 별도 인증 token을 발급하지 않는다. 설치와 저장소 접근 권한은 각 호스트 및 Git provider가 소유한다.

## Command 카탈로그

### Prime

- **호출:** Claude Code와 Codex의 `/leanforge:prime`.
- **입력:** 자연어 목표, 기존 설계 문서, 메모, 저장소 증거의 조합.
- **출력:** 사용자가 이해하고 승인할 수 있는 의도·요구사항·실행 순서 계약, 간결한 승인 요약, 사용자만 결정할 수 있는 중요한 미확정 질문.
- **제품 경계:** repository-derived 기술 판단과 내부 mode 선택을 사용자에게 되묻지 않는다. Prime 산출물은 Run이 대화를 재추론하지 않고 실행할 수 있어야 한다.
- **오류:** Git 저장소가 아니거나, 자료 간 중요한 충돌이 사용자 결정 없이 해소될 수 없거나, 실행 계약의 graph가 유효하지 않으면 실행 준비 완료를 주장하지 않는다.

### Run

- **호출:** Claude Code와 Codex의 `/leanforge:run`.
- **입력:** 사용자가 승인한 실행 계약, 현재 Git branch/commit/worktree 사실, 프로젝트 검증 명령.
- **출력:** feature branch의 검증된 실제 변경 또는 외부 결과, 실행한 명령과 exit code, review·integration 결과, 잔여 위험과 사용자에게 남은 통합 선택.
- **최종 보고 형식:** 성공과 복구가 소진된 terminal blocker 모두 사용자 언어로 명확히 구분한 **변경**, **검증**, **남은 위험**, **통합** 네 구역을 사용한다. 성공 시 실제 변경 또는 외부 결과, 관찰된 명령·출력·exit code와 runtime evidence, 미검증 범위·concern·복구 상태, 사용자 소유의 merge·PR/push·branch handoff 선택을 각각 담는다. blocker 시에는 완료·보존된 상태 또는 변경 없음, 중단을 증명하는 evidence, blocker·복구 상태, 통합 불가와 안전한 다음 선택을 같은 구역에 기록한다.
- **제품 경계:** 내부 plumbing보다 결과와 증거를 우선한다. 완료 요약은 사용자가 무엇이 바뀌었고 왜 믿을 수 있으며 무엇을 선택해야 하는지 알 수 있어야 한다.
- **오류:** 승인 계약 부재·불일치, malformed dependency graph, active state 충돌, child의 `BLOCKED`/`NEEDS_CONTEXT`, 검증 실패, 미처분 concern은 완료가 아니라 중단 또는 사용자 질문으로 반환한다.

### Set

- **호출:** Claude Code와 Codex의 `/leanforge:set`.
- **입력:** 기존 저장소의 코드·문서와 코드로 알 수 없는 사용자 결정.
- **출력:** 두 호스트의 동일한 프로젝트 진입 지침, 프로젝트 문서, 의미 있는 module별 작업 지침.
- **제품 경계:** 다음 작업에서 반복 설명·재발견을 줄이는 durable knowledge만 보존한다. per-change 기록이나 바뀌지 않은 지식을 갱신하기 위한 문서 churn을 만들지 않는다.
- **오류:** 기존 프로젝트 지침과 새 구조가 충돌하거나 사용자만 결정할 수 있는 제품 규칙이 비어 있으면 덮어쓰지 않고 disposition 또는 답변을 요청한다.

### Run TDD

- **호출:** Claude Code와 Codex의 `/leanforge:run-tdd`.
- **입력:** Run과 같은 승인 계약. 관찰 가능한 행동 변경 task에는 acceptance behavior와 검증 seam이 필요하다.
- **출력:** Run 결과에 행동 단위 RED→GREEN→refactor와 acceptance evidence를 추가한다.
- **오류:** Run 자체의 precondition이 실패하면 래퍼도 실패한다. 행동 test가 구현 세부 문자열, skipped test, 약화된 assertion에 의존하면 acceptance evidence로 인정하지 않는다. 문서·단순 설정·mechanical 작업에는 가짜 RED 단계를 만들지 않는다.

## Adaptive Assurance 소비자 경계

- Adaptive Assurance는 별도 command나 사용자 선택 항목이 아니다.
- shadow sidecar와 mode label은 advisory 내부 상태이며 Prime 3-doc, Run route, 검증, 복구, 승인 또는 통합 권위를 갖지 않는다.
- 첫 live pilot은 strict Lite와 기존 Full Assurance 두 경로만 가질 수 있다. `standard`는 독립 실행 계약이 아니라 관측 label이다.
- 새 위험이나 불확실성이 나타나면 기존 Full Assurance로 단조 복귀한다. 사용자에게 mode를 다시 선택시키거나 낮은 경로로 되돌리지 않는다.
- pilot은 분류 안전성뿐 아니라 Prime overhead, 품질, 사용자 부담, 예상 절감과 복귀 가능성을 별도 release에서 검증해야 한다.

## Codex 호출 정책

Codex의 Prime, Run, Set, Run TDD metadata는 `policy.allow_implicit_invocation: false`다. Host 또는 agent가 사용자의 명시적 command 없이 이 workflow를 자동 시작해서는 안 된다. Canonical metadata와 generated package에서 이 값이 다르면 배포 계약 위반이다.

## Version 계약

현재 candidate manifest version은 `1.9.0`이다. 소비자가 보는 README 제목, CHANGELOG 첫 entry, Claude·Codex canonical/generated manifest는 같은 version이어야 한다. Version label이 없거나 둘 이상이거나 서로 다르면 build가 non-zero로 종료하며 해당 package는 릴리스 후보가 아니다.
