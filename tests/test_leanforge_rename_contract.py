import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def user_facing_markdown_files():
    files = [ROOT / "README.md", ROOT / "README_KO.md"]
    files.extend(sorted(ROOT.glob("docs/*.md")))
    files.extend(sorted(ROOT.glob("examples/**/*.md")))
    for rel in ("CONTRIBUTING.md", "SECURITY.md", "SUPPORT.md"):
        path = ROOT / rel
        if path.exists():
            files.append(path)
    return files


class LeanforgeRenameContractTests(unittest.TestCase):
    def test_plugin_identity_is_leanforge_with_colon_display_calls(self):
        codex_manifest = json.loads((ROOT / "platform/codex/plugin.json").read_text(encoding="utf-8"))
        claude_manifest = json.loads((ROOT / "platform/claude/plugin.json").read_text(encoding="utf-8"))

        self.assertEqual("leanforge", codex_manifest["name"])
        self.assertEqual("leanforge", claude_manifest["name"])
        self.assertEqual("Leanforge", codex_manifest["interface"]["displayName"])
        self.assertNotIn("homepage", codex_manifest)
        self.assertEqual("https://github.com/pkkgh1519/leanforge", codex_manifest["repository"])
        self.assertEqual("pkkgh1519", codex_manifest["author"]["name"])
        self.assertEqual("pkkgh1519", codex_manifest["interface"]["developerName"])
        self.assertEqual("pkkgh1519", claude_manifest["author"]["name"])

        prompts = "\n".join(codex_manifest["interface"]["defaultPrompt"])
        for call in ("/leanforge:prime", "/leanforge:run", "/leanforge:harness"):
            self.assertIn(call, prompts)

    def test_docs_use_leanforge_distribution_path_without_homepage_site(self):
        for rel in ("README.md", "README_KO.md"):
            with self.subTest(rel=rel):
                body = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn("pkkgh1519/leanforge", body)
                self.assertNotIn("fn-opt/leanforge", body)
                self.assertNotIn("fn-opt/dryforge", body)
                self.assertNotIn("dryforge.vercel.app", body)
                self.assertNotIn("Website (legacy URL)", body)
                self.assertIn("leanforge", body)
                self.assertIn("Distribution:" if rel == "README.md" else "배포:", body)

    def test_user_facing_markdown_avoids_legacy_distribution_artifacts(self):
        forbidden = (
            "fn-opt/leanforge",
            "fn-opt/dryforge",
            "dryforge.vercel.app",
            "Website (legacy URL)",
            "/leanforge:herness",
            "harness:*",
        )
        for path in user_facing_markdown_files():
            rel = path.relative_to(ROOT)
            body = path.read_text(encoding="utf-8")
            for value in forbidden:
                with self.subTest(rel=rel, value=value):
                    self.assertNotIn(value, body)

    def test_user_facing_markdown_links_are_resolvable(self):
        for path in user_facing_markdown_files():
            rel = path.relative_to(ROOT)
            body = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", body):
                if target.startswith(("http://", "https://")):
                    continue
                with self.subTest(rel=rel, target=target):
                    self.assertTrue((path.parent / target).exists())

    def test_marketplace_metadata_does_not_declare_homepage_site(self):
        claude_marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual("pkkgh1519", claude_marketplace["owner"]["name"])
        self.assertEqual("pkkgh1519", claude_marketplace["plugins"][0]["author"]["name"])
        self.assertNotIn("homepage", claude_marketplace["plugins"][0])

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

    def test_readme_uses_harness_slash_command(self):
        for rel in ("README.md", "README_KO.md"):
            with self.subTest(rel=rel):
                body = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn("/leanforge:harness", body)
                self.assertNotIn("harness:*", body)
                self.assertNotIn("/leanforge:herness", body)

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

    def test_local_state_directory_is_leanforge_with_guarded_legacy_migration(self):
        combined = "\n".join(
            [
                (ROOT / "src/skills/prime/SKILL.md").read_text(encoding="utf-8"),
                (ROOT / "src/skills/run/SKILL.md").read_text(encoding="utf-8"),
                (ROOT / "src/skills/set/SKILL.md").read_text(encoding="utf-8"),
                (ROOT / "src/skills/run/references/harness-lifecycle.md").read_text(encoding="utf-8"),
            ]
        )
        self.assertIn(".leanforge/status.json", combined)
        self.assertIn(".leanforge/run.json", combined)
        self.assertIn('schema": "leanforge.stateMigration.v1"', combined)
        self.assertIn(".dryforge/run.json", combined)
        self.assertIn(".dryforge/worktrees/", combined)
        self.assertIn("do **not** rename the directory", combined)
        self.assertNotIn("__" + "LEANFORGE", combined)

    def test_target_repo_gitignore_ignores_canonical_and_legacy_state(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".leanforge/", ignore)
        self.assertIn(".dryforge/", ignore)


if __name__ == "__main__":
    unittest.main()
