# 0004 — Run orchestration의 정본 블록과 호환 monolith를 분리한다

## 배경

검증된 Full Assurance 기준점 `e5b3cbc4778be190bd2c3c4477450e8f3c34e0cb`에서 Run은
`src/skills/run/references/orchestration.md` 하나를 startup에 강제 로드한다. 이 파일은 scheduling,
dispatch, worktree, review, failure와 recovery 규칙을 함께 담아 향후 Strict Lite가 필요하지 않은
instruction만 선택적으로 읽기 어렵다. 그러나 과거 조건부 split처럼 파일 분리와 load activation을
같은 변경에 묶으면 어떤 규칙을 언제 읽는지가 달라져 Full 행동 보존을 증명하기 어렵다.

## 결정

v1.9.1의 첫 단계는 ordered source blocks만 도입한다.

- `src/instruction-blocks/run/orchestration/`의 닫힌 manifest와 9개 ordered Markdown block을
  authoring authority로 둔다.
- `tools/run_orchestration_blocks.py sync`가 block bytes를 순서대로 이어 기존
  `src/skills/run/references/orchestration.md`를 명시적으로 materialize한다.
- `build/build.sh`는 materialized monolith를 자동 수리하지 않고 build 전에 검증한다.
- 현재 `run/SKILL.md`, `load-graph.json`, `semantic-contract.json`, packaged Run tree와 load phase는
  `e5b3cbc…` 기준과 byte-identical하게 유지한다.
- baseline commit, tree, orchestration blob, runtime surface hash는 manifest와 verifier 코드에
  이중 고정한다. block, manifest와 monolith를 함께 바꿔도 이번 release gate를 우회할 수 없다.

## 비목표

이번 결정은 다음을 활성화하지 않는다.

- Strict Lite routing 또는 사용자 선택 mode
- conditional block loading
- reviewer, worktree, verification, harness sync 또는 recovery 생략
- Run route topology, semantic event 또는 user output 변경
- plugin package에 source block 포함

실제 load edge 전환은 이 split이 독립적으로 병합되고 installed-host Full replay가 통과한 뒤 별도
reviewed release에서만 검토한다.

## 검증과 실패 기준

병합 후보는 다음을 모두 만족해야 한다.

1. ordered blocks의 concat이 `e5b3cbc…` orchestration Git blob 36,790 bytes와 exact match다.
2. canonical, Claude, Codex의 전체 packaged Run surface가 기준점과 byte-identical하다.
3. 기존 load graph와 semantic contract가 같은 blob과 activation phase를 유지한다.
4. missing, reordered, duplicated, CRLF, byte drift, manifest rewrite, monolith drift와 runtime drift
   mutation이 fail-closed다.
5. Linux와 Windows에서 build, generated parity, 전체 contract suite와 whitespace 검사가 통과한다.
6. exact candidate를 설치한 Full replay가 Golden Run과 decision-ownership 결과를 보존한다.

하나라도 실패하면 source block patch 전체를 revert한다. 기존 monolith와 `e5b3cbc…`가 rollback
boundary이며 부분적인 conditional load 전환은 남기지 않는다.

## 결과

이 단계의 이익은 행동 최적화가 아니라 다음 release가 선택할 수 있는 검증 가능한 source 경계를
만드는 것이다. Full runtime은 같은 한 권을 계속 읽지만, 편집 정본은 페이지별로 봉인된 상태가 된다.
경제성 주장은 후속 installed-host paired experiment 전에는 하지 않는다.
