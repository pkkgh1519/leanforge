# Host overlays

## 범위

`platform/`은 Claude Code와 Codex가 설치 패키지를 읽기 위해 필요한 host별 manifest, license, interface metadata를 소유한다. 공통 workflow 본문과 generated package는 이 모듈의 소유가 아니다.

## 경계

- Claude 쪽은 plugin manifest와 license를 소유한다. Skill별 `allowed-tools`와 `disable-model-invocation` 주입 로직은 build가 소유하므로 이 디렉터리에 공통 본문 사본을 만들지 않는다.
- Codex 쪽은 plugin manifest, skill별 `agents/openai.yaml`, license를 소유한다. 공통 `SKILL.md`를 이 디렉터리에서 포크하지 않는다.
- `claude/`와 `codex/plugin/`을 직접 수정하지 않는다. Overlay 변경 뒤 build가 generated counterpart를 쓰게 한다.

## 불변조건

- 두 manifest의 product identity, version, repository/license 의미는 같은 release를 가리켜야 한다.
- Codex의 Prime, Run, Set, Run TDD metadata는 명시적 사용자 호출을 요구하며 `policy.allow_implicit_invocation: false`를 정확히 한 번 유지한다.
- Host 차이는 interface·권한·packaging 요구에 한정한다. Prime/Run/Set/Run TDD의 공통 행동 의미가 host마다 달라져서는 안 된다.

## 테스트

Overlay 변경 뒤 build를 실행하고 canonical/generated manifest 및 `openai.yaml` parity를 확인한다. `tests/test_release_consistency.py`의 invocation·version 검증과 전체 contract suite를 실행한다. Host metadata 변경이 generated package 밖의 공통 스킬 diff를 만들면 경계 위반이다.
