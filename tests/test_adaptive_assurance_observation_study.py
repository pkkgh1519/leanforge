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
        missing = [term for term in terms if term not in body]
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
                "seal Section A",
                "then reveal the prediction",
                "The observation never changes the current cycle.",
            ),
            "observation and blinded-adjudication boundary",
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

    def test_manual_template_preserves_order_redaction_and_exact_shadow_payload(self):
        body = read(TEMPLATE)
        self.assert_terms(
            body,
            (
                "A. Sealed shadow prediction",
                "B. Independent observed class",
                "C. Reveal and comparison",
                "D. Redaction and integrity check",
                "Copy the sidecar unchanged",
                "The independent class was fixed before the shadow mode was revealed.",
                "Missing or contradictory evidence was not counted as a pass.",
                "This record did not alter the observed Prime or Run cycle.",
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
                "does not activate Lite",
                "No completed observation record belongs in this public repository.",
            ),
            "Phase 1 study handoff",
        )
        self.assert_terms(
            status,
            (
                "Phase 1.2 observation study protocol",
                "zero unresolved Lite-to-Assurance cases",
                "separate reviewed release",
            ),
            "project status study gate",
        )
        for path in (PROTOCOL, TEMPLATE):
            relative = path.relative_to(ROOT).as_posix()
            self.assertIn(f"{relative} text eol=lf", attributes)


if __name__ == "__main__":
    unittest.main()
