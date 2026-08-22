import re
import unittest
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
BUSINESS = ROOT / "docs/business-rules.md"
ARCHITECTURE = ROOT / "docs/architecture.md"
CONTRACTS = ROOT / "docs/contracts.md"
STANDARDS = ROOT / "docs/standards.md"
PHASE1 = ROOT / "docs/adaptive-assurance-phase1.md"
STATUS = ROOT / "docs/tracking/status.md"
PROTOCOL = ROOT / "research/adaptive-assurance/pilot-readiness-study.md"
REPORT = ROOT / "research/adaptive-assurance/pilot-readiness-report-template.md"

PRODUCT_DOCUMENTS = (
    BUSINESS,
    ARCHITECTURE,
    CONTRACTS,
    STANDARDS,
    PHASE1,
    STATUS,
    PROTOCOL,
    REPORT,
)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def normalized(path: Path) -> str:
    return normalize_text(path.read_text(encoding="utf-8"))


def _policy_units(value: str) -> tuple[str, ...]:
    units: list[str] = []
    current: list[str] = []
    in_fence = False

    def flush() -> None:
        if not current:
            return
        paragraph = normalize_text(" ".join(current))
        units.extend(
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph)
            if sentence.strip()
        )
        current.clear()

    for raw_line in value.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            continue
        if re.match(r"^(?:[-*+]|\d+[.)])\s+", stripped):
            flush()
            current.append(stripped)
            continue
        current.append(stripped)
    flush()
    return tuple(units)


def _is_negated(sentence: str) -> bool:
    lowered = sentence.lower()
    return any(
        token in lowered
        for token in (
            "아니다",
            "않는다",
            "않으며",
            "않고",
            "해서는 안",
            "할 수 없다",
            "금지",
            "never",
            "must not",
            "does not",
            "do not",
            "cannot",
            "is not",
            "are not",
            "outside",
            "forbidden",
            "exclude",
            "yes is failure",
            "no benefit",
        )
    )


def validate_no_normative_inversions(documents: Mapping[str, str]) -> None:
    violations: list[str] = []
    for path, body in documents.items():
        for sentence in _policy_units(body):
            lowered = sentence.lower()
            negated = _is_negated(sentence)

            if (
                "제품의 1차 성과는" in sentence
                and any(term in lowered for term in ("문서 수", "reviewer 수", "worktree 수"))
                and not negated
            ):
                violations.append(f"{path}: primary outcome inverted: {sentence}")

            if (
                "time to trusted change" in lowered
                and any(
                    term in lowered
                    for term in (
                        "참고 지표",
                        "secondary metric",
                        "optional metric",
                        "non-primary metric",
                    )
                )
                and not negated
            ):
                violations.append(f"{path}: north-star metric demoted: {sentence}")

            has_all_modes = all(mode in lowered for mode in ("lite", "standard", "assurance"))
            user_subject = any(term in lowered for term in ("사용자", "user"))
            selection_verb = any(term in lowered for term in ("선택", "choose", "select"))
            if has_all_modes and user_subject and selection_verb and not negated:
                violations.append(f"{path}: user-facing mode selection introduced: {sentence}")

            standard_topology = (
                "standard" in lowered
                and any(term in lowered for term in ("세 번째", "third", "three"))
                and any(
                    term in lowered
                    for term in ("workflow", "topology", "orchestration", "실행 경로")
                )
            )
            if standard_topology and not negated:
                violations.append(f"{path}: third Standard topology introduced: {sentence}")

            go_authority = (
                ("go_to_phase_2_design_review" in lowered or "go recommendation" in lowered)
                and any(
                    term in lowered
                    for term in (
                        "activation",
                        "activate_lite",
                        "reviewer",
                        "worktree",
                        "evidence reuse",
                        "harness sync",
                    )
                )
                and any(term in lowered for term in ("승인", "허용", "authorize", "approve", "permit"))
            )
            if go_authority and not negated:
                violations.append(f"{path}: GO authority expanded beyond design review: {sentence}")

    if violations:
        raise AssertionError("\n".join(violations))


class ProductNorthStarContractTests(unittest.TestCase):
    def assert_terms(self, body: str, terms: tuple[str, ...], context: str) -> None:
        missing = [term for term in terms if normalize_text(term) not in body]
        self.assertFalse(missing, f"missing {context}: {missing}")

    def test_business_rules_define_one_authoritative_user_outcome(self):
        raw = BUSINESS.read_text(encoding="utf-8")
        body = normalize_text(raw)
        self.assertEqual(1, raw.count("## 제품 북극성 — 최상위 권위"))
        self.assertEqual(1, raw.count("## Adaptive Assurance 경계"))
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
                "초기: 기존 저장소 증거 + 사용자 결정 → durable project knowledge",
                "Set의 첫 실행은 현재 delivery cycle에서 바뀐 내용이 없어도 기존 코드·문서·dependencies·conventions·module boundaries를 읽어 초기 durable context를 만든다.",
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

    def test_authoritative_documents_have_no_normative_inversions(self):
        documents = {
            path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
            for path in PRODUCT_DOCUMENTS
        }
        validate_no_normative_inversions(documents)

    def test_negative_policy_controls_are_not_inversions(self):
        validate_no_normative_inversions(
            {
                "negative-controls.md": """
- exclude any saving that depends on a third `standard` execution topology;
- Savings depend on a third Standard topology: `<yes | no; yes is failure>`;
- User mode selection absent: `<yes | no>`.
"""
            }
        )

    def test_known_opposite_product_mutations_are_rejected(self):
        documents = {
            path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
            for path in PRODUCT_DOCUMENTS
        }
        mutations = (
            (
                "primary-outcome-inversion",
                BUSINESS.relative_to(ROOT).as_posix(),
                "제품의 1차 성과는 문서 수와 reviewer 수이며 Time to Trusted Change는 참고 지표일 뿐이다.",
            ),
            (
                "user-mode-selection",
                CONTRACTS.relative_to(ROOT).as_posix(),
                "사용자는 Lite, Standard, Assurance 세 실행 workflow 중\n하나를 직접 선택해야 한다.",
            ),
            (
                "third-standard-topology",
                ARCHITECTURE.relative_to(ROOT).as_posix(),
                "Standard를 세 번째 live workflow로 추가하고 별도 orchestration으로 실행한다.",
            ),
            (
                "go-authorizes-activation",
                PROTOCOL.relative_to(ROOT).as_posix(),
                "GO_TO_PHASE_2_DESIGN_REVIEW은 Lite activation과\nreviewer/worktree 생략을 승인한다.",
            ),
        )
        for name, path, opposite in mutations:
            mutated = dict(documents)
            mutated[path] = mutated[path] + "\n\n" + opposite + "\n"
            with self.subTest(mutation=name):
                with self.assertRaises(AssertionError):
                    validate_no_normative_inversions(mutated)


if __name__ == "__main__":
    unittest.main()
