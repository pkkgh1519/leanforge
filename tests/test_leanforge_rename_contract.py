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
        for call in ("/leanforge:prime", "/leanforge:run"):
            self.assertIn(call, prompts)
        self.assertNotIn("/leanforge:harness", prompts)

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
            "/leanforge:harness",
            "Leanforge:Harness",
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
            "run-tdd": "Leanforge:Run TDD",
        }
        for skill, display_name in expected.items():
            with self.subTest(skill=skill):
                yaml_text = (ROOT / f"platform/codex/skills/{skill}/agents/openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f'display_name: "{display_name}"', yaml_text)

    def test_retired_harness_command_is_absent_from_current_surfaces(self):
        checked = {ROOT / "README.md", ROOT / "README_KO.md"}
        for rel in ("docs", "src/skills", "platform", "claude/skills", "codex/plugin"):
            checked.update(
                path
                for path in (ROOT / rel).rglob("*")
                if path.is_file() and path.suffix in {".md", ".json", ".yaml", ".yml"}
            )

        for path in sorted(checked):
            with self.subTest(rel=path.relative_to(ROOT)):
                body = path.read_text(encoding="utf-8")
                self.assertNotIn("/leanforge:harness", body)
                self.assertNotIn("Leanforge:Harness", body)

    def test_retired_skill_directories_are_not_part_of_sources_or_packages(self):
        old_skill_names = ("ready", "go", "migration", "dryforge-go-tdd", "harness")
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

    def test_project_harness_contracts_remain_in_core_skills(self):
        required = (
            "src/skills/run/references/harness-format.md",
            "src/skills/run/references/harness-lifecycle.md",
            "src/skills/run/references/harness-review.md",
            "src/skills/set/references/harness-format.md",
            "src/skills/set/references/harness-review.md",
        )
        for rel in required:
            with self.subTest(rel=rel):
                self.assertTrue((ROOT / rel).is_file())

    def test_readme_project_harness_tree_excludes_retired_meta_harness_output(self):
        for rel in ("README.md", "README_KO.md"):
            with self.subTest(rel=rel):
                body = (ROOT / rel).read_text(encoding="utf-8")
                self.assertNotIn("│   ├── harness/", body)

    def test_set_blocks_active_canonical_run_before_any_write(self):
        heading = "- **Active canonical state preflight — before any write.**"
        required = (
            "`.leanforge/run.json`",
            "`in_progress`",
            "`awaiting_user_approval`",
            "`archive_in_progress`",
            "`.leanforge/handoff.md`",
            "`.leanforge/spec.md`",
            "`.leanforge/plan.md`",
            "`.leanforge/worktrees/`",
            "stop without modifying the repository",
            "resume, finish, abandon, or recover",
            "Do not write `.leanforge/status.json`, harness/entry files, `.leanforge/backup/`, or `.gitignore`",
            "`completed` or `abandoned` stale marker alone",
            "unreadable marker, unknown status, or inconsistent state",
        )

        for surface in ("src/skills", "codex/plugin/skills", "claude/skills"):
            with self.subTest(surface=surface):
                body = (ROOT / surface / "set/SKILL.md").read_text(encoding="utf-8")
                start = body.find(heading)
                legacy = body.find("- **Legacy state preflight.**")
                phase_one = body.find("## Phase 1")

                self.assertGreaterEqual(start, 0, "missing canonical active-state guard")
                self.assertGreater(legacy, start, "canonical guard must precede legacy migration")
                self.assertGreater(phase_one, legacy, "all state preflights must precede Phase 1")

                contract = " ".join(body[start:legacy].split())
                missing = [term for term in required if term not in contract]
                self.assertFalse(missing, f"missing canonical guard terms: {missing}")

    def test_each_skill_blocks_migration_of_legacy_active_root_3doc(self):
        for surface in ("src/skills", "codex/plugin/skills", "claude/skills"):
            with self.subTest(surface=surface):
                body = (ROOT / surface / "set/SKILL.md").read_text(encoding="utf-8")
                preflight = re.search(
                    r"(?ms)- \*\*Legacy state preflight\.\*\*(.*?)(?=\n\n## Phase 1)",
                    body,
                )
                self.assertIsNotNone(preflight)
                contract = " ".join(preflight.group(1).split())
                self.assertIn("root active 3-doc", contract)
                self.assertIn("active `run.json`", contract)
                self.assertIn("`worktrees/`", contract)
                self.assertIn("do not migrate", contract)

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
