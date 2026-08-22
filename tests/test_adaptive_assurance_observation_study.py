import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/adaptive-assurance-observation-study.md"
TEMPLATE = ROOT / "docs/adaptive-assurance-observation-template.md"
PHASE1 = ROOT / "docs/adaptive-assurance-phase1.md"
STATUS = ROOT / "docs/tracking/status.md"
PILOT = ROOT / "src/skills/prime/references/adaptive-assurance-lite-pilot.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class AdaptiveAssuranceObservationStudyTests(unittest.TestCase):
    def assert_terms(self, body: str, terms: tuple[str, ...], context: str) -> None:
        normalized = " ".join(body.split())
        missing = [
            term for term in terms if " ".join(term.split()) not in normalized
        ]
        self.assertFalse(missing, f"missing {context}: {missing}")

    def test_protocol_separates_shadow_prediction_from_blinded_adjudication(self):
        body = read(PROTOCOL)
        self.assert_terms(
            body,
            (
                "The study is observation only.",
                "Collector:",
                "Adjudicator:",
                "Resolver:",
                "without reading the sidecar mode, reasons",
                "mechanically without inspecting its contents",
                "Reveal the prediction only after",
                "The observation never changes the current cycle.",
            ),
            "observation and blinded-adjudication boundary",
        )

    def test_protocol_pins_one_router_revision_per_study_batch(self):
        body = read(PROTOCOL)
        self.assert_terms(
            body,
            (
                "one exact Leanforge commit",
                "Git blob object ID",
                "Do not pool observations from different router or contract revisions.",
                "starts a new study batch",
                "do not carry the old batch's coverage count forward",
            ),
            "pinned router revision",
        )

    def test_protocol_predeclares_enrollment_and_host_scope(self):
        body = read(PROTOCOL)
        self.assert_terms(
            body,
            (
                "Before reading any prediction in a batch",
                "Do not decide whether to enroll a case after seeing its shadow mode.",
                "Record every eligible Prime cycle",
                "Convenience, an unexpected prediction, or an inconvenient outcome is not an exclusion reason.",
                "host-limited pilot",
                "counts by host",
            ),
            "cohort selection and host coverage",
        )

    def test_protocol_has_fail_closed_comparison_and_activation_gates(self):
        body = read(PROTOCOL)
        self.assert_terms(
            body,
            (
                "lite_to_standard",
                "material_false_negative",
                "unevaluable",
                "any shadow `lite` case is independently observed as `assurance`",
                "Aggregate percentages must not hide an underclassified case.",
                "The study cannot activate Lite by itself.",
                "GO_TO_PHASE_2_REVIEW",
                "NO_GO",
            ),
            "comparison and activation gates",
        )

    def test_protocol_minimizes_data_and_excludes_synthetic_cases_from_evidence(self):
        body = read(PROTOCOL)
        self.assert_terms(
            body,
            (
                "Do not commit them to the public Leanforge repository.",
                "Do not record raw prompts",
                "proprietary source",
                "secrets",
                "personal data",
                "Synthetic contract cases remain test oracles",
                "do not count as real shadow observations",
            ),
            "data-minimization and real-observation boundary",
        )

    def test_manual_template_preserves_order_revision_cohort_and_exact_payload(self):
        body = read(TEMPLATE)
        self.assert_terms(
            body,
            (
                "A. Sealed shadow prediction",
                "B. Independent observed class",
                "C. Reveal and comparison",
                "D. Redaction and integrity check",
                "Predeclared observation window or case range:",
                "Enrollment status:",
                "Leanforge commit:",
                "Adaptive Assurance contract Git blob object ID:",
                "Copy the sidecar unchanged",
                "Case enrollment decided before prediction reveal:",
                "This case was not selected or excluded because of its shadow mode or outcome.",
                "The independent class was fixed before the shadow mode was revealed.",
                "This record is not pooled with a different router or contract revision.",
            ),
            "manual observation worksheet",
        )

    def test_study_remains_documentation_only_and_pilot_remains_shadow(self):
        protocol_name = PROTOCOL.name
        template_name = TEMPLATE.name
        for skill_root in (ROOT / "src/skills").iterdir():
            if not skill_root.is_dir():
                continue
            for path in skill_root.rglob("*.md"):
                body = read(path)
                with self.subTest(path=path.relative_to(ROOT).as_posix()):
                    self.assertNotIn(protocol_name, body)
                    self.assertNotIn(template_name, body)

        pilot = json.loads(read(PILOT))
        self.assertEqual("shadow", pilot["activation"])

    def test_phase1_status_and_lf_contract_point_to_the_study_without_claiming_results(self):
        phase1 = read(PHASE1)
        status = read(STATUS)
        attributes = read(ROOT / ".gitattributes")

        self.assert_terms(
            phase1,
            (
                "adaptive-assurance-observation-study.md",
                "adaptive-assurance-observation-template.md",
                "one pinned Leanforge commit and contract blob",
                "predeclared cohort",
                "does not activate Lite",
                "No completed observation record belongs in this public repository.",
            ),
            "Phase 1 study handoff",
        )
        self.assert_terms(
            status,
            (
                "Phase 1.2 observation study protocol",
                "고정된 router revision",
                "사전 등록된 cohort",
                "zero unresolved Lite-to-Assurance cases",
                "별도 reviewed release",
                "20회 behavior smoke",
                "100회 반복 측정",
            ),
            "project status study gate and preserved measurement commitments",
        )
        for path in (PROTOCOL, TEMPLATE):
            relative = path.relative_to(ROOT).as_posix()
            self.assertIn(f"{relative} text eol=lf", attributes)


if __name__ == "__main__":
    unittest.main()
