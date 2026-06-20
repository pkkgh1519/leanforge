import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class GoRepoLensContractTests(unittest.TestCase):
    def test_repo_lens_routing_reference_exists_on_all_surfaces(self):
        required_terms = [
            "repo-local skill",
            "final review",
            "conditional spec-review",
            "failure exploration",
            "MUST NOT replace implementer",
            "MUST NOT manage worktrees",
            "MUST NOT read .dryforge active docs",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                body = read(f"{surface}/go/references/repo-lens-routing.md")
                missing = [term for term in required_terms if term not in body]
                self.assertFalse(missing, f"missing repo lens contract terms: {missing}")

    def test_go_references_repo_lens_routing_without_yielding_execution_authority(self):
        required_terms = [
            "repo-lens-routing.md",
            "go keeps execution authority",
            "review/explore/checklist lens",
            "not an implementer",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/go/SKILL.md"),
                        read(f"{surface}/go/references/reviewer-prompt.md"),
                        read(f"{surface}/go/references/spec-review-prompt.md"),
                    ]
                )
                missing = [term for term in required_terms if term not in combined]
                self.assertFalse(missing, f"missing go repo lens references: {missing}")

    def test_omitted_risk_is_unclassified_not_direct_mechanical_path(self):
        forbidden = "Orchestrator-direct (`MECHANICAL` / `NONE` / omitted, file-diff task)"
        required = "Omitted `risk` remains unclassified, not `MECHANICAL`"
        for surface in SURFACES:
            with self.subTest(surface=surface):
                orchestration = read(f"{surface}/go/references/orchestration.md")
                self.assertNotIn(forbidden, orchestration)
                self.assertIn(required, orchestration)


if __name__ == "__main__":
    unittest.main()
