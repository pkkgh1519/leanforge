import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class ReadyScoutContractTests(unittest.TestCase):
    def test_ready_scout_reference_exists_on_all_surfaces(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                body = read(f"{surface}/ready/references/evidence-grounding-scout.md")
                self.assertIn("evidence-grounding scout", body)

    def test_ready_scout_reference_matches_generated_surfaces(self):
        src = read("src/skills/ready/references/evidence-grounding-scout.md")
        self.assertEqual(src, read("codex/plugin/skills/ready/references/evidence-grounding-scout.md"))
        self.assertEqual(src, read("claude/skills/ready/references/evidence-grounding-scout.md"))

    def test_ready_scout_boundary_contract_on_all_surfaces(self):
        required = [
            "optional evidence-grounding scout",
            "read-only repo-evidence QA",
            "after ORIENT",
            "main ready remains the authority",
            "evidence pointers only",
            "must not set product intent",
            "must not write the spec",
            "must not design the plan",
            "must not make decisions",
            "must not ask the user",
            "No recursive delegation",
            "One dispatch max",
            "DECOMPOSE or ELICIT",
            "not a go repo-local lens",
            "do not invoke harness-generated repo-local skills",
            "do not invoke custom agents as scout",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/ready/SKILL.md"),
                        read(f"{surface}/ready/references/evidence-grounding-scout.md"),
                    ]
                )
                missing = [term for term in required if term not in combined]
                self.assertFalse(missing, f"missing ready scout boundary terms: {missing}")

    def test_ready_scout_trigger_and_skip_contract_on_all_surfaces(self):
        required = [
            "main ORIENT cheap-map completed",
            "material uncertainty",
            "skip for greenfield",
            "simple documentation-only",
            "small deltas",
            "ORIENT already has sufficient evidence",
            "source conflict candidate",
            "verify command candidate",
            "likely blast-radius candidate",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/ready/SKILL.md"),
                        read(f"{surface}/ready/references/evidence-grounding-scout.md"),
                    ]
                )
                missing = [term for term in required if term not in combined]
                self.assertFalse(missing, f"missing ready scout trigger/skip terms: {missing}")

    def test_ready_scout_replaces_unqualified_two_only_language(self):
        checked = [
            "ready/SKILL.md",
            "ready/references/3-doc-gate.md",
            "ready/references/gap-analysis.md",
            "ready/references/review-fidelity.md",
        ]
        forbidden = [
            "Subagents only at the two independent checks",
            "This and the 3-doc-gate are the only subagent dispatches",
            "one of the skill's two",
            "no subagent dispatch — those belong to the two independent checks",
            "subagents only at intent-completeness + 3-doc-gate",
        ]
        for surface in SURFACES:
            for rel in checked:
                with self.subTest(surface=surface, rel=rel):
                    body = read(f"{surface}/{rel}")
                    present = [term for term in forbidden if term in body]
                    self.assertFalse(present, f"stale two-only ready scout terms remain: {present}")

    def test_ready_scout_is_ready_only_and_does_not_relax_migration(self):
        required = [
            "ready-only optional ORIENT evidence scout",
            "does not change migration's inline-only contract",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/ready/SKILL.md"),
                        read(f"{surface}/ready/references/evidence-grounding-scout.md"),
                    ]
                )
                missing = [term for term in required if term not in combined]
                self.assertFalse(missing, f"missing ready-only migration boundary terms: {missing}")


if __name__ == "__main__":
    unittest.main()
