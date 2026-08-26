import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
MAIN = ROOT / "src/skills/prime/references/adaptive-assurance-contract.json"
PILOT_SURFACES = (
    ROOT / "src/skills/prime/references/adaptive-assurance-lite-pilot.json",
    ROOT / "claude/skills/prime/references/adaptive-assurance-lite-pilot.json",
    ROOT / "codex/plugin/skills/prime/references/adaptive-assurance-lite-pilot.json",
)
TOOL = ROOT / "tools/adaptive_assurance_pilot.py"

spec = importlib.util.spec_from_file_location("adaptive_assurance_pilot", TOOL)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load adaptive assurance pilot oracle")
pilot_oracle = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot_oracle
spec.loader.exec_module(pilot_oracle)


def lite_shadow() -> dict:
    return {
        "schema_version": 1,
        "shadow_only": True,
        "cycle": "delta",
        "mode": "lite",
        "reasons": ["lite_eligible"],
        "hard_triggers": [],
        "missing_lite_required_true": [],
        "violated_lite_required_false": [],
        "harness_sync": False,
    }


def markdown_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return text
    _, _, body = text.split("---\n", 2)
    return body


def normalized(text: str) -> str:
    return " ".join(text.split())


class AdaptiveAssuranceLitePilotTests(unittest.TestCase):
    def test_pilot_contract_is_default_off_binary_and_surface_identical(self):
        raw = [path.read_bytes() for path in PILOT_SURFACES]
        self.assertEqual(1, len(set(raw)))
        pilot = json.loads(raw[0])
        pilot_oracle.validate_pilot_contract(pilot)
        self.assertEqual("default_off", pilot["activation"])
        self.assertEqual(["strict_lite", "full_assurance"], pilot["live_topology"])
        self.assertNotIn("standard", pilot["live_topology"])

    def test_alpha_removes_only_low_risk_ceremony(self):
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))
        prime = pilot["prime"]
        run = pilot["run"]
        self.assertEqual("skip", prime["intent_completeness_review"])
        self.assertEqual("keep", prime["three_doc_gate"])
        self.assertEqual("keep", prime["user_approval"])
        self.assertEqual("existing_direct_route", run["execution"])
        self.assertEqual("full_once", run["completion_verification"])
        self.assertEqual("keep", run["final_independent_review"])
        self.assertEqual("skip_when_no_durable_change", run["harness_sync"])
        self.assertEqual("keep", run["user_integration_choice"])

    def test_enabled_exact_lite_shadow_derives_one_profile(self):
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))
        activation = {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": True}
        self.assertEqual(
            {
                "schema_version": 1,
                "contract_id": "leanforge.adaptive-assurance-live-profile",
                "profile": "strict_lite_alpha",
                "cycle": "delta",
                "reason": "lite_eligible",
                "harness_sync": False,
            },
            pilot_oracle.derive_profile(pilot, activation, lite_shadow()),
        )

    def test_off_nonlite_and_malformed_inputs_fail_closed_to_full(self):
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))
        off = {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": False}
        self.assertIsNone(pilot_oracle.derive_profile(pilot, off, lite_shadow()))
        for mode in ("standard", "assurance"):
            shadow = lite_shadow()
            shadow["mode"] = mode
            shadow["reasons"] = ["standard_default" if mode == "standard" else "hard_assurance_trigger"]
            self.assertIsNone(
                pilot_oracle.derive_profile(
                    pilot,
                    {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": True},
                    shadow,
                )
            )
        malformed = copy.deepcopy(pilot)
        malformed["live_topology"].append("standard")
        with self.assertRaises(pilot_oracle.ContractError):
            pilot_oracle.validate_pilot_contract(malformed)

    def test_cli_removes_stale_profile_when_activation_is_absent_or_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / ".leanforge/assurance-profile.json"
            output.parent.mkdir(parents=True)
            output.write_text('{"profile":"strict_lite_alpha"}\n', encoding="utf-8")
            missing = root / "missing-activation.json"
            shadow = root / "shadow.json"
            shadow.write_text(json.dumps(lite_shadow()) + "\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--pilot",
                    str(PILOT_SURFACES[0]),
                    "--activation",
                    str(missing),
                    "--shadow",
                    str(shadow),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertFalse(output.exists())

    def test_prime_and_run_surfaces_keep_alpha_safety_boundaries(self):
        prime_paths = (
            ROOT / "src/skills/prime/SKILL.md",
            ROOT / "claude/skills/prime/SKILL.md",
            ROOT / "codex/plugin/skills/prime/SKILL.md",
        )
        run_paths = (
            ROOT / "src/skills/run/SKILL.md",
            ROOT / "claude/skills/run/SKILL.md",
            ROOT / "codex/plugin/skills/run/SKILL.md",
        )
        live_pilot_paths = (
            ROOT / "src/skills/prime/references/adaptive-assurance-live-pilot.md",
            ROOT / "claude/skills/prime/references/adaptive-assurance-live-pilot.md",
            ROOT / "codex/plugin/skills/prime/references/adaptive-assurance-live-pilot.md",
        )
        self.assertEqual(
            prime_paths[0].read_text(encoding="utf-8"),
            prime_paths[2].read_text(encoding="utf-8"),
        )
        self.assertEqual(markdown_body(prime_paths[0]), markdown_body(prime_paths[1]))
        self.assertEqual(
            run_paths[0].read_text(encoding="utf-8"),
            run_paths[2].read_text(encoding="utf-8"),
        )
        self.assertEqual(markdown_body(run_paths[0]), markdown_body(run_paths[1]))
        self.assertEqual(1, len({path.read_text(encoding="utf-8") for path in live_pilot_paths}))
        prime = prime_paths[0].read_text(encoding="utf-8")
        run = run_paths[0].read_text(encoding="utf-8")
        live_pilot = live_pilot_paths[0].read_text(encoding="utf-8")
        prime_norm = normalized(prime)
        run_norm = normalized(run)
        live_pilot_norm = normalized(live_pilot)
        self.assertIn("skips only this dispatch", prime_norm)
        self.assertIn("3-doc gate remains mandatory", prime_norm)
        self.assertIn("Full Assurance is the default", run_norm)
        self.assertIn("existing direct route", run_norm)
        self.assertIn("One fresh leaf reviews the full base diff", run_norm)
        self.assertIn("promotes monotonically to Full", run_norm)
        self.assertIn("default-off", live_pilot_norm)
        self.assertIn("never a third live execution path", live_pilot_norm)


if __name__ == "__main__":
    unittest.main()
