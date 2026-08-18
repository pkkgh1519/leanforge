# 보안 정책

## 보호 대상과 신뢰 경계

플러그인이 보호해야 하는 자산은 사용자의 저장소 내용, active local state, Git branch와 worktree, 생성 패키지의 무결성, 검증 로그에 포함될 수 있는 민감정보다. 제품은 별도 서버·데이터베이스·credential store를 운영하지 않는다. Claude Code·Codex 설치 및 원격 저장소 인증은 각 호스트와 Git 도구가 소유하며 플러그인이 토큰을 복사하거나 보관하지 않는다.

## 권한 모델

| 주체 | 허용 동작 | 조건 | 명시적으로 금지되는 동작 |
|---|---|---|---|
| 사용자 | 목표·결정 승인, main 통합·게시 승인, 복구 방향 선택 | 영향과 증거를 확인한 뒤 명시적으로 결정 | 검증되지 않은 결과를 검증 완료로 자동 승격시키는 것 |
| 실행 에이전트 | 승인 범위의 파일 수정, 격리 branch/worktree 생성, 로컬 검증 | 현재 저장소·branch·HEAD와 쓰기 범위를 먼저 확인 | active state 덮어쓰기, 무단 reset·history rewrite, 승인 없는 push·PR·tag·Release |
| 빌드 | 정본과 호스트 오버레이에서 generated package 재생성 | 로컬 저장소 안의 고정된 입력만 사용 | generated package를 새 정본으로 취급하거나 정본을 역수정하는 것 |
| CI | build, drift 검사, 전체 contract test, whitespace 검사 | checkout된 commit과 선언된 workflow 안에서 실행 | 테스트 우회를 위해 assertion·검증 순서를 약화하는 것 |

## 실패 시 보호 규칙

Git root·branch·HEAD가 예상과 다르거나 worktree가 다른 branch에 연결되어 있으면 쓰기 전에 중단한다. active state가 두 위치에서 충돌하거나 archive hash가 다르면 어느 쪽도 삭제·병합하지 않는다. 생성 중간 실패로 패키지가 부분 상태가 되면 손으로 일부 파일을 복구하지 않고 원인을 해결한 뒤 전체 build를 다시 실행하고 Git diff로 원상복구를 증명한다.

## 민감정보

저장소 내용과 검증 로그는 사용자 데이터로 취급한다. 지원 요청, issue, PR, release note에 로그를 붙이기 전 token, API key, credential, 개인 경로와 불필요한 저장소 내용을 제거한다. 보안 취약점은 공개 issue로 먼저 공개하지 않고 저장소의 비공개 보안 신고 채널을 사용한다. credential 생성·회전·폐기는 플러그인의 런타임 기능이 아니며 호스트 또는 Git provider 정책을 따른다.

## 기록해야 하는 보안 사건

active state 또는 worktree 유실 시도, destructive Git 명령 거부, 승인 없는 외부 쓰기 시도, canonical/generated 무결성 실패, 검증 로그의 비밀정보 노출은 사용자에게 즉시 보고한다. 기록에는 대상, 실행되지 않았거나 실패한 동작, 보존된 상태, 필요한 다음 승인을 포함하되 비밀값 자체는 포함하지 않는다.
