# 빌드와 릴리스 일관성

## 범위

`build/build.sh`는 materialized `src/skills/`와 `platform/` 입력에서 Claude·Codex 설치 패키지를 생성하고, `src/instruction-blocks/`의 Run orchestration reconstruction, release version 및 shared-reference parity를 검증한다. Workflow 의미, host metadata 내용, release note 문구 자체는 이 모듈의 소유가 아니다.

## 경계

- Generated directory의 단일 writer다. 기존 `claude/`와 `codex/`를 지운 뒤 전체를 재생성하므로 partial patch 방식으로 동작하게 바꾸지 않는다.
- Root marketplace manifest와 README는 build output이 아니다. Build는 읽거나 검증할 수 있지만 생성물로 덮어쓰지 않는다.
- Build는 Run orchestration monolith를 자동 sync하거나 수리하지 않는다. Author가 별도 sync를 실행한 뒤 build는 exact block reconstruction과 pinned Full runtime identity를 fail-closed로 검증한다.
- Release guard는 Git을 호출하지 않는다. Source archive에서도 같은 label 검증이 동작해야 한다.

## 불변조건

- Bash 3.2에서 parse·execute되어야 하며 Bash 4+ 전용 기능을 사용하지 않는다.
- README 두 제목, CHANGELOG 첫 entry, canonical/generated manifest 네 개에서 각각 정확히 하나의 release label을 얻고 모든 값이 같아야 한다.
- README 본문 예시와 JSON nested version은 release label이 아니다.
- Run↔Set shared reference 두 쌍과 Run↔Prime shared reference 한 쌍의 bytes가 같아야 한다.
- Ordered orchestration blocks, closed manifest와 materialized monolith는 검증된 Full baseline bytes를 정확히 재구성해야 한다. Manifest와 output을 함께 바꿔 baseline pin을 우회할 수 없어야 한다.
- Claude frontmatter injection은 skill별 허용 도구를 유지하고, Codex overlay copy는 `agents/openai.yaml`을 canonical skill tree에 합친다.

## 구현 패턴

Bash 3.2가 지원하는 indexed array, `case`, POSIX 도구와 Perl을 사용한다. 실패 메시지는 missing, ambiguous, mismatch, shared-reference drift를 구분하고 non-zero로 종료한다. 임시 runner를 만들 때 Bash, Python 3.10 이상과 Perl을 같은 PATH에 제공한다.

## 테스트

Build 변경은 먼저 `tests/test_release_consistency.py`의 baseline·missing·ambiguous·mismatch mutation으로 실패를 재현한다. Orchestration source 변경은 stale monolith를 build가 자동 복구하지 않는 mutation과 `tests/test_run_orchestration_blocks.py`의 exact reconstruction·identity rewrite mutation을 포함한다. 이후 build, focused test, tracked/untracked generated drift, 전체 unittest, whitespace 검사를 실행한다. 호환성 관련 변경은 실제 Bash 3.2에서 version, build, focused test의 exit code 0을 별도로 증명한다.
