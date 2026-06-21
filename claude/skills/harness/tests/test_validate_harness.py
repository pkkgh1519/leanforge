import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "validate_harness.py"

spec = importlib.util.spec_from_file_location("validate_harness", VALIDATOR)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ValidateHarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-validator-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_skill(
        self,
        path: Path,
        *,
        body: str = "",
        reference: str | None = None,
        name: str = "sample-skill",
        description: str = "Use when validating a sample harness skill.",
    ) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        references = path / "references"
        references.mkdir(exist_ok=True)
        if reference is not None:
            (references / "guide.md").write_text(reference, encoding="utf-8")
            body = body or "See references/guide.md.\n"
        (path / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# Sample\n\n" + body,
            encoding="utf-8",
        )
        return path

    def issue_codes(self, result):
        errors, warnings = result
        return {issue.code for issue in [*errors, *warnings]}

    def add_claude_frontmatter_injection(self, skill: Path) -> None:
        path = skill / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "\n---\n\n# Sample",
            "\ndisable-model-invocation: true\nallowed-tools: Read, Edit, Write, Bash, Grep, Glob, Agent, AskUserQuestion\n---\n\n# Sample",
            1,
        )
        path.write_text(text, encoding="utf-8")

    def test_clean_skill_dir_validates(self):
        skill = self.write_skill(self.tmp / "sample-skill", reference="# Guide\n")
        errors, warnings = module.validate_skill_dir(skill)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_reference_is_error(self):
        skill = self.write_skill(self.tmp / "sample-skill", body="See references/missing.md.\n")
        self.assertIn("skill-reference-missing", self.issue_codes(module.validate_skill_dir(skill)))

    def test_fixed_model_pin_is_error(self):
        skill = self.write_skill(self.tmp / "sample-skill", reference="Use gpt-9 for this role.\n")
        self.assertIn("fixed-model-pin", self.issue_codes(module.validate_skill_dir(skill)))

    def test_peer_runtime_messaging_is_error(self):
        skill = self.write_skill(self.tmp / "sample-skill", reference="Agents coordinate through send_message.\n")
        self.assertIn("runtime-peer-messaging", self.issue_codes(module.validate_skill_dir(skill)))

    def test_custom_agent_missing_required_field(self):
        repo = self.tmp / "repo"
        agent_dir = repo / ".codex" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "reviewer.toml").write_text('name = "reviewer"\ndescription = "Review."\n', encoding="utf-8")
        self.assertIn("custom-agent-field-missing", self.issue_codes(module.validate(repo)))

    def test_custom_agent_reserved_builtin_name_is_error(self):
        repo = self.tmp / "repo"
        agent_dir = repo / ".codex" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "reviewer.toml").write_text(
            'name = "reviewer"\n'
            'description = "Review repository-specific API contracts."\n'
            'developer_instructions = """Return concise findings only."""\n',
            encoding="utf-8",
        )
        self.assertIn("custom-agent-name-reserved", self.issue_codes(module.validate(repo)))

    def test_run_compatible_skill_missing_usage_contract_is_error(self):
        skill = self.write_skill(
            self.tmp / "api-contract-review",
            name="api-contract-review",
            description="Use when Leanforge Run needs a repository API contract review lens.",
            body="Review API route, schema, client SDK, and generated type changes for Leanforge Run final_review.\n",
        )
        self.assertIn("run-compatible-skill-contract-missing", self.issue_codes(module.validate_skill_dir(skill)))

    def test_run_compatible_skill_disallows_active_leanforge_doc_dependency(self):
        for state_dir in (".leanforge", ".dryforge"):
            with self.subTest(state_dir=state_dir):
                skill = self.write_skill(
                    self.tmp / f"api-contract-review-{state_dir.strip('.')}",
                    name=f"api-contract-review-{state_dir.strip('.')}",
                    description="Use when Leanforge Run needs a repository API contract review lens.",
                    body=(
                        "## Leanforge Run usage\n\n"
                        "Allowed phases: final_review, conditional_spec_review, failure_exploration.\n"
                        "Never use for: implementer replacement, wave scheduling, merge gate, worktree lifecycle, .leanforge state management.\n"
                        "Inputs Run must provide: changed files, relevant spec slice, verification evidence, diff or commit range.\n"
                        "Output: blocking findings, advisory findings, missing evidence, uncertainty.\n\n"
                        f"Read {state_dir}/spec.md before reviewing.\n"
                    ),
                )
                self.assertIn("run-compatible-active-doc-dependency", self.issue_codes(module.validate_skill_dir(skill)))

    def test_run_compatible_skill_warns_on_broad_trigger(self):
        skill = self.write_skill(
            self.tmp / "api-contract-review",
            name="api-contract-review",
            description="Use for all API work in this repository, including ordinary implementation tasks.",
            body=(
                "## Leanforge Run usage\n\n"
                "Allowed phases: final_review, conditional_spec_review, failure_exploration.\n"
                "Never use for: implementer replacement, wave scheduling, merge gate, worktree lifecycle, .leanforge state management.\n"
                "Inputs Run must provide: changed files, relevant spec slice, verification evidence, diff or commit range.\n"
                "Output: blocking findings, advisory findings, missing evidence, uncertainty.\n"
            ),
        )
        self.assertIn("run-compatible-skill-trigger-too-broad", self.issue_codes(module.validate_skill_dir(skill)))

    def test_team_spec_missing_contract_section(self):
        repo = self.tmp / "repo"
        spec_dir = repo / "docs" / "harness" / "demo"
        spec_dir.mkdir(parents=True)
        (spec_dir / "team-spec.md").write_text("# Demo Team Spec\n\n## Purpose\n\nOnly purpose.\n", encoding="utf-8")
        self.assertIn("team-spec-contract-missing", self.issue_codes(module.validate(repo)))

    def test_long_agents_md_is_warning(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        (repo / "AGENTS.md").write_text("\n".join(f"line {idx}" for idx in range(251)), encoding="utf-8")
        errors, warnings = module.validate(repo)
        self.assertEqual(errors, [])
        self.assertIn("agents-md-long", {issue.code for issue in warnings})

    def test_install_check_validates_generated_parity_and_overlay(self):
        repo = self.tmp / "repo"
        source = self.write_skill(repo / "src" / "skills" / "harness", reference="# Guide\n")
        scripts = source / "scripts"
        scripts.mkdir()
        (scripts / "validate_harness.py").write_text("print('ok')\n", encoding="utf-8")
        claude = repo / "claude" / "skills" / "harness"
        codex = repo / "codex" / "plugin" / "skills" / "harness"
        shutil.copytree(source, claude)
        self.add_claude_frontmatter_injection(claude)
        shutil.copytree(source, codex)
        overlay = repo / "platform" / "codex" / "skills" / "harness" / "agents"
        overlay.mkdir(parents=True)
        (overlay / "openai.yaml").write_text("interface:\n  display_name: harness\n", encoding="utf-8")
        codex_agents = codex / "agents"
        codex_agents.mkdir()
        shutil.copy2(overlay / "openai.yaml", codex_agents / "openai.yaml")
        errors, warnings = module.validate_harness_install(repo)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_install_check_detects_generated_drift(self):
        repo = self.tmp / "repo"
        source = self.write_skill(repo / "src" / "skills" / "harness", reference="# Guide\n")
        scripts = source / "scripts"
        scripts.mkdir()
        (scripts / "validate_harness.py").write_text("print('ok')\n", encoding="utf-8")
        claude = repo / "claude" / "skills" / "harness"
        shutil.copytree(source, claude)
        self.add_claude_frontmatter_injection(claude)
        codex = repo / "codex" / "plugin" / "skills" / "harness"
        shutil.copytree(source, codex)
        (codex / "SKILL.md").write_text((codex / "SKILL.md").read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
        errors, _ = module.validate_harness_install(repo)
        self.assertIn("harness-generated-drift", {issue.code for issue in errors})

    def test_install_check_detects_generated_extra_file(self):
        repo = self.tmp / "repo"
        source = self.write_skill(repo / "src" / "skills" / "harness", reference="# Guide\n")
        scripts = source / "scripts"
        scripts.mkdir()
        (scripts / "validate_harness.py").write_text("print('ok')\n", encoding="utf-8")
        claude = repo / "claude" / "skills" / "harness"
        shutil.copytree(source, claude)
        self.add_claude_frontmatter_injection(claude)
        codex = repo / "codex" / "plugin" / "skills" / "harness"
        shutil.copytree(source, codex)
        (codex / "unexpected.md").write_text("extra\n", encoding="utf-8")
        errors, _ = module.validate_harness_install(repo)
        self.assertIn("harness-generated-extra", {issue.code for issue in errors})

    def test_install_check_detects_overlay_drift(self):
        repo = self.tmp / "repo"
        source = self.write_skill(repo / "src" / "skills" / "harness", reference="# Guide\n")
        scripts = source / "scripts"
        scripts.mkdir()
        (scripts / "validate_harness.py").write_text("print('ok')\n", encoding="utf-8")
        claude = repo / "claude" / "skills" / "harness"
        shutil.copytree(source, claude)
        self.add_claude_frontmatter_injection(claude)
        codex = repo / "codex" / "plugin" / "skills" / "harness"
        shutil.copytree(source, codex)
        overlay = repo / "platform" / "codex" / "skills" / "harness" / "agents"
        overlay.mkdir(parents=True)
        (overlay / "openai.yaml").write_text("interface:\n  display_name: harness\n", encoding="utf-8")
        codex_agents = codex / "agents"
        codex_agents.mkdir()
        (codex_agents / "openai.yaml").write_text("interface:\n  display_name: drift\n", encoding="utf-8")
        errors, _ = module.validate_harness_install(repo)
        self.assertIn("harness-overlay-drift", {issue.code for issue in errors})

    def test_install_check_detects_claude_frontmatter_drift(self):
        repo = self.tmp / "repo"
        source = self.write_skill(repo / "src" / "skills" / "harness", reference="# Guide\n")
        scripts = source / "scripts"
        scripts.mkdir()
        (scripts / "validate_harness.py").write_text("print('ok')\n", encoding="utf-8")
        claude = repo / "claude" / "skills" / "harness"
        shutil.copytree(source, claude)
        codex = repo / "codex" / "plugin" / "skills" / "harness"
        shutil.copytree(source, codex)
        errors, _ = module.validate_harness_install(repo)
        self.assertIn("harness-generated-frontmatter-drift", {issue.code for issue in errors})


if __name__ == "__main__":
    unittest.main()
