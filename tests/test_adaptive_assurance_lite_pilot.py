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
        "bounded_direct_execution": True,
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
        self.assertEqual(
            "required_before_intent_review_skip",
            prime["bounded_direct_execution"],
        )
        self.assertEqual(
            "required_mechanical_or_none", prime["plan_task_risk"]
        )
        self.assertEqual(
            "return_to_prime_review_reapprove_before_full_resume",
            prime["promotion_backfill"],
        )
        self.assertEqual("keep", prime["three_doc_gate"])
        self.assertEqual("keep", prime["user_approval"])
        self.assertEqual("existing_direct_route", run["execution"])
        self.assertEqual("full_once", run["completion_verification"])
        self.assertEqual("keep_bounded_lite_scope", run["final_independent_review"])
        self.assertEqual(
            "acceptance_diff_changed_paths_verification_promotion",
            run["final_review_scope"],
        )
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
                "bounded_direct_execution": True,
            },
            pilot_oracle.derive_profile(pilot, activation, lite_shadow()),
        )

    def test_profile_requires_bounded_direct_shadow_fact(self):
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))
        activation = {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": True}
        shadow = lite_shadow()
        shadow["bounded_direct_execution"] = False
        self.assertIsNone(pilot_oracle.derive_profile(pilot, activation, shadow))

    def test_schema_v1_shadow_missing_bounded_fact_is_stale_not_backward_accepted(self):
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))
        activation = {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": True}
        shadow = lite_shadow()
        del shadow["bounded_direct_execution"]
        with self.assertRaises(pilot_oracle.ContractError):
            pilot_oracle.derive_profile(pilot, activation, shadow)

    def test_plan_mutations_remove_profile_and_route_to_full_before_approval(self):
        profile = pilot_oracle.derive_profile(
            json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8")),
            {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": True},
            lite_shadow(),
        )
        self.assertIsNotNone(profile)
        eligible = {
            "task_count": 1,
            "task_risk": "MECHANICAL",
            "regeneration_barrier": False,
            "local_file_diff": True,
            "targeted_verification_sufficient": True,
        }
        self.assertEqual(
            {
                "route": "strict_lite",
                "profile_action": "keep",
                "intent_review": "skipped",
                "dependent_work": "allowed_after_approval",
                "approval": "required",
                "same_cycle_lite_reentry": "not_applicable",
            },
            pilot_oracle.evaluate_plan_profile(profile, eligible),
        )
        mutations = {
            "multiple_tasks": {**eligible, "task_count": 2},
            "omitted_risk": {key: value for key, value in eligible.items() if key != "task_risk"},
            "malformed_risk": {**eligible, "task_risk": ["MECHANICAL"]},
            "risky": {**eligible, "task_risk": "RISKY"},
            "regen_barrier": {**eligible, "regeneration_barrier": True},
            "verification_gap": {**eligible, "targeted_verification_sufficient": False},
        }
        expected = {
            "route": "full_assurance",
            "profile_action": "remove",
            "intent_review": "required_before_3doc_gate",
            "dependent_work": "forbidden_before_approval",
            "approval": "required",
            "same_cycle_lite_reentry": "forbidden",
        }
        for name, plan in mutations.items():
            with self.subTest(name=name):
                self.assertEqual(expected, pilot_oracle.evaluate_plan_profile(profile, plan))
        malformed_profile = {**profile, "bounded_direct_execution": 1}
        self.assertEqual(
            expected,
            pilot_oracle.evaluate_plan_profile(malformed_profile, eligible),
        )

    def test_runtime_promotion_halts_run_and_requires_prime_reapproval(self):
        pilot = json.loads(PILOT_SURFACES[0].read_text(encoding="utf-8"))
        profile = pilot_oracle.derive_profile(
            pilot,
            {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": True},
            lite_shadow(),
        )
        self.assertIsNotNone(profile)
        expected = {
            "route": "full_assurance",
            "profile_action": "remove",
            "run_action": "halt_and_preserve_state",
            "prime_action": "reenter_elicit_with_source_context",
            "intent_review": "required_before_spec",
            "three_doc_action": "regenerate_review_reapprove",
            "dependent_work": "forbidden_before_reapproval",
            "resume_profile": "full_assurance",
            "same_cycle_lite_reentry": "forbidden",
        }
        for trigger in (
            "verification_gap_discovered",
            "multiple_write_areas_discovered",
            "user_intent_conflict_discovered",
            "new_unknown_material_risk",
            None,
        ):
            with self.subTest(trigger=trigger):
                self.assertEqual(
                    expected,
                    pilot_oracle.derive_runtime_promotion(pilot, profile, trigger),
                )
        stale_profile = dict(profile)
        del stale_profile["bounded_direct_execution"]
        self.assertEqual(
            expected,
            pilot_oracle.derive_runtime_promotion(
                pilot, stale_profile, "profile_invalid_or_stale"
            ),
        )
        self.assertEqual(
            {
                "route": "full_assurance",
                "profile_action": "remove",
                "run_action": "halt_and_preserve_state",
                "prime_action": "await_original_prime_context_or_resupplied_source",
                "intent_review": "blocked_until_source_context",
                "three_doc_action": "forbid_reconstruction_from_approved_3doc",
                "dependent_work": "forbidden_before_reapproval",
                "resume_profile": "full_assurance_after_reapproval",
                "same_cycle_lite_reentry": "forbidden",
            },
            pilot_oracle.derive_runtime_promotion(
                pilot,
                profile,
                "verification_gap_discovered",
                source_context_available=False,
            ),
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

    def test_cli_removes_stale_profile_and_temp_for_every_fail_closed_input(self):
        enabled = {"schema_version": 1, "pilot": "strict_lite_alpha", "enabled": True}
        cases = (
            ("missing_activation", None, lite_shadow()),
            ("malformed_activation", {**enabled, "extra": True}, lite_shadow()),
            ("disabled", {**enabled, "enabled": False}, lite_shadow()),
            (
                "non_lite",
                enabled,
                {**lite_shadow(), "mode": "standard", "reasons": ["standard_default"]},
            ),
            (
                "not_bounded_direct",
                enabled,
                {**lite_shadow(), "bounded_direct_execution": False},
            ),
            (
                "stale_v1_missing_bounded_fact",
                enabled,
                {
                    key: value
                    for key, value in lite_shadow().items()
                    if key != "bounded_direct_execution"
                },
            ),
        )
        for name, activation_value, shadow_value in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                output = root / ".leanforge/assurance-profile.json"
                stale_tmp = output.with_name(output.name + ".tmp")
                output.parent.mkdir(parents=True)
                output.write_text('{"profile":"strict_lite_alpha"}\n', encoding="utf-8")
                stale_tmp.write_text("stale\n", encoding="utf-8")
                activation = root / "activation.json"
                shadow = root / "shadow.json"
                if activation_value is not None:
                    activation.write_text(
                        json.dumps(activation_value) + "\n", encoding="utf-8"
                    )
                shadow.write_text(json.dumps(shadow_value) + "\n", encoding="utf-8")
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(TOOL),
                        "--pilot",
                        str(PILOT_SURFACES[0]),
                        "--activation",
                        str(activation),
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
                self.assertFalse(stale_tmp.exists())

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
        self.assertIn("bounded direct execution", prime_norm)
        self.assertIn("risk must be `MECHANICAL` or `NONE`", prime)
        self.assertIn("3-doc gate remains mandatory", prime_norm)
        self.assertIn("Full Assurance is the default", run_norm)
        self.assertIn("existing direct route", run_norm)
        self.assertIn("One fresh leaf reviews the full base diff", run_norm)
        self.assertIn("bounded Lite final review", run_norm)
        self.assertIn("Halt and preserve the Run state", run_norm)
        self.assertIn("return to Prime", run_norm)
        self.assertIn("reapproval", run_norm)
        self.assertIn("Never reconstruct missing source context from the 3-doc", run_norm)
        self.assertIn("promotes monotonically to Full", run_norm)
        self.assertIn("default-off", live_pilot_norm)
        self.assertIn("`bounded_direct_execution` is `true`", live_pilot_norm)
        self.assertIn("never a third live execution path", live_pilot_norm)


if __name__ == "__main__":
    unittest.main()
