# 0003 — Bash 3.2 호환성 증거

## 배경

설치 패키지 생성기는 Bash script이며 오래된 Bash 환경에서도 동작한다고 표방한다. 최신 CI의 Bash만 통과하면 associative array 같은 Bash 4+ 문법이나 오래된 shell에서만 드러나는 문제가 릴리스 뒤에 발견될 수 있다.

## 결정

Bash 3.2 지원을 표방하는 동안 build 관련 변경은 실제 `bash --version` major.minor 3.2 환경에서 검증한다. 같은 PATH에서 build와 focused release-consistency test가 모두 exit 0이어야 하며, 이후 generated drift가 없어야 한다.

## 대안

- **정적 shell 검토와 최신 Bash CI만 사용:** 운영 비용은 낮지만 실제 3.2 parser·runtime 차이를 증명하지 못한다.
- **최소 지원 version을 Bash 4+로 올림:** 구현 자유도는 커지지만 기존 호환성 약속을 제거하고 설치 요구사항을 바꾸는 별도 제품 결정이 필요하다.

## 결과

Build script는 Bash 4+ 전용 문법을 사용할 수 없다. 검증 runner는 Bash뿐 아니라 build가 요구하는 Python과 Perl도 제공해야 한다. Bash 3.2 실행기를 확보하지 못하거나 실제 명령이 실패하면 release gate는 통과할 수 없다.
