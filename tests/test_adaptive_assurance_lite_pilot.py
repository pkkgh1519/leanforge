import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "src/skills/prime/references/adaptive-assurance-contract.json"
PILOT_SURFACES = (
    ROOT / "src/skills/prime/references/adaptive-assurance-lite-pilot.json",
    ROOT / "claude/skills/prime/references/adaptive-assurance-lite-pilot.json",
    ROOT / "codex/plugin/skills/prime/references/adaptive-assurance-lite-pilot.json",
)


class AdaptiveAssuranceLitePilotTests(unittest.TestCase):
    def test_pilot_contract_is_closed_dormant_and_surface_identical(self):
        raw = [path.read_bytes() for path in PILOT_SURFACES]
        self.assertEqual(1, len(set(raw)))
        pilot = json.loads(raw[0])

        self.assertEqual(
            {
                "schema_version",
                "contract_id",
                "activation",
                "eligibility_contract",
                "promotion_policy",
                "prime",
                "run",
                "escalate_to_standard_on",
                "escalate_to_assurance_on",
            },
            set(pilot),
        )
        self.assertEqual(
            {
                "artifact_contract",
                "preconditions",
                "intent_completeness_review",
                "three_doc_gate",
                "user_approval",
                "questions",
            },
            set(pilot["prime"]),
        )
        self.assertEqual(
            {
                "git_preflight",
                "recovery_guard",
                "contract_validation",
                "execution",
                "worktree",
                "task_verification",
                "integration_verification",
                "completion_verification",
                "evidence_reuse",
                "runtime_smoke",
                "final_independent_review",
                "final_diff_check",
                "harness_sync",
                "user_integration_choice",
            },
            set(pilot["run"]),
        )
        self.assertEqual(1, pilot["schema_version"])
        self.assertEqual("leanforge.adaptive-assurance-lite-pilot", pilot["contract_id"])
        self.assertEqual("shadow", pilot["activation"])
        self.assertEqual("leanforge.adaptive-assurance#lite", pilot["eligibility_contract"])
        self.assertEqual("monotonic", pilot["promotion_policy"])

    def test_lite_pilot_reduces_ceremony_without_weakening_hard_boundaries(self):
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))
        prime = pilot["prime"]
        run = pilot["run"]

        self.assertEqual("existing_3doc_thin", prime["artifact_contract"])
        self.assertEqual("keep", prime["preconditions"])
        self.assertEqual("skip", prime["intent_completeness_review"])
        self.assertEqual("skip", prime["three_doc_gate"])
        self.assertEqual("keep", prime["user_approval"])
        self.assertEqual("user_owned_only", prime["questions"])

        self.assertEqual("keep", run["git_preflight"])
        self.assertEqual("keep", run["recovery_guard"])
        self.assertEqual("keep", run["contract_validation"])
        self.assertEqual("direct", run["execution"])
        self.assertEqual("skip", run["worktree"])
        self.assertEqual("targeted", run["task_verification"])
        self.assertEqual("skip", run["integration_verification"])
        self.assertEqual("full_once", run["completion_verification"])
        self.assertEqual("exact_only", run["evidence_reuse"])
        self.assertEqual("when_spec_declares_runnable_service", run["runtime_smoke"])
        self.assertEqual("skip", run["final_independent_review"])
        self.assertEqual("keep", run["final_diff_check"])
        self.assertEqual("skip", run["harness_sync"])
        self.assertEqual("keep", run["user_integration_choice"])

    def test_pilot_escalation_vocabulary_matches_shadow_contract(self):
        main = json.loads(MAIN.read_text(encoding="utf-8"))
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))

        self.assertEqual(
            set(main["escalation_signals"]["to_standard"]),
            set(pilot["escalate_to_standard_on"]),
        )
        self.assertEqual(
            set(main["escalation_signals"]["to_assurance"]),
            set(pilot["escalate_to_assurance_on"]),
        )


if __name__ == "__main__":
    unittest.main()
