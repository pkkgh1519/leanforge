import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/adaptive_assurance_shadow.py"
CONTRACT = ROOT / "src/skills/prime/references/adaptive-assurance-contract.json"
CORPUS = ROOT / "tests/fixtures/adaptive_assurance_cases_v1.json"


class AdaptiveAssuranceShadowRunnerTest(unittest.TestCase):
    def test_writes_exact_shadow_record_atomically(self):
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
        source = next(
            c for c in corpus["cases"] if c["case_id"] == "lite-single-regression-fix"
        )
        case = {k: v for k, v in source.items() if not k.startswith("expected_")}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_path = root / "case.json"
            output = root / ".leanforge" / "assurance-shadow.json"
            case_path.write_text(json.dumps(case) + "\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--contract",
                    str(CONTRACT),
                    "--case",
                    str(case_path),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertFalse(output.with_name(output.name + ".tmp").exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "schema_version",
                    "shadow_only",
                    "cycle",
                    "mode",
                    "reasons",
                    "hard_triggers",
                    "missing_lite_required_true",
                    "violated_lite_required_false",
                    "harness_sync",
                },
                set(payload),
            )
            self.assertEqual("delta", payload["cycle"])
            self.assertEqual("lite", payload["mode"])
            self.assertEqual(["lite_eligible"], payload["reasons"])
            self.assertTrue(payload["shadow_only"])
            self.assertFalse(payload["harness_sync"])

    def test_malformed_case_discards_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case_path = root / "bad.json"
            output = root / "out.json"
            stale_tmp = output.with_name(output.name + ".tmp")
            case_path.write_text('{"schema_version":1}\n', encoding="utf-8")
            output.write_text('{"mode":"lite"}\n', encoding="utf-8")
            stale_tmp.write_text("stale\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--contract",
                    str(CONTRACT),
                    "--case",
                    str(case_path),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, completed.returncode)
            self.assertFalse(output.exists())
            self.assertFalse(stale_tmp.exists())


if __name__ == "__main__":
    unittest.main()
