# 엔지니어링 노트

## 생성 도중 실패하면 패키지가 부분 상태가 된다

- **증상:** build가 중간에 실패한 뒤 `claude/` 또는 `codex/` 아래에 삭제·수정된 파일이 대량으로 보인다.
- **원인:** 생성기는 기존 패키지 디렉터리를 먼저 지우고 정본을 복사한 뒤 frontmatter 주입과 일관성 검사를 수행한다. `perl` 같은 실행 의존성이 없으면 삭제 이후 단계에서 멈출 수 있다.
- **대응:** 누락된 runner 의존성을 해결한 뒤 `bash build/build.sh` 전체를 다시 실행한다. 개별 generated 파일을 checkout하거나 손으로 편집하지 않는다. 이후 tracked diff와 untracked output이 모두 비어 있는지 확인한다.

## Bash만 있어서는 release build가 충분하지 않다

- **증상:** 최소 Bash 컨테이너에서 `build/build.sh: perl: command not found`로 exit 127이 발생한다.
- **원인:** Claude frontmatter 주입, 개행 정규화, release label 추출이 Perl을 사용한다.
- **대응:** Bash 3.2 호환성 검증 runner에도 Python과 Perl을 함께 제공한다. 같은 PATH에서 `bash --version`, build, focused release test를 차례로 실행하고 각 exit code를 보존한다.

## Claude와 Codex 패키지의 차이는 비대칭이 아니라 의도된 주입이다

- **증상:** Claude의 `SKILL.md`가 정본과 byte-identical하지 않지만 Codex의 Markdown은 정본과 같다.
- **원인:** Claude는 `disable-model-invocation`과 skill별 `allowed-tools`를 frontmatter에 build-time으로 주입하고, Codex는 `agents/openai.yaml` 오버레이로 인터페이스와 호출 정책을 추가한다.
- **대응:** 공통 본문 의미를 비교할 때 Claude의 주입된 frontmatter를 분리해 판단한다. Codex Markdown drift 또는 Claude 본문 drift는 build/source 문제로 취급하고 전체 재생성으로 확인한다.

## tracked diff만으로는 generated parity를 증명할 수 없다

- **증상:** `git diff --exit-code -- claude codex`가 성공하지만 build가 새 untracked 파일을 남긴다.
- **원인:** `git diff`는 아직 추적되지 않은 파일을 보고하지 않는다.
- **대응:** tracked diff 직후 `git status --porcelain --untracked-files=all -- claude codex`의 출력이 빈 값인지 별도로 확인한다. CI에서도 두 검사를 합치지 않고 순서대로 유지한다.

## Release label parser는 아무 version 문자열이나 세지 않는다

- **증상:** 문서 본문이나 manifest의 nested metadata에 다른 version 예시가 있어도 build가 실패하지 않는다.
- **원인:** README는 첫 유효 heading, CHANGELOG는 제목 뒤 첫 version entry, JSON manifest는 top-level `version`만 릴리스 label로 해석한다.
- **대응:** 릴리스 버전을 바꿀 때 정확한 label만 수정하고, missing·ambiguous·mismatch mutation을 포함한 focused test를 실행한다. parser 범위를 넓혀 본문 예시를 릴리스 값으로 취급하지 않는다.

## 공유 reference는 물리적 사본이지만 하나의 계약이다

- **증상:** 한 skill의 shared reference만 수정하면 build가 reference drift로 실패한다.
- **원인:** 각 skill은 자기 `references/`만 패키징하므로 공통 계약도 물리적 사본을 유지한다.
- **대응:** Run↔Set의 harness format/review, Run↔Prime의 foundation format을 같은 변경에서 함께 수정하고 byte parity를 build로 확인한다.
