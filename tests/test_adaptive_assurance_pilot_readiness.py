import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/adaptive-assurance/pilot-readiness-study.md"
OBSERVATION = ROOT / "research/adaptive-assurance/observation-template.md"
REPORT = ROOT / "research/adaptive-assurance/pilot-readiness-report-template.md"
PHASE1 = ROOT / "docs/adaptive-assurance-phase1.md"
STATUS = ROOT / "docs/tracking/status.md"
PILOT = ROOT / "src/skills/prime/references/adaptive-assurance-lite-pilot.json"
ATTRIBUTES = ROOT / ".gitattributes"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class AdaptiveAssurancePilotReadinessTests(unittest.TestCase):
    def assert_terms(self, body: str, terms: tuple[str, ...], context: str) -> None:
        missing = [term for term in terms if " ".join(term.split()) not in body]
        self.assertFalse(missing, f"missing {context}: {missing}")

    def test_study_is_outside_default_docs_and_live_skill_surfaces(self):
        self.assertTrue(PROTOCOL.is_file())
        self.assertTrue(OBSERVATION.is_file())
        self.assertTrue(REPORT.is_file())
        self.assertFalse(
            (ROOT / "docs/adaptive-assurance-observation-study.md").exists()
        )
        self.assertFalse(
            (ROOT / "docs/adaptive-assurance-observation-template.md").exists()
        )

        names = {PROTOCOL.name, OBSERVATION.name, REPORT.name}
        for surface in (
            ROOT / "src/skills",
            ROOT / "claude/skills",
            ROOT / "codex/plugin/skills",
        ):
            for path in surface.rglob("*.md"):
                body = path.read_text(encoding="utf-8")
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    for name in names:
                        self.assertNotIn(name, body)

    def test_study_is_pilot_readiness_not_classifier_accuracy_only(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "Time to Trusted Change",
                "Safety:",
                "Shadow tax:",
                "Quality:",
                "User burden:",
                "Potential value and reversibility:",
                "A classifier can be accurate and still fail this study",
                "Phase 1.2 does not activate Lite and therefore cannot prove actual Lite net benefit.",
            ),
            "north-star study dimensions",
        )

    def test_first_pilot_topology_is_binary_and_internal(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "The user never selects `lite | standard | assurance`.",
                "The first live pilot has only two execution paths: strict Lite and existing Full Assurance.",
                "`standard` remains an observational label.",
                "A newly discovered risk promotes monotonically to the existing Full Assurance path.",
                "three independent live workflows",
                "outside this study's admissible Phase 2 design",
            ),
            "binary internal pilot boundary",
        )

    def test_safety_cohort_is_revision_pinned_blinded_and_fail_closed(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "one exact Leanforge commit",
                "Git blob object ID",
                "Do not pool observations",
                "Before reading any prediction",
                "Record every eligible Prime cycle",
                "without reading the prediction",
                "material_false_negative",
                "at least 35 usable real observations",
                "at least 15 shadow `lite`",
                "at least 10 shadow `standard`",
                "at least 10 shadow `assurance`",
            ),
            "safety study integrity",
        )

    def test_shadow_tax_benchmark_has_paired_versions_metrics_and_margins(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "2d2be39c01c9d19819acb0c658f07d06b06931a7",
                "5 cases × 2 hosts × 2 versions × 5 repetitions = 100 runs",
                "randomized A/B order",
                "wall-clock from Prime invocation to G7",
                "tool-call count and files read",
                "subagent dispatch count",
                "number of user questions and user reply turns",
                "median time-to-G7 regression: no more than `5%`",
                "p90 time-to-G7 regression: no more than `10%`",
                "at most one small contract read and one sidecar replacement",
            ),
            "paired shadow-tax benchmark",
        )

    def test_quality_user_burden_potential_value_and_go_gate_are_closed(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "Use a blinded reviewer",
                "surviving user-owned ambiguity",
                "3-doc-gate blocker rate",
                "no mode-induced user burden",
                "conservative median removable-ceremony estimate to exceed the measured median shadow tax by at least `2×`",
                "`GO_TO_PHASE_2_DESIGN_REVIEW` requires all of the following",
                "A GO decision authorizes only a separate Phase 2 design review.",
            ),
            "quality, burden, value, and decision gate",
        )

    def test_templates_capture_product_gates_without_claiming_activation(self):
        observation = normalized(OBSERVATION)
        report = normalized(REPORT)
        self.assert_terms(
            observation,
            (
                "Product north-star observation",
                "User was asked to choose or understand a mode:",
                "Shadow collection added a subagent dispatch:",
                "Prime invocation to G7 or stop",
                "Potential Lite value",
                "Estimated net removable cost after shadow tax",
            ),
            "per-cycle product observation",
        )
        self.assert_terms(
            report,
            (
                "Safety gate:",
                "Shadow-tax gate:",
                "Quality gate:",
                "User-burden gate:",
                "Potential-value gate:",
                "Binary reversibility gate:",
                "A GO recommendation requires every gate to pass.",
                "These figures are a design estimate. They are not actual Lite performance evidence.",
                "Actual end-to-end Time to Trusted Change improvement must be measured in Phase 2",
            ),
            "final pilot-readiness report",
        )

    def test_phase1_status_lf_and_dormant_activation_match_the_study(self):
        phase1 = normalized(PHASE1)
        status = normalized(STATUS)
        attributes = ATTRIBUTES.read_text(encoding="utf-8")
        pilot = json.loads(PILOT.read_text(encoding="utf-8"))

        self.assert_terms(
            phase1,
            (
                "research/adaptive-assurance/pilot-readiness-study.md",
                "The first live activation, if separately approved, must be binary",
                "It never activates Lite.",
                "claim actual Time to Trusted Change improvement",
            ),
            "Phase 1 handoff",
        )
        self.assert_terms(
            status,
            (
                "Time to Trusted Change",
                "100회를 수행",
                "median time-to-G7 +5%, p90 +10%",
                "strict Lite와 기존 Full Assurance 두 실행 경로",
                "보수적인 removable-ceremony 추정치가 측정된 median shadow tax의 2배 이상",
            ),
            "tracked study commitments",
        )
        self.assertIn(
            "research/adaptive-assurance/** text eol=lf", attributes
        )
        self.assertIn("tests/test_product_north_star.py text eol=lf", attributes)
        self.assertEqual("shadow", pilot["activation"])


if __name__ == "__main__":
    unittest.main()
