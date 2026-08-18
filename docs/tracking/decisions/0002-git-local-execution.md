# 0002 — Git 로컬 실행 경계

## 배경

제품은 사용자 저장소의 승인된 변경, branch, worktree, 검증 결과를 다룬다. 중앙 서버를 추가하면 credential 보관, 원격 상태 동기화, 실행 권한 위임이 필요하고 active local state와 원격 state 중 어느 쪽이 권위인지 새로운 충돌이 생긴다.

## 결정

실행과 복구 상태는 사용자 저장소와 Git 사실을 기준으로 처리한다. 별도 runtime service, database, credential store를 두지 않는다. 격리가 필요하면 Git branch/worktree를 사용하고, main 통합과 원격 게시 권한은 사용자에게 남긴다.

## 대안

- **중앙 orchestration service:** 여러 machine의 상태를 모을 수 있지만 사용자 코드·credential·실행 권한을 서버에 맡겨야 하고 로컬 Git과의 충돌 복구가 복잡해진다.
- **Git 없이 파일 snapshot만 사용:** 초기 진입은 가볍지만 branch ancestry, 독립 worktree, commit 기반 검증 재사용을 신뢰할 수 없다.

## 결과

Git이 없는 저장소에서는 정상 실행을 시작할 수 없다. Active state나 worktree가 불일치하면 자동 복구보다 보존과 사용자 결정을 우선한다. 서버 기반 동시 실행, 계정 관리, 원격 credential lifecycle은 현재 제품이 제공할 수 없다.
