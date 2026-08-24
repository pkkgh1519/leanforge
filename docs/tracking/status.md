# 프로젝트 상태

## 제품 북극성

Leanforge의 1차 성과는 최소한의 사용자 노력으로 완성된 신뢰 가능한 변경이다. 핵심 지표는 **Time to Trusted Change**이며, wall-clock뿐 아니라 사용자 질문·읽기·승인 부담, agent 실행 비용, 재작업, 품질과 안전을 함께 본다.

사용자가 받아야 할 산출물은 검증된 실제 변경, 신뢰 증거와 잔여 위험 요약, 승인 가능한 의도 계약, 통합 선택, 그리고 실제로 변경된 durable project knowledge다. 3-doc·reviewer·worktree·mode·sidecar는 이를 위한 내부 수단이다.

## 검증된 현재 상태

- **v1.9.0 semantic contract foundation:** 기존 monolithic Run orchestration을 유지하면서 route topology, external proof, failure precedence, completion reuse, concern disposition, lifecycle·review ownership, user output 의미를 작은 machine-readable kernel과 stable protected Markdown block으로 결속했다.
- **Instruction load graph:** Run의 instruction path와 activation edge를 별도 graph로 정의하고 route·overlay·phase·profile별 transitive closure를 deterministic activation path로 검증한다.
- **독립 검증 기반:** hand-authored scenario, known-opposite mutation, canonical·generated skill surface의 exact raw-byte baseline으로 semantic kernel과 load closure를 검증한다.
- **Adaptive Assurance shadow foundation:** Prime은 ELICIT exit에서 advisory prediction을 기록하지만 Full Assurance 흐름을 바꾸지 않는다.
- **Shadow observation integrity:** sidecar freshness, closed Lite fact partition, `unknown_material_risk` fail-closed 경계를 검증한다.
- **Pilot-readiness study contract:** pinned source·contract·generated/installed package identity, blinded safety observation, removable-gate intervention, installed-host smoke, paired A/B shadow tax, predeclared quality, user burden, prevalence-weighted value를 함께 평가한다.
- **Generated parity CI:** build 뒤 tracked drift, untracked output, 전체 unittest, whitespace를 순서대로 차단한다.
- **사용자 결과 표면:** marketplace·skill discovery·온보딩·Run 최종 보고를 검증된 변경, 증거, 남은 위험, 사용자 소유 통합 선택에 맞췄다. `leanforge.product-outcome.minimum-v1`의 고정 7개 검사에서 기존 표면은 1/7, 후보 표면은 7/7을 기록했고, 3-doc 우선 문구·남은 위험 누락·generated drift·검증 누락·무측정 속도 주장을 넣은 known-opposite mutation은 모두 거부된다. 이 결과는 정적 제품 계약과 완료 예시의 정합성만 증명하며 installed-host 실행이나 Time to Trusted Change 개선은 증명하지 않는다.

## Adaptive Assurance의 고정 경계

- 사용자는 mode를 선택하지 않고 mode 판단을 위한 추가 질문을 받지 않는다.
- shadow 분류는 기존에 grounded된 사실만 사용하며 추가 repo scan이나 subagent를 만들지 않는다.
- 첫 live pilot은 strict Lite와 기존 Full Assurance 두 실행 경로만 갖는다.
- `standard`는 관측 label이며 별도 live orchestration이 아니다.
- 새 위험이나 불확실성이 생기면 기존 Full Assurance로 단조 복귀한다.

## 남은 확정 목표

1. **Safety observation:** 최소 35개의 usable real observation을 수집한다. Shadow Lite 15건은 모두 Run completion 또는 Run terminal blocker까지 도달해야 하며, later escalation을 적용한 Lite-to-Standard와 Lite-to-Assurance wrong-path가 모두 해결되어야 한다.
2. **Removable-gate safety:** strict-Lite 결과가 Prime reviewer, worktree/wave gate, final reviewer, harness sync 등 생략 후보 gate의 safety-relevant intervention에 의존한 사례가 0이어야 한다.
3. **Installed identity and host floors:** installed package digest가 pinned generated package와 같아야 한다. 두 host pilot이면 host별 usable 15건, Lite 5건, Standard 3건, Assurance 3건 이상을 확보한다.
4. **Installed-host behavior smoke:** proposed host scope에서 최소 20회 수행한다. 두 host가 범위라면 Claude Code 10회 이상과 Codex 10회 이상을 포함한다.
5. **Paired A/B shadow-tax benchmark:** 같은 pinned candidate tree에서 live shadow hook만 제거한 control A와 candidate B를 별도로 hash-pin하고, allowlisted hook diff 외에는 동일함을 확인한다. 5 case × 2 host × 2 version × 5 repetition으로 100회를 수행하며, 양쪽이 G7에 도달한 matched pair만 latency에 사용하고 host별 median +5%, p90 +10%, B-only stop 0을 적용한다.
6. **Quality·사용자 부담 gate:** host별 blinded score와 critical defect, blocker rate, 질문·reply turn·approval step·summary size가 사전 고정된 non-inferiority margin을 통과해야 한다.
7. **Potential-value gate:** 공통 단위는 wall-clock seconds다. 모든 enrolled cycle에 대해 nonqualifying case의 benefit을 0으로 두고 conservative removable seconds를 합산한 뒤 enrolled count로 나눈다. 이 weighted benefit이 같은 denominator의 shadow tax와 promotion/recovery cost 합계의 2배 이상이며 net seconds/cycle이 양수여야 한다.
8. **Phase 2 design review:** 위 gate가 proposed host마다 독립적으로 통과할 때만 별도 reviewed release 설계로 이동한다. Phase 1.2 결과는 activation 권위가 아니다.
9. **v1.9.1 block-preserving split:** Adaptive Assurance activation과 같은 릴리스에 묶지 않고 독립적인 의미·load closure·행동 review를 통과한다.

## 연구 산출물

상세 연구 문서는 Prime의 기본 `docs/` context 밖에 둔다.

- `research/adaptive-assurance/pilot-readiness-study.md`
- `research/adaptive-assurance/observation-template.md`
- `research/adaptive-assurance/pilot-readiness-report-template.md`
- `research/product-outcome/minimum-experiment.md`

제품 결과 정적 실험의 다음 단계는 설치된 Claude Code·Codex에서 prompt→captured run→checks 흐름을 재현하고 TTTC·질문 수·읽기 부담·재작업·critical defect를 동일한 paired population으로 측정하는 것이다. Adaptive Assurance 최종 판정은 `GO_TO_PHASE_2_DESIGN_REVIEW` 또는 `NO_GO`이며, GO도 Lite activation을 승인하지 않는다.

## 차단 사항

현재 Full Assurance 제품 흐름에 확인된 blocker는 없다. Lite activation은 wrong-path, removable-gate dependence, installed identity, per-host coverage, endpoint-safe shadow tax, quality, user burden, prevalence-weighted value, binary reversibility가 모두 통과하고 별도 reviewed release가 승인될 때까지 닫혀 있다.
