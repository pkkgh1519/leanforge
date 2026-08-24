import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
SOURCE = ROOT / "src/skills/prime/references/grounds-gate.md"

sys.path.insert(0, str(TOOLS))
import adaptive_assurance_study as study  # noqa: E402


class AdaptiveAssuranceStudySurfaceTests(unittest.TestCase):
    def test_shadow_hook_is_the_terminal_exact_control_boundary(self):
        working_tree_bytes = SOURCE.read_bytes()
        candidate = study.normalized_lf_bytes(working_tree_bytes)
        marker = f"\n{study.SHADOW_HEADING}\n".encode()

        self.assertEqual(1, candidate.count(marker))
        prefix, shadow = candidate.split(marker, 1)
        self.assertTrue(shadow.strip())
        self.assertNotIn(b"\n## ", shadow)
        self.assertNotIn(b"\r", candidate)

        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / "grounds-gate.md"
            copied.write_bytes(working_tree_bytes)
            original, control = study.strip_shadow(copied)

        self.assertEqual(working_tree_bytes, original)
        self.assertEqual(prefix.rstrip() + b"\n", control)
        self.assertNotIn(marker, control)

    def test_shadow_hook_rejects_unsupported_lone_cr(self):
        candidate = SOURCE.read_bytes().replace(b"\r\n", b"\n")
        candidate = candidate.replace(b"\n## ", b"\r## ", 1)

        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / "grounds-gate.md"
            copied.write_bytes(candidate)
            with self.assertRaisesRegex(study.StudyError, "unsupported lone CR"):
                study.strip_shadow(copied)


if __name__ == "__main__":
    unittest.main()
