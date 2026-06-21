import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class PrimeScoutContractTests(unittest.TestCase):
    def test_prime_scout_reference_exists_on_all_surfaces(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                body = read(f"{surface}/prime/references/evidence-grounding-scout.md")
                self.assertIn("evidence-grounding scout", body)

    def test_ready_scout_reference_matches_generated_surfaces(self):
        src = read("src/skills/prime/references/evidence-grounding-scout.md")
        self.assertEqual(src, read("codex/plugin/skills/prime/references/evidence-grounding-scout.md"))
        self.assertEqual(src, read("claude/skills/prime/references/evidence-grounding-scout.md"))

    def test_prime_scout_boundary_contract_on_all_surfaces(self):
        required = [
            "optional evidence-grounding scout",
            "read-only repo-evidence QA",
            "after ORIENT",
            "main Prime remains the authority",
            "evidence pointers only",
            "must not set product intent",
            "must not write the spec",
            "must not design the plan",
            "must not make decisions",
            "must not ask the user",
            "No recursive delegation",
            "One dispatch max",
            "DECOMPOSE or ELICIT",
            "not a Run repo-local lens",
            "do not invoke harness-generated repo-local skills",
            "do not invoke custom agents as scout",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/prime/SKILL.md"),
                        read(f"{surface}/prime/references/evidence-grounding-scout.md"),
                    ]
                )
                missing = [term for term in required if term not in combined]
                self.assertFalse(missing, f"missing Prime scout boundary terms: {missing}")

    def test_prime_scout_trigger_and_skip_contract_on_all_surfaces(self):
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
                        read(f"{surface}/prime/SKILL.md"),
                        read(f"{surface}/prime/references/evidence-grounding-scout.md"),
                    ]
                )
                missing = [term for term in required if term not in combined]
                self.assertFalse(missing, f"missing Prime scout trigger/skip terms: {missing}")

    def test_prime_scout_replaces_unqualified_two_only_language(self):
        checked = [
            "prime/SKILL.md",
            "prime/references/3-doc-gate.md",
            "prime/references/gap-analysis.md",
            "prime/references/review-fidelity.md",
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
                    self.assertFalse(present, f"stale two-only Prime scout terms remain: {present}")

    def test_prime_scout_is_prime_only_and_does_not_relax_set(self):
        required = [
            "Prime-only optional ORIENT evidence scout",
            "does not change Set's inline-only contract",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/prime/SKILL.md"),
                        read(f"{surface}/prime/references/evidence-grounding-scout.md"),
                    ]
                )
                missing = [term for term in required if term not in combined]
                self.assertFalse(missing, f"missing Prime-only Set boundary terms: {missing}")


if __name__ == "__main__":
    unittest.main()
