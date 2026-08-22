import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/adaptive-assurance/pilot-readiness-study.md"
OBSERVATION = ROOT / "research/adaptive-assurance/observation-template.md"
REPORT = ROOT / "research/adaptive-assurance/pilot-readiness-report-template.md"


def normalize(value: str) -> str:
    return " ".join(value.split())


def validate_realizable_value_contract(
    protocol: str,
    observation: str,
    report: str,
) -> None:
    required = {
        "protocol": (
            "A **realizable Lite-benefit case** must have a shadow prediction of `lite`",
            "remain `lite` after final facts and later escalation",
            "a conservative shadow Standard or Assurance prediction that later adjudicates as Lite still follows Full Assurance",
            "sum(conservative removable seconds across all enrolled cycles) / enrolled cycle count",
        ),
        "observation": (
            "Shadow prediction is Lite:",
            "Escalated observed class remains Lite:",
            "Realizable Lite-benefit case:",
            "Counts in realizable Lite-benefit numerator:",
        ),
        "report": (
            "Realizable shadow-Lite→observed-Lite cycles",
            "zero benefit assigned unless the shadow prediction is Lite",
            "the escalated observed class remains Lite",
        ),
    }
    bodies = {
        "protocol": normalize(protocol),
        "observation": normalize(observation),
        "report": normalize(report),
    }
    missing = [
        f"{name}: {term}"
        for name, terms in required.items()
        for term in terms
        if normalize(term) not in bodies[name]
    ]
    if missing:
        raise AssertionError("missing realizable-benefit boundaries: " + repr(missing))

    forbidden = (
        "Every final observed Lite case contributes removable benefit.",
        "Conservative Standard-to-Lite cases contribute removable benefit.",
    )
    violations = [
        phrase
        for phrase in forbidden
        if normalize(phrase) in bodies["protocol"]
    ]
    if violations:
        raise AssertionError("unreachable savings admitted: " + repr(violations))


class AdaptiveAssuranceRealizableValueTests(unittest.TestCase):
    def test_only_reachable_shadow_lite_cases_contribute_benefit(self):
        validate_realizable_value_contract(
            PROTOCOL.read_text(encoding="utf-8"),
            OBSERVATION.read_text(encoding="utf-8"),
            REPORT.read_text(encoding="utf-8"),
        )

    def test_conservative_standard_to_lite_benefit_mutation_is_rejected(self):
        protocol = PROTOCOL.read_text(encoding="utf-8") + (
            "\nEvery final observed Lite case contributes removable benefit.\n"
        )
        with self.assertRaises(AssertionError):
            validate_realizable_value_contract(
                protocol,
                OBSERVATION.read_text(encoding="utf-8"),
                REPORT.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
