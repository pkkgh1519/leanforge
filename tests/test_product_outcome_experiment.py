import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import product_outcome_experiment as experiment  # noqa: E402


class ProductOutcomeExperimentTests(unittest.TestCase):
    def check(self, result: dict, check_id: str) -> dict:
        return next(check for check in result["checks"] if check["id"] == check_id)

    def mutate(self, relative: str, old: str, new: str) -> dict:
        body = (ROOT / relative).read_text(encoding="utf-8")
        self.assertEqual(1, body.count(old), (relative, old))
        return {relative: body.replace(old, new)}

    def test_current_repository_passes_the_minimum_product_outcome_experiment(self):
        result = experiment.evaluate(ROOT)
        self.assertTrue(result["passed"], result)
        self.assertEqual({"passed": 7, "total": 7}, result["score"])

    def test_three_doc_first_marketplace_copy_is_rejected(self):
        overrides = self.mutate(
            "platform/codex/plugin.json",
            experiment.CODEX_SHORT_DESCRIPTION,
            "Turn any input into a grounded 3-doc, then execute it.",
        )
        result = experiment.evaluate(ROOT, overrides)
        self.assertFalse(self.check(result, "marketplace-outcome-promise")["passed"])

    def test_final_result_without_remaining_risk_is_rejected(self):
        overrides = self.mutate("src/skills/run/SKILL.md", "3. **Remaining risk**", "3. **Notes**")
        result = experiment.evaluate(ROOT, overrides)
        self.assertFalse(self.check(result, "run-final-result-contract")["passed"])

    def test_terminal_blocker_without_preserved_state_contract_is_rejected(self):
        overrides = self.mutate(
            "src/skills/run/SKILL.md",
            "completed or preserved state",
            "an internal status summary",
        )
        result = experiment.evaluate(ROOT, overrides)
        self.assertFalse(self.check(result, "run-final-result-contract")["passed"])

    def test_generated_run_result_contract_drift_is_rejected(self):
        overrides = self.mutate("codex/plugin/skills/run/SKILL.md", "4. **Integration**", "4. **Delivery**")
        result = experiment.evaluate(ROOT, overrides)
        self.assertFalse(self.check(result, "run-final-result-contract")["passed"])

    def test_golden_result_without_verification_is_rejected(self):
        overrides = self.mutate("examples/trusted-change-package/result.md", "## Verification", "## Activity")
        result = experiment.evaluate(ROOT, overrides)
        self.assertFalse(self.check(result, "golden-cycle-package")["passed"])

    def test_unmeasured_every_task_faster_claim_is_rejected(self):
        body = (ROOT / "README.md").read_text(encoding="utf-8")
        overrides = {
            "README.md": body.replace(
                "Leanforge asks only for decisions the user owns,",
                "Leanforge makes every task faster and asks only for decisions the user owns,",
                1,
            )
        }
        result = experiment.evaluate(ROOT, overrides)
        self.assertFalse(self.check(result, "unsupported-performance-claims-absent")["passed"])

    def test_missing_candidate_files_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="leanforge-product-outcome-empty-") as temp:
            result = experiment.evaluate(Path(temp))
        self.assertFalse(result["passed"])
        self.assertLess(result["score"]["passed"], result["score"]["total"])


if __name__ == "__main__":
    unittest.main()
