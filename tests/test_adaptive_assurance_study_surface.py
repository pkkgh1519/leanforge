import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
SOURCE = ROOT / "src/skills/prime/references/grounds-gate.md"

import sys

sys.path.insert(0, str(TOOLS))
import adaptive_assurance_study as study  # noqa: E402


class AdaptiveAssuranceStudySurfaceTests(unittest.TestCase):
    def test_shadow_hook_is_the_terminal_exact_control_boundary(self):
        candidate = SOURCE.read_bytes()
        marker = f"\n{study.SHADOW_HEADING}\n".encode()

        self.assertEqual(1, candidate.count(marker))
        prefix, shadow = candidate.split(marker, 1)
        self.assertTrue(shadow.strip())
        self.assertNotIn(b"\n## ", shadow)
        self.assertNotIn(b"\r", candidate)

        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp) / "grounds-gate.md"
            copied.write_bytes(candidate)
            original, control = study.strip_shadow(copied)

        self.assertEqual(candidate, original)
        self.assertEqual(prefix.rstrip() + b"\n", control)
        self.assertNotIn(marker, control)

    def test_manifest_pins_current_commit_tree_and_contract_blob(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            manifest = study.prepare_control(ROOT, workspace)

            self.assertEqual(
                study.git(ROOT, "rev-parse", "HEAD"),
                manifest["candidate"]["commit"],
            )
            self.assertEqual(
                study.git(ROOT, "rev-parse", "HEAD^{tree}"),
                manifest["candidate"]["git_tree"],
            )
            self.assertEqual(
                study.git(
                    ROOT,
                    "rev-parse",
                    f"HEAD:{study.CONTRACT_REL.as_posix()}",
                ),
                manifest["candidate"]["contract_blob_sha1"],
            )


if __name__ == "__main__":
    unittest.main()
