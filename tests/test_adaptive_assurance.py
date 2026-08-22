import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "src/skills/prime/references/adaptive-assurance-contract.json"
CORPUS_PATH = ROOT / "tests/fixtures/adaptive_assurance_cases_v1.json"
MODULE_PATH = ROOT / "tools/adaptive_assurance.py"

spec = importlib.util.spec_from_file_location("adaptive_assurance", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load adaptive assurance router")
adaptive = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adaptive
spec.loader.exec_module(adaptive)

CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


class AdaptiveAssuranceTest(unittest.TestCase):
    def test_representative_corpus(self):
        seen = set()
        declared_reasons = set(CONTRACT["decision_reasons"])
        for case in CORPUS["cases"]:
            runtime = {
                k: copy.deepcopy(v)
                for k, v in case.items()
                if k not in {"expected_mode", "expected_harness_sync"}
            }
            with self.subTest(case_id=case["case_id"]):
                decision = adaptive.route_case(runtime, CONTRACT)
                self.assertEqual(case["expected_mode"], decision.mode)
                self.assertEqual(
                    case["expected_harness_sync"],
                    adaptive.harness_sync_required(runtime, CONTRACT),
                )
                self.assertTrue(decision.shadow_only)
                self.assertTrue(set(decision.reasons) <= declared_reasons)
                payload = adaptive.shadow_payload(runtime, CONTRACT)
                self.assertEqual(list(decision.reasons), payload["reasons"])
                seen.add(decision.mode)
        self.assertEqual({"lite", "standard", "assurance"}, seen)

    def test_decision_reason_vocabulary_is_closed(self):
        self.assertEqual(
            [
                "first_cycle",
                "hard_assurance_trigger",
                "lite_eligible",
                "standard_default",
            ],
            CONTRACT["decision_reasons"],
        )
        mutated = copy.deepcopy(CONTRACT)
        mutated["decision_reasons"].append("other")
        with self.assertRaises(adaptive.ContractError):
            adaptive.validate_contract(mutated)

    def test_unknown_trigger_fails_closed(self):
        case = {
            k: copy.deepcopy(v)
            for k, v in CORPUS["cases"][0].items()
            if k not in {"expected_mode", "expected_harness_sync"}
        }
        case["triggers"] = ["new-risk"]
        with self.assertRaises(adaptive.ContractError):
            adaptive.route_case(case, CONTRACT)

    def test_escalation_is_monotonic(self):
        self.assertEqual(
            "standard",
            adaptive.escalate_mode("lite", ["changed_scope_expanded"], CONTRACT),
        )
        self.assertEqual(
            "assurance",
            adaptive.escalate_mode("standard", ["external_state_discovered"], CONTRACT),
        )
        self.assertEqual(
            "assurance",
            adaptive.escalate_mode("assurance", ["changed_scope_expanded"], CONTRACT),
        )
        self.assertEqual(
            "assurance",
            adaptive.escalate_mode("lite", ["unknown-signal"], CONTRACT),
        )

    def test_evidence_reuse_requires_exact_identity(self):
        prior = {
            "outcome": "green",
            "base_sha": "a",
            "environment_fingerprint": "b",
            "relevant_scope_hash": "c",
            "verify_set": "d",
        }
        current = dict(prior)
        current["outcome"] = "pending"
        self.assertTrue(adaptive.can_reuse_evidence(prior, current, CONTRACT))
        for key in (
            "base_sha",
            "environment_fingerprint",
            "relevant_scope_hash",
            "verify_set",
        ):
            changed = dict(current)
            changed[key] += "x"
            with self.subTest(key=key):
                self.assertFalse(adaptive.can_reuse_evidence(prior, changed, CONTRACT))


if __name__ == "__main__":
    unittest.main()
