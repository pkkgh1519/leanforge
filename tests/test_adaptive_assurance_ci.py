import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AdaptiveAssuranceCiContractTests(unittest.TestCase):
    def test_ci_fetches_full_history_for_predecessor_blob_baselines(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertEqual(1, ci.count("uses: actions/checkout@v4"))
        self.assertEqual(1, ci.count("fetch-depth: 0"))

    def test_ci_prepares_and_reverifies_the_exact_shadow_disabled_control(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertEqual(
            1, ci.count("Verify Adaptive Assurance shadow-disabled control")
        )
        self.assertEqual(1, ci.count("prepare-control"))
        self.assertEqual(1, ci.count("verify-control"))
        self.assertIn("$RUNNER_TEMP/adaptive-assurance-study-control", ci)
        self.assertIn("cmp \\", ci)

        prepare = ci.index("prepare-control")
        verify = ci.index("verify-control")
        unit_tests = ci.index("Run all unit tests")
        self.assertLess(prepare, verify)
        self.assertLess(verify, unit_tests)


if __name__ == "__main__":
    unittest.main()
