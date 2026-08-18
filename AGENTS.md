# 개발 지침

이 저장소는 Claude Code와 Codex에서 사용되는 MIT 라이선스의 로컬 Git 기반 워크플로 플러그인이다. 숨은 제품 결정을 실행 전에 드러내고, 승인된 계약을 격리된 Git 작업과 검증 증거로 구현하려는 사용자를 대상으로 한다. 런타임 서버나 데이터베이스를 운영하지 않으며 지원 호스트와 Git 위에서 동작한다.

## 프로젝트 구조

```text
project-root/
├── CLAUDE.md                         ← Claude Code 진입 지침
├── AGENTS.md                         ← Codex 진입 지침; CLAUDE.md와 동일
├── docs/
│   ├── architecture.md               ← 구성 요소, 생성 흐름, 의존 방향
│   ├── business-rules.md             ← 승인·실행·검증의 제품 규칙
│   ├── security.md                   ← 로컬 상태, Git, 공개 경계의 보호 정책
│   ├── standards.md                  ← 변경과 검증의 강제 규칙
│   ├── engineering-notes.md          ← 빌드·생성·검증의 비직관적 함정
│   ├── operations.md                 ← 설치, 빌드, 검증, 릴리스 절차
│   ├── contracts.md                  ← Claude Code·Codex 소비자 인터페이스
│   ├── installation.md               ← 호스트별 설치와 첫 실행
│   ├── migration-dryforge-to-leanforge.md ← 레거시 로컬 상태 이전 규칙
│   ├── troubleshooting.md            ← 설치·실행 실패 진단
│   ├── harness/
│   │   └── sdd-lite-stage-1-roadmap.md ← SDD-lite Stage 1의 역사적 설계 기록
│   ├── prime/
│   │   ├── harness-authority-graph-validation-follow-up.md ← 권위·그래프 검증 후속 기록
│   │   └── outcome-preservation-patch-roadmap.md ← 결과 보존 설계 기록
│   └── tracking/
│       ├── status.md                 ← 검증된 현재 상태, 남은 목표, 미래 방향
│       ├── findings.md               ← 현재 해결되지 않은 재현 가능한 문제
│       └── decisions/
│           ├── index.md              ← 기술 결정 색인
│           ├── 0001-canonical-source-and-generated-packages.md ← 단일 정본과 생성 패키지
│           ├── 0002-git-local-execution.md ← Git 로컬 실행 경계
│           └── 0003-bash-3-2-compatibility.md ← Bash 3.2 호환성 보증
├── src/
│   └── AGENTS.md                     ← 공통 스킬 정본 경계
├── platform/
│   └── AGENTS.md                     ← Claude·Codex host 오버레이 경계
└── build/
    └── AGENTS.md                     ← 생성기와 릴리스 일관성 검증 경계
```

## 핵심 게이트

- 공통 동작은 `src/skills/`, 호스트 차이는 `platform/`에서만 직접 고친다. `claude/`와 `codex/plugin/`은 직접 편집하지 않고 `bash build/build.sh`로 재생성한다.
- 릴리스 버전은 README 두 제목, CHANGELOG 첫 항목, canonical·generated manifest 네 개가 하나의 값이어야 한다. 누락·중복·불일치는 빌드 실패다.
- 병합 전 빌드, tracked·untracked 생성물 드리프트, 전체 `unittest`, whitespace 검사를 모두 통과해야 한다.
- 활성 로컬 상태나 worktree를 추측으로 덮어쓰거나 destructive Git 복구를 실행하지 않는다. main 통합과 외부 게시도 명시적 승인 없이는 수행하지 않는다.

## 작업 전 확인

1. `docs/standards.md`, `docs/engineering-notes.md`, 변경 대상 모듈의 `AGENTS.md`를 읽는다.
2. Prime·Run·Set·Run TDD 의미를 바꾸기 전 `docs/business-rules.md`와 `src/AGENTS.md`를 읽고 관련 contract test를 찾는다.
3. 호스트 메타데이터나 권한을 바꾸기 전 `platform/AGENTS.md`와 `build/AGENTS.md`를 읽고 생성 결과의 차이를 확인한다.
4. 버전·CHANGELOG·README·manifest를 바꾸기 전 `docs/operations.md`, `build/AGENTS.md`, `tests/test_release_consistency.py`를 읽는다.
5. 로컬 상태 이전·복구·worktree 처리에 손대기 전 `docs/security.md`, `src/AGENTS.md`, `src/skills/run/SKILL.md`와 관련 `src/skills/run/references/`의 실패 경계를 확인한다.

## 문제 처리

활성 상태 또는 worktree 유실 가능성, destructive Git 동작, canonical/generated 의미 불일치, 서로 다른 릴리스 버전의 배포 가능성, 사용자 승인 없는 외부 게시, 비밀정보 노출은 즉시 사용자에게 보고하고 진행을 중단한다. 그 밖의 재현 가능한 미해결 문제는 `docs/tracking/findings.md`에 조건·영향 범위·현재 해결할 수 없는 이유를 함께 기록한다.
