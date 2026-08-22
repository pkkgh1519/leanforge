# 프로젝트 상태

## 제품 북극성

Leanforge의 1차 성과는 최소한의 사용자 노력으로 완성된 신뢰 가능한 변경이다. 핵심 지표는 **Time to Trusted Change**이며, wall-clock뿐 아니라 사용자 질문·읽기·승인 부담, agent 실행 비용, 재작업, 품질과 안전을 함께 본다.

사용자가 받아야 할 산출물은 검증된 실제 변경, 신뢰 증거와 잔여 위험 요약, 승인 가능한 의도 계약, 통합 선택, 그리고 실제로 변경된 durable project knowledge다. 3-doc·reviewer·worktree·mode·sidecar는 이를 위한 내부 수단이다.

## 검증된 현재 상태

- **v1.9.0 semantic contract foundation:** 기존 monolithic Run orchestration을 유지하면서 route topology, external proof, failure precedence, completion reuse, concern disposition, lifecycle·review ownership, user output 의미를 작은 machine-readable kernel과 stable protected Markdown block으로 결속했다.
- **Instruction load graph:** Run의 instruction path와 activation edge를 별도 graph로 정의하고 route·overlay·phase·profile별 transitive closure를 하나의 deterministic activation path로 검증한다.
- **독립 검증 기반:** hand-authored scenario, known-opposite mutation, canonical·generated skill surface의 exact raw-byte baseline으로 semantic kernel과 load closure를 독립 검증한다.
- **Adaptive Assurance shadow foundation:** Prime은 ELICIT exit에서 Lite·Standard·Assurance advisory prediction을 `.leanforge/assurance-shadow.json`에 기록한다. 이 snapshot은 실행 권위가 없고 Full Assurance 흐름을 바꾸지 않는다.
- **Shadow observation integrity:** sidecar는 현재 Prime cycle의 교체 가능한 ELICIT-exit prediction으로 한정된다. 새 record가 완성되지 않으면 이전 snapshot을 현재 결과로 남기지 않으며, closed Lite fact partition과 `unknown_material_risk` fail-closed 경계를 검증한다.
- **Pilot-readiness study contract:** 고정된 router revision과 사전 등록 cohort에서 safety observation, installed-host behavior smoke, paired A/B shadow-tax benchmark, blinded 3-doc quality, 사용자 부담, 보수적 잠재 절감을 함께 평가한다. 완료 record와 raw benchmark log는 공개 저장소에 커밋하지 않는다.
- **Release consistency guard:** build가 Git 없이 일곱 release surface의 정확한 label을 읽고 missing·ambiguous·mismatch를 거부한다. Baseline, 본문 예시 제외, 각 mutation을 focused test로 검증했다.
- **명시적 Run TDD 호출:** Codex canonical/generated metadata에 implicit invocation 금지가 일치한다.
- **Generated parity CI:** build 뒤 tracked drift, untracked output, 전체 unittest, whitespace를 순서대로 차단한다.

## Adaptive Assurance의 고정 경계

- 사용자는 mode를 선택하지 않고 mode 판단을 위한 추가 질문을 받지 않는다.
- shadow 분류는 기존에 grounded된 사실만 사용하며 추가 repo scan이나 subagent를 만들지 않는다.
- 첫 live pilot은 strict Lite와 기존 Full Assurance 두 실행 경로만 갖는다.
- `standard`는 관측 label이며 별도 live orchestration이 아니다.
- 새 위험이나 불확실성이 생기면 기존 Full Assurance로 단조 복귀한다.

## 남은 확정 목표

1. **Phase 1.2 safety observation:** 한 pinned revision에서 최소 35개의 usable real observation을 수집한다. Shadow Lite 15건 이상, Standard 10건 이상, Assurance 10건 이상을 포함하고 모든 underclassification을 개별 처분한다.
2. **Installed-host behavior smoke:** proposed host scope에서 최소 20회 수행한다. 두 host가 범위라면 Claude Code 10회 이상과 Codex 10회 이상을 포함하며 classification-only 질문·subagent·mode choice·live behavior 변화가 0인지 확인한다.
3. **Paired A/B shadow-tax benchmark:** pre-shadow base `2d2be39c01c9d19819acb0c658f07d06b06931a7`와 pinned candidate를 동일 case·host·model/settings에서 비교한다. 두 host 기준 5 case × 2 version × 5 repetition으로 100회를 수행하고 median time-to-G7 +5%, p90 +10% 비열화 한계를 적용한다.
4. **Quality·사용자 부담 gate:** blinded 3-doc review에서 intent completeness·graph·coverage·blocker rate가 악화되지 않고, mode 때문에 질문·reply turn·approval step·읽기 부담이 늘지 않아야 한다.
5. **Potential-value gate:** 보수적인 removable-ceremony 추정치가 측정된 median shadow tax의 2배 이상이어야 한다. 이는 Phase 2 설계 가치를 판단하는 buffer이며 실제 Lite 성능 주장이 아니다.
6. **Phase 2 design review:** 위 다섯 gate와 binary fallback이 모두 통과할 때만 별도 reviewed release 설계로 이동한다. Phase 1.2 결과는 activation 권위가 아니다.
7. **v1.9.1 block-preserving split:** v1.9.0 계약을 기준으로 core·worktree·parallel·external·failure overlay를 분리한다. Adaptive Assurance activation과 같은 릴리스에 묶지 않으며 독립적인 의미·load closure·행동 review를 통과해야 한다.

각 목표는 현재 구현을 자동 승인하지 않는다. Lite activation과 block-preserving split은 각각 독립된 사용자 승인과 release review를 요구한다.

## 연구 산출물

상세 연구 문서는 Prime의 기본 `docs/` context 밖에 둔다.

- `research/adaptive-assurance/pilot-readiness-study.md`
- `research/adaptive-assurance/observation-template.md`
- `research/adaptive-assurance/pilot-readiness-report-template.md`

최종 보고서 판정은 `GO_TO_PHASE_2_DESIGN_REVIEW` 또는 `NO_GO`다. GO도 실제 Lite activation을 승인하지 않는다.

## 미래 방향

- Phase 2 bounded pilot이 별도 승인되면 실제 end-to-end Time to Trusted Change를 기존 Full Assurance와 비교한다.
- 실제 Claude Code·Codex host에서 behavior smoke와 paired benchmark로 deterministic contract 밖의 host 비용과 동작을 관찰한다.
- Token·latency 개선은 위 반복 측정이 존재할 때만 주장한다. 분류 정확도나 synthetic fixture는 순효익 증거를 대체하지 않는다.

## 차단 사항

현재 Full Assurance 제품 흐름에 확인된 blocker는 없다. Lite activation gate는 safety, shadow-tax, quality, user burden, potential value, binary reversibility가 모두 통과하고 별도 reviewed release가 승인될 때까지 의도적으로 닫혀 있다.
