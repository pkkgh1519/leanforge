# 운영 절차

## 사용자 설치

필수 조건은 PATH에서 실행 가능한 Git, Claude Code 또는 Codex, 그리고 설치 후 사용할 Git 저장소 workspace다. 먼저 터미널에서 Git을 확인한다.

```text
git --version
```

Claude Code를 사용하면 Claude Code의 command 입력창에서 다음 순서로 실행한다.

```text
/plugin marketplace add pkkgh1519/leanforge
/plugin install leanforge
```

Codex를 사용하면 터미널에서 다음 순서로 실행한다.

```text
codex plugin marketplace add pkkgh1519/leanforge
codex plugin add leanforge@leanforge
```

설치 후 Git 저장소 workspace에서 command palette를 열어 Prime, Run, Set, Run TDD 네 command가 보이는지 확인한다.

## 기여자 준비

Git, Bash, Python, Perl이 PATH에 있어야 한다. CI 기준 Python은 3.12이며 테스트는 Python 표준 라이브러리 `unittest`만 사용하므로 별도 package 설치는 필요 없다. 새 checkout은 다음 순서로 준비한다.

```text
git clone https://github.com/pkkgh1519/leanforge.git
cd leanforge
git switch -c <branch-name>
git --version
bash --version
python --version
perl -e 'print "$^V\n"'
bash build/build.sh
python -m unittest discover -s tests -v
git diff --check
```

Build가 먼저인 이유는 테스트와 설치 패키지가 정본에서 재생성된 같은 상태를 검사해야 하기 때문이다.

## 변경 검증

공통 스킬 또는 host overlay 변경 뒤에는 다음 명령을 그대로 실행한다.

```text
bash build/build.sh
git diff --exit-code -- claude codex
test -z "$(git status --porcelain --untracked-files=all -- claude codex)"
python -m unittest discover -s tests -v
git diff --check
```

의도한 generated 변경을 아직 commit하지 않은 작업 단계에서는 첫 diff가 변경을 보여줄 수 있다. 해당 변경을 정확한 경로로 commit한 뒤 같은 명령을 다시 실행해 clean 상태를 증명한다. 반복 build 재현성이 중요한 변경은 generated tree의 hash를 build 전후로 비교하거나 두 번째 build 뒤 Git 상태가 비어 있는지 확인한다.

## 릴리스 준비

1. README 두 릴리스 제목, CHANGELOG 첫 entry, Claude·Codex canonical manifest version을 같은 값으로 수정한다.
2. 필요한 host metadata는 `platform/`에서 수정한다.
3. `bash build/build.sh`로 두 generated package를 다시 만든다.
4. `python -m unittest tests.test_release_consistency -v`로 release label, invocation policy, CI ordering mutation을 확인한다.
5. 전체 test와 generated tracked·untracked drift, whitespace를 확인한다.
6. Bash 3.2 호환을 주장하는 build 변경이면 실제 Bash 3.2 환경의 같은 PATH에서 version, build, focused test의 stdout/stderr와 exit code를 보존한다.
7. branch diff와 CHANGELOG 표현이 실제 변경 범위를 넘지 않는지 검토한다.

## Bash 3.2 검증 환경

검증 환경은 `bash --version`의 major.minor가 3.2여야 하고, 같은 container 또는 machine의 PATH에서 Python과 Perl을 사용할 수 있어야 한다. 최소 Bash image만으로는 build가 완료되지 않는다. 먼저 runner에서 다음 세 도구를 확인한 뒤 실제 명령을 실행한다.

```text
bash --version
python --version
perl -e 'print "$^V\n"'
bash build/build.sh
python -m unittest tests.test_release_consistency -v
```

최신 Bash의 성공 결과는 이 호환성 증거를 대체하지 않는다.

## 게시와 배포

Generated package는 저장소에 commit되지만 tag, GitHub Release, marketplace 변경, PR/push/merge는 자동 릴리스 단계가 아니다. 사용자가 승인한 branch와 범위를 다시 확인한 뒤 수행한다. 원격 게시 후에는 remote commit, CI 결과, tag/Release가 의도한 commit을 가리키는지 authoritative readback으로 확인한다.
