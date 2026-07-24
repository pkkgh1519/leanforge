import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class RunRecoveryContractTests(unittest.TestCase):
    def test_run_documents_run_marker_recovery_model(self):
        required_terms = [
            ".leanforge/run.json",
            "in_progress",
            "awaiting_user_approval",
            "archive_in_progress",
            "abandoned",
            "activeDocs",
            "handoffSha256",
            "specSha256",
            "planSha256",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                run = read(f"{surface}/run/SKILL.md")
                lifecycle = read(f"{surface}/run/references/harness-lifecycle.md")
                combined = run + "\n" + lifecycle
                missing = [term for term in required_terms if term not in combined]
                self.assertFalse(missing, f"missing recovery contract terms: {missing}")

    def test_run_preflight_distinguishes_interrupted_run_from_first_cycle(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                run = read(f"{surface}/run/SKILL.md")
                lifecycle = read(f"{surface}/run/references/harness-lifecycle.md")
                combined = run + "\n" + lifecycle

                self.assertIn("status.json absent + run.json present", combined)
                self.assertIn("interrupted Run run", combined)
                self.assertIn("not a first cycle", combined)

    def test_archive_retry_is_idempotent_and_hash_guarded(self):
        required = [
            "idempotent archive retry",
            "hash mismatch",
            "archive complete but marker missing",
            "root active 3-doc",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                lifecycle = read(f"{surface}/run/references/harness-lifecycle.md")
                missing = [term for term in required if term not in lifecycle]
                self.assertFalse(missing, f"missing archive safety terms: {missing}")

    def test_prime_warns_before_overwriting_active_run_or_docs(self):
        required = [
            ".leanforge/run.json",
            "active 3-doc",
            "do not overwrite",
            "resume or abandon",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                prime = read(f"{surface}/prime/SKILL.md")
                missing = [term for term in required if term not in prime]
                self.assertFalse(missing, f"missing Prime overwrite guard terms: {missing}")


    def test_generated_skill_surfaces_match_src_contract(self):
        claude_injected_lines = (
            "disable-model-invocation: true\n"
            "allowed-tools: Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion\n"
        )

        source_files = sorted(
            path.relative_to(ROOT / "src/skills")
            for path in (ROOT / "src/skills").rglob("*")
            if path.is_file()
        )
        for rel_path in source_files:
            rel = rel_path.as_posix()
            with self.subTest(surface="codex", rel=rel):
                self.assertEqual(read(f"src/skills/{rel}"), read(f"codex/plugin/skills/{rel}"))

        for rel_path in source_files:
            rel = rel_path.as_posix()
            with self.subTest(surface="claude", rel=rel):
                claude = read(f"claude/skills/{rel}")
                if rel_path.name == "SKILL.md":
                    self.assertIn(claude_injected_lines, claude)
                    claude = claude.replace(claude_injected_lines, "", 1)
                self.assertEqual(read(f"src/skills/{rel}"), claude)

    def test_Leanforge_ops_is_not_packaged(self):
        removed_paths = [
            ROOT / "src/skills/dryforge-ops",
            ROOT / "platform/codex/skills/dryforge-ops",
            ROOT / "claude/skills/dryforge-ops",
            ROOT / "codex/plugin/skills/dryforge-ops",
        ]
        for path in removed_paths:
            with self.subTest(path=path):
                self.assertFalse(path.exists())

    def test_codex_only_run_tdd_wrapper_is_packaged(self):
        codex_skill = ROOT / "codex/plugin/skills/run-tdd/SKILL.md"
        codex_agent = ROOT / "codex/plugin/skills/run-tdd/agents/openai.yaml"
        platform_skill = ROOT / "platform/codex/skills/run-tdd/SKILL.md"
        claude_skill = ROOT / "claude/skills/run-tdd/SKILL.md"

        self.assertTrue(platform_skill.exists())
        self.assertTrue(codex_skill.exists())
        self.assertTrue(codex_agent.exists())
        self.assertFalse(claude_skill.exists())

        body = codex_skill.read_text(encoding="utf-8")
        self.assertIn("Leanforge:Run remains the primary execution", body)
        self.assertIn("selective TDD guidance", body)
        self.assertIn("self-contained", body)
        self.assertIn("does not require a separately installed `tdd` skill", body)
        self.assertNotIn("Read the `tdd` `SKILL.md`", body)
        self.assertNotIn("standalone `tdd` skill's general advice", body)
        self.assertEqual(
            platform_skill.read_text(encoding="utf-8"),
            codex_skill.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
