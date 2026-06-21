import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LeanforgeRenameContractTests(unittest.TestCase):
    def test_plugin_identity_is_leanforge_with_colon_display_calls(self):
        codex_manifest = json.loads((ROOT / "platform/codex/plugin.json").read_text(encoding="utf-8"))
        claude_manifest = json.loads((ROOT / "platform/claude/plugin.json").read_text(encoding="utf-8"))

        self.assertEqual("leanforge", codex_manifest["name"])
        self.assertEqual("leanforge", claude_manifest["name"])
        self.assertEqual("Leanforge", codex_manifest["interface"]["displayName"])

        prompts = "\n".join(codex_manifest["interface"]["defaultPrompt"])
        for call in ("Leanforge:Prime", "Leanforge:Run", "Leanforge:Harness"):
            self.assertIn(call, prompts)

    def test_codex_skill_display_names_are_colon_names(self):
        expected = {
            "prime": "Leanforge:Prime",
            "run": "Leanforge:Run",
            "set": "Leanforge:Set",
            "harness": "Leanforge:Harness",
            "run-tdd": "Leanforge:Run TDD",
        }
        for skill, display_name in expected.items():
            with self.subTest(skill=skill):
                yaml_text = (ROOT / f"platform/codex/skills/{skill}/agents/openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f'display_name: "{display_name}"', yaml_text)

    def test_old_skill_directories_are_not_part_of_sources_or_packages(self):
        old_skill_names = ("ready", "go", "migration", "dryforge-go-tdd")
        roots = (
            ROOT / "src/skills",
            ROOT / "platform/codex/skills",
            ROOT / "claude/skills",
            ROOT / "codex/plugin/skills",
        )
        for root in roots:
            for skill in old_skill_names:
                with self.subTest(root=root, skill=skill):
                    self.assertFalse((root / skill).exists())

    def test_local_state_directory_stays_backward_compatible(self):
        combined = "\n".join(
            [
                (ROOT / "src/skills/prime/SKILL.md").read_text(encoding="utf-8"),
                (ROOT / "src/skills/run/SKILL.md").read_text(encoding="utf-8"),
                (ROOT / "src/skills/set/SKILL.md").read_text(encoding="utf-8"),
            ]
        )
        self.assertIn(".dryforge/status.json", combined)
        self.assertIn(".dryforge/run.json", combined)
        self.assertNotIn("__" + "LEANFORGE", combined)


if __name__ == "__main__":
    unittest.main()
