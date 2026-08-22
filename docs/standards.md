# 개발 표준

## 제품 북극성 준수

- 모든 workflow·review·routing·state 변경은 `business-rules.md`의 Time to Trusted Change와 사용자 산출물 계약에 연결되어야 한다. 내부 단계 수나 mode 정확도만으로 순개선을 주장하지 않는다.
- 절차를 줄이는 변경은 safety·quality·user burden·recovery guardrail을 함께 검증한다. 절차를 추가하는 변경은 작은 작업의 wall-clock·token/tool cost·사용자 질문과 읽기 부담이 비열화되지 않음을 증명한다.
- Adaptive Assurance의 첫 live pilot은 strict Lite와 기존 Full Assurance의 binary topology만 허용한다. `standard`를 별도 live orchestration으로 추가하려면 독립적인 사용자 순효익과 rollback boundary를 별도 릴리스에서 증명해야 한다.
- 연구 protocol·worksheet·raw benchmark 자료는 live skill 또는 Prime이 기본으로 읽는 `docs/` context에 넣지 않는다. `docs/`에는 제품 계약과 짧은 현재 상태만 남기고 상세 연구 자료는 `research/`에 둔다.

## 정본과 생성물

- 공통 워크플로 의미는 `src/skills/`에서만 직접 수정한다. 호스트별 manifest, Claude frontmatter 입력, Codex `openai.yaml`은 `platform/`에서만 직접 수정한다.
- `claude/`와 `codex/plugin/`은 `bash build/build.sh`의 출력이다. 직접 편집한 generated diff는 허용되지 않으며, 정본 또는 오버레이를 고친 뒤 전체 build로 재생성해야 한다.
- `harness-format.md`의 Run↔Set 사본, `harness-review.md`의 Run↔Set 사본, `foundation-format.md`의 Run↔Prime 사본은 각각 byte-identical이어야 한다.

## 릴리스 일관성

- `README.md`, `README_KO.md`의 첫 유효 릴리스 제목, `CHANGELOG.md`의 첫 version entry, Claude·Codex canonical manifest와 generated manifest의 top-level version은 정확히 하나의 같은 값을 가져야 한다.
- 본문 예시의 version 문자열과 nested metadata는 릴리스 label로 세지 않는다. label 누락, 하나의 표면에 둘 이상의 label, 표면 간 불일치는 모두 build 실패다.
- Codex command metadata는 사용자 호출형 스킬에 `policy.allow_implicit_invocation: false`를 유지한다. canonical과 generated 파일의 정책이 달라서는 안 된다.

## Build와 호환성

- `build/build.sh`는 Bash 3.2에서 실행 가능해야 한다. associative array 등 Bash 4+ 전용 문법을 도입하지 않는다.
- release version guard는 Git 명령 없이 동작해야 한다. source archive에서도 같은 검증을 수행할 수 있어야 한다.
- Bash 3.2 호환을 계속 주장하는 build 변경은 `bash --version`이 3.2인 실제 환경에서 build와 focused release test가 통과한 증거를 요구한다. 최신 Bash의 성공이나 정적 검토로 대체하지 않는다.

## 테스트와 병합 게이트

다음 순서를 모두 통과하지 않은 commit은 병합 후보가 아니다.

```text
bash build/build.sh
git diff --exit-code -- claude codex
test -z "$(git status --porcelain --untracked-files=all -- claude codex)"
python -m unittest discover -s tests -v
git diff --check
```

행동·복구·스케줄링·외부 인터페이스 계약을 바꾸면 해당 실패를 재현하는 가장 작은 contract test를 추가한다. 테스트를 통과시키기 위해 기존 assertion, mutation, 실패 경로를 삭제하거나 완화하지 않는다. 새 dependency는 현재 표준 라이브러리 기반 검증으로 해결할 수 없는 필요가 증명되지 않으면 추가하지 않는다.

성능·사용자 부담 개선을 주장하는 변경은 동일 repository snapshot·prompt·host/model/settings의 paired baseline을 사용하고, 측정 전에 cohort와 non-inferiority 또는 improvement margin을 고정한다. 결과를 본 뒤 기준을 바꾸거나 서로 다른 revision의 측정을 합치지 않는다.

## Git과 게시

기존 프로젝트 변경은 feature branch에 유지한다. branch 또는 worktree를 삭제하기 전에 대상 commit이 보존 대상 branch의 ancestor인지 확인한다. reset, force push, history rewrite, main 통합, tag, GitHub Release, PR 생성·merge는 사용자의 명시적 승인과 범위 확인 없이는 실행하지 않는다.

## 문서와 표현

CHANGELOG와 README는 실제 구현·검증된 결과만 주장한다. token, latency, footprint, host behavior 개선은 그 측정 또는 행동 검증이 존재할 때만 기록한다. 역사적 roadmap은 당시 결정과 검증 기록으로 유지하고 현재 릴리스 계약처럼 재해석하지 않는다.

`GO_TO_PHASE_2_DESIGN_REVIEW`는 설계 검토 진입 권한이지 Lite activation, merge, release 또는 성능 개선 증명이 아니다. 실제 pilot 전에는 예상 절감으로, pilot 후에는 측정된 end-to-end Time to Trusted Change로 구분해 표현한다.
