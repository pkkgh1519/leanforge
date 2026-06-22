import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class RunRepoLensContractTests(unittest.TestCase):
    def test_repo_lens_routing_reference_exists_on_all_surfaces(self):
        required_terms = [
            "repo-local skill",
            "final review",
            "conditional spec-review",
            "failure exploration",
            "MUST NOT replace implementer",
            "MUST NOT manage worktrees",
            "MUST NOT read .leanforge active docs",
            "legacy .dryforge",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                body = read(f"{surface}/run/references/repo-lens-routing.md")
                missing = [term for term in required_terms if term not in body]
                self.assertFalse(missing, f"missing repo lens contract terms: {missing}")

    def test_run_references_repo_lens_routing_without_yielding_execution_authority(self):
        required_terms = [
            "repo-lens-routing.md",
            "Run keeps execution authority",
            "review/explore/checklist lens",
            "not an implementer",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/run/SKILL.md"),
                        read(f"{surface}/run/references/reviewer-prompt.md"),
                        read(f"{surface}/run/references/spec-review-prompt.md"),
                    ]
                )
                missing = [term for term in required_terms if term not in combined]
                self.assertFalse(missing, f"missing Run repo lens references: {missing}")


    def test_legacy_delegation_surface_is_absent_from_skill_surfaces(self):
        forbidden = [
            "custom" + " agent",
            "custom-" + "agent",
            "." + "codex/" + "agents",
            "." + "codex/" + "config.toml",
        ]
        checked = [
            "README.md",
            "README_KO.md",
            "docs/harness/harness-skill-improvement-plan.md",
        ]
        for surface in SURFACES:
            root = ROOT / surface
            checked.extend(
                str(path.relative_to(ROOT)).replace("\\", "/")
                for path in root.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            )
        for rel in checked:
            with self.subTest(rel=rel):
                body = read(rel).lower()
                present = [term for term in forbidden if term in body]
                self.assertFalse(present, f"removed delegation surface terms remain: {present}")

    def test_omitted_risk_is_unclassified_not_direct_mechanical_path(self):
        forbidden = "Orchestrator-direct (`MECHANICAL` / `NONE` / omitted, file-diff task)"
        required = "Omitted `risk` remains unclassified, not `MECHANICAL`"
        for surface in SURFACES:
            with self.subTest(surface=surface):
                orchestration = read(f"{surface}/run/references/orchestration.md")
                self.assertNotIn(forbidden, orchestration)
                self.assertIn(required, orchestration)


if __name__ == "__main__":
    unittest.main()
