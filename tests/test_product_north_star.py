import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUSINESS = ROOT / "docs/business-rules.md"
ARCHITECTURE = ROOT / "docs/architecture.md"
CONTRACTS = ROOT / "docs/contracts.md"
STANDARDS = ROOT / "docs/standards.md"
PHASE1 = ROOT / "docs/adaptive-assurance-phase1.md"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class ProductNorthStarContractTests(unittest.TestCase):
    def assert_terms(self, body: str, terms: tuple[str, ...], context: str) -> None:
        missing = [term for term in terms if " ".join(term.split()) not in body]
        self.assertFalse(missing, f"missing {context}: {missing}")

    def test_business_rules_define_authoritative_user_outcome(self):
        body = normalized(BUSINESS)
        self.assert_terms(
            body,
            (
                "제품 북극성 — 최상위 권위",
                "최소한의 사용자 노력으로 신뢰 가능한 변경을 완성",
                "Time to Trusted Change",
                "wall-clock뿐 아니라 사용자 개입 시간·질문 수·읽기 부담·agent 실행 비용·재작업",
                "하위 mechanism 문서가 이 절과 충돌하면 이 절이 우선한다.",
            ),
            "authoritative product outcome",
        )

    def test_user_artifacts_are_results_not_workflow_plumbing(self):
        body = normalized(BUSINESS)
        self.assert_terms(
            body,
            (
                "검증된 실제 변경",
                "신뢰 증거와 잔여 위험 요약",
                "승인 가능한 의도 계약",
                "통합 선택",
                "변경된 durable knowledge",
                "3-doc, reviewer, worktree, wave, mode label, shadow sidecar, load graph, semantic contract, fixture와 harness sync는 사용자 산출물이 아니라 내부 수단이다.",
            ),
            "user artifacts and internal mechanisms",
        )

    def test_product_guardrails_require_net_benefit(self):
        body = normalized(BUSINESS)
        self.assert_terms(
            body,
            (
                "의도:",
                "안전:",
                "품질:",
                "효율:",
                "사용자 부담:",
                "단순성:",
                "복구:",
                "내부 단계를 줄였더라도 총시간·사용자 노력·재작업 또는 결함 위험이 늘면 제품 회귀다.",
            ),
            "net-benefit guardrails",
        )

    def test_adaptive_assurance_is_internal_binary_and_monotonic(self):
        business = normalized(BUSINESS)
        architecture = normalized(ARCHITECTURE)
        contracts = normalized(CONTRACTS)
        phase1 = normalized(PHASE1)

        self.assert_terms(
            business,
            (
                "mode 선택은 내부 변속기다.",
                "사용자가 `lite | standard | assurance`를 선택",
                "strict Lite와 기존 Full Assurance의 두 실행 경로",
                "`standard`는 관측·분석 label",
                "같은 cycle에서 더 낮은 경로로 다시 내리지 않는다.",
            ),
            "authoritative adaptive boundary",
        )
        self.assert_terms(
            architecture,
            (
                "내부 risk-to-procedure 선택기",
                "strict Lite와 현재 Full Assurance 두 개",
                "`standard`는 별도 순효익이 증명되기 전까지 관측 label",
                "기존 Full Assurance로 단조 복귀",
            ),
            "architecture adaptive boundary",
        )
        self.assert_terms(
            contracts,
            (
                "사용자는 mode를 선택하지 않으며 내부 분류를 위해 추가 질문을 받지 않는다.",
                "strict Lite와 기존 Full Assurance 두 경로",
                "`standard`는 독립 실행 계약이 아니라 관측 label",
                "기존 Full Assurance로 단조 복귀",
            ),
            "consumer adaptive boundary",
        )
        self.assert_terms(
            phase1,
            (
                "The first live activation, if separately approved, must be binary",
                "strict Lite",
                "existing Full Assurance",
                "`standard` remains an observation label",
                "promotes monotonically to the existing Full Assurance path",
                "The user never selects a mode.",
            ),
            "Phase 1 adaptive boundary",
        )

    def test_component_outputs_align_to_the_product_artifacts(self):
        architecture = normalized(ARCHITECTURE)
        contracts = normalized(CONTRACTS)
        self.assert_terms(
            architecture,
            (
                "사용자 목표와 사용자 소유 결정 → 제품 북극성·사용자 산출물 계약 → Prime·Run·Set의 책임 경계",
                "mode, sidecar, reviewer 또는 worktree가 존재한다는 이유로 사용자 질문·문서·단계를 추가해서는 안 된다.",
                "검증된 실제 변경·증거·통합 선택",
            ),
            "architecture dependency direction",
        )
        self.assert_terms(
            contracts,
            (
                "내부 mechanism 변경이 사용자 질문·승인 단계·읽기 부담·Time to Trusted Change를 늘리면 인터페이스 회귀로 취급한다.",
                "repository-derived 기술 판단과 내부 mode 선택을 사용자에게 되묻지 않는다.",
                "현재 candidate manifest version은 `1.9.0`이다.",
            ),
            "consumer outcome contract",
        )

    def test_release_standards_require_measurement_and_keep_research_out_of_live_context(self):
        body = normalized(STANDARDS)
        self.assert_terms(
            body,
            (
                "Time to Trusted Change와 사용자 산출물 계약",
                "내부 단계 수나 mode 정확도만으로 순개선을 주장하지 않는다.",
                "strict Lite와 기존 Full Assurance의 binary topology",
                "상세 연구 자료는 `research/`에 둔다.",
                "paired baseline",
                "측정 전에 cohort와 non-inferiority 또는 improvement margin을 고정",
                "실제 pilot 전에는 예상 절감으로, pilot 후에는 측정된 end-to-end Time to Trusted Change로 구분",
            ),
            "north-star release standards",
        )


if __name__ == "__main__":
    unittest.main()
