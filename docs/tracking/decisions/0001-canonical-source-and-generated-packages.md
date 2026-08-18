# 0001 — 공통 정본과 생성 패키지 분리

## 배경

Claude Code와 Codex는 같은 워크플로 의미를 사용하지만 manifest, frontmatter, interface metadata 형식이 다르다. 각 설치 패키지를 독립적으로 편집하면 공통 규칙의 한쪽만 고쳐지는 drift가 발생하고 어느 사본이 정본인지 판단할 수 없게 된다.

## 결정

공통 스킬과 reference는 `src/skills/`를 단일 정본으로 둔다. Host 차이는 `platform/claude/`와 `platform/codex/` 입력에 한정하고, `build/build.sh`만 `claude/`와 `codex/plugin/`을 쓴다. Generated package는 commit하지만 직접 편집하지 않는다.

## 대안

- **두 패키지를 각각 정본으로 유지:** host별 변경은 단순하지만 공통 의미 변경을 매번 두 번 적용해야 하고 silent drift를 막기 어렵다.
- **Runtime에 하나의 공통 package를 해석:** 생성 drift는 줄지만 두 host의 manifest·권한·metadata 형식을 runtime adapter가 떠안아 설치 경계를 복잡하게 만든다.

## 결과

공통 의미 변경은 정본 한 곳에서 시작하며 build와 parity test가 두 배포면을 검증한다. Build 없이 generated package만 고친 변경은 허용되지 않는다. Host별로 공통 본문을 다르게 발전시키는 선택은 불가능하며, 필요한 차이는 명시적 overlay 또는 build-time injection으로 표현해야 한다.
