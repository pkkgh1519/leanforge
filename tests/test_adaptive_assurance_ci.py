import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AdaptiveAssuranceCiContractTests(unittest.TestCase):
    def test_ci_fetches_full_history_for_predecessor_blob_baselines(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertEqual(1, ci.count("uses: actions/checkout@v4"))
        self.assertEqual(1, ci.count("fetch-depth: 0"))


if __name__ == "__main__":
    unittest.main()
