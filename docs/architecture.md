# 아키텍처

## 구성과 의존 방향

플러그인의 실행 계약은 Markdown 스킬과 참조 문서로 구성된다. 공통 의미는 `src/skills/`가 소유하고, `platform/claude/`와 `platform/codex/`는 호스트가 요구하는 manifest·메타데이터·권한 차이만 추가한다. `build/build.sh`는 이 두 입력을 소비해 설치 가능한 `claude/`와 `codex/plugin/` 패키지를 만든다. 생성 패키지는 정본을 향해 역으로 의존하지 않으며, 생성 패키지의 변경이 정본으로 복사되는 흐름은 허용되지 않는다.

```text
사용자 요청
  → 호스트가 설치 패키지의 Prime | Run | Set | Run TDD를 호출
  → 공통 스킬 계약이 입력·Git 사실·검증 결과를 처리
  → 필요한 로컬 Git 변경과 검증 증거를 사용자에게 반환

src/skills ─┐
            ├─ build/build.sh ─→ claude
platform/claude ┘

src/skills ─┐
            ├─ build/build.sh ─→ codex/plugin
platform/codex ┘
```

Claude 패키지는 공통 `SKILL.md` 본문에 Claude 전용 `disable-model-invocation`과 `allowed-tools` frontmatter를 빌드 시 주입한다. Codex 패키지는 공통 스킬을 복사한 뒤 `agents/openai.yaml` 오버레이를 합친다. 이 차이를 제외한 공통 워크플로 의미는 두 패키지에서 같아야 한다.

## 제품 구성 요소

| 구성 요소 | 역할 | 허용된 의존 방향 |
|---|---|---|
| Prime | 목표·문서·메모를 검토 가능한 승인 계약으로 정제 | 저장소 증거와 사용자 결정 → 실행 계약 |
| Run | 승인 계약과 Git 상태를 소비해 격리 실행·검증·통합 후보를 생성 | 승인 계약 → Git 작업·테스트·리뷰 증거 |
| Set | 기존 프로젝트의 지속 가능한 운영 문맥을 생성 | 기존 코드·문서·사용자 결정 → 프로젝트 문서 |
| Run TDD | Run 위에 행동 변경용 선택적 TDD 규율을 추가 | Run 계약 → 행동 단위 RED·GREEN·리팩터 검증 |
| build | 정본과 호스트 오버레이를 두 설치 패키지로 변환 | `src/skills` + `platform` → generated packages |
| contract tests | 워크플로·복구·배포면 불변조건을 실행 가능한 예로 고정 | source + generated + CI/build 계약 → pass/fail |

## 대표 흐름

Prime은 사용자의 입력을 그대로 권위로 채택하지 않고 저장소 사실과 대조한다. 사용자가 중요한 결정을 승인하면 Run이 실행 가능한 계약을 소비한다. Run은 작업 의존성과 위험도에 따라 직접 실행 또는 격리된 worktree 실행을 선택하고, 명령·출력·exit code가 확보되지 않은 결과는 완료로 승격하지 않는다. 작업이 끝나면 설치 패키지 생성이나 프로젝트별 검증을 실행하고, main 통합이나 외부 게시 전에는 사용자 결정을 기다린다.

## 배포 경계

루트 marketplace manifest는 설치 패키지의 위치를 가리키는 저장소 파일이며 build output이 아니다. 설치 가능한 실제 내용은 committed generated package에 있다. GitHub Actions는 정본에서 패키지를 다시 만든 뒤 tracked drift와 untracked output을 모두 검사하므로, 빌드가 재현되지 않는 commit은 배포 후보가 될 수 없다.
