import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACES = (
    "src/skills/prime/references/grounds-gate.md",
    "claude/skills/prime/references/grounds-gate.md",
    "codex/plugin/skills/prime/references/grounds-gate.md",
)


class AdaptiveAssurancePrimeHookTests(unittest.TestCase):
    def test_shadow_hook_is_identical_and_non_authoritative(self):
        bodies = [(ROOT / rel).read_text(encoding="utf-8") for rel in SURFACES]

        self.assertEqual(1, len(set(bodies)))
        body = bodies[0]
        self.assertIn("At the **ELICIT exit**", body)
        self.assertIn("adaptive-assurance-contract.json", body)
        self.assertIn(".leanforge/assurance-shadow.json", body)
        self.assertIn("**ELICIT-exit prediction**", body)
        self.assertIn("current Prime cycle's replaceable snapshot", body)
        self.assertIn("leave the sidecar absent", body)
        self.assertIn('"shadow_only": true', body)
        self.assertIn("closed decision_reasons atom", body)
        self.assertIn("**Shadow means no authority.**", body)
        self.assertIn("must not change Prime's stage sequence", body)
        self.assertIn("current Full Assurance behavior remains", body)


if __name__ == "__main__":
    unittest.main()
