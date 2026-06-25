import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def collapsed(rel: str) -> str:
    return " ".join(read(rel).split())


def markdown_body(rel: str) -> str:
    text = read(rel)
    if text.startswith("---\n"):
        return text.split("---\n", 2)[2]
    return text


class SddLiteStage1ContractTests(unittest.TestCase):
    def assertTermsPresent(self, body: str, terms: list[str], context: str):
        normalized = " ".join(body.split())
        missing = [term for term in terms if term not in normalized]
        self.assertFalse(missing, f"missing {context}: {missing}")

    def test_prime_defines_behavior_scoped_acceptance_evidence_matrix(self):
        required = [
            "Acceptance & Evidence Matrix",
            "behavior-changing work only",
            "externally observable behavior",
            "documentation-only",
            "mechanical wiring",
            "pure scaffold work with no user-observable behavior",
            "Verification",
            "Expected evidence",
            "never let missing verification read as a pass",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                body = read(f"{surface}/prime/references/output-format.md")
                self.assertTermsPresent(body, required, "Prime SDD-lite matrix terms")

    def test_run_implementer_requires_ac_evidence_without_shallow_evidence(self):
        required = [
            "Acceptance & Evidence Matrix",
            "AC id",
            "acceptance_evidence",
            "File existence",
            "source-string checks",
            "symbol existence",
            "skipped tests",
            "weakened assertions",
            "swallowed exceptions",
            "not valid behavior AC evidence",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                body = read(f"{surface}/run/references/implementer-prompt.md")
                self.assertTermsPresent(body, required, "Run implementer AC evidence terms")

    def test_run_reviewer_has_evidence_integrity_and_ceremony_budget_lenses(self):
        required = [
            "Evidence integrity sub-lens",
            "Acceptance & Evidence Matrix",
            "behavior AC",
            "source-string checks",
            "weakened assertions",
            "Ceremony budget sub-lens",
            "one-use",
            "owner/contract/policy/result",
            "Do not demand removal automatically",
            "load-bearing reason",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                body = read(f"{surface}/run/references/reviewer-prompt.md")
                self.assertTermsPresent(body, required, "Run reviewer SDD-lite lens terms")

    def test_run_tdd_is_behavior_first_and_ac_derived_on_codex_surface(self):
        required = [
            "Acceptance & Evidence Matrix",
            "derive each TDD slice",
            "observable behavior",
            "smallest stable public surface",
            "File existence",
            "source-string checks",
            "skipped tests",
            "weakened assertions",
            "do not count as AC evidence",
        ]
        for rel in (
            "platform/codex/skills/run-tdd/SKILL.md",
            "codex/plugin/skills/run-tdd/SKILL.md",
        ):
            with self.subTest(rel=rel):
                body = collapsed(rel)
                missing = [term for term in required if term not in body]
                self.assertFalse(missing, f"missing run-tdd SDD-lite terms: {missing}")

    def test_stage1_generated_surfaces_match_sources_exactly(self):
        exact_pairs = [
            ("src/skills/prime/references/output-format.md", "codex/plugin/skills/prime/references/output-format.md"),
            ("src/skills/prime/references/output-format.md", "claude/skills/prime/references/output-format.md"),
            ("src/skills/run/SKILL.md", "codex/plugin/skills/run/SKILL.md"),
            ("src/skills/run/references/implementer-prompt.md", "codex/plugin/skills/run/references/implementer-prompt.md"),
            ("src/skills/run/references/implementer-prompt.md", "claude/skills/run/references/implementer-prompt.md"),
            ("src/skills/run/references/reviewer-prompt.md", "codex/plugin/skills/run/references/reviewer-prompt.md"),
            ("src/skills/run/references/reviewer-prompt.md", "claude/skills/run/references/reviewer-prompt.md"),
            ("platform/codex/skills/run-tdd/SKILL.md", "codex/plugin/skills/run-tdd/SKILL.md"),
        ]
        for source, generated in exact_pairs:
            with self.subTest(source=source, generated=generated):
                self.assertEqual(read(source), read(generated))
        self.assertEqual(markdown_body("src/skills/run/SKILL.md"), markdown_body("claude/skills/run/SKILL.md"))

    def test_stage1_non_goals_remain_documented(self):
        body = read("docs/harness/sdd-lite-stage-1-roadmap.md")
        forbidden_from_scope = [
            "Do not add Workboard support.",
            "Do not add committed spec snapshots.",
            "Do not change `Leanforge:Set` for this stage.",
            "Do not force the new matrix for documentation-only, mechanical, formatting-only, or scaffold-only work.",
        ]
        missing = [term for term in forbidden_from_scope if term not in body]
        self.assertFalse(missing, f"missing Stage 1 non-goals: {missing}")

    def test_behavior_change_scenario_has_end_to_end_ac_evidence_path(self):
        """Smoke scenario: a behavior-changing feature can carry AC evidence from Prime to Run review."""
        prime = read("src/skills/prime/references/output-format.md")
        implementer = read("src/skills/run/references/implementer-prompt.md")
        reviewer = " ".join(read("src/skills/run/references/reviewer-prompt.md").split())
        run_tdd = " ".join(read("platform/codex/skills/run-tdd/SKILL.md").split())

        self.assertTermsPresent(
            prime,
            [
                "Acceptance & Evidence Matrix (behavior-changing work only)",
                "| AC | Observable behavior | Non-goal / exclusion | Verification | Expected evidence |",
                "externally observable behavior",
                "never let missing verification read as a pass",
            ],
            "Prime behavior-change AC matrix smoke terms",
        )
        self.assertTermsPresent(
            implementer,
            [
                "pass the relevant AC ids and rows inline",
                "each relevant behavior AC has matching evidence",
                "map each relevant AC to the command/result that proves it",
                "`acceptance_evidence`",
                "not valid behavior AC evidence",
            ],
            "Run implementer behavior-change evidence smoke terms",
        )
        self.assertTermsPresent(
            reviewer,
            [
                "every behavior AC must trace to real evidence",
                "command plus exit code",
                "observed response",
                "blocking when used as the only evidence",
            ],
            "Run reviewer behavior-change evidence smoke terms",
        )
        self.assertTermsPresent(
            run_tdd,
            [
                "derive each TDD slice",
                "relevant AC's observable behavior",
                "smallest stable public surface",
                "do not count as AC evidence",
            ],
            "Run TDD behavior-change smoke terms",
        )

    def test_non_behavioral_scenario_stays_lightweight(self):
        """Smoke scenario: docs/config/scaffold work is not forced through the behavior matrix or TDD."""
        prime = read("src/skills/prime/references/output-format.md")
        run_tdd = read("platform/codex/skills/run-tdd/SKILL.md")
        roadmap = read("docs/harness/sdd-lite-stage-1-roadmap.md")

        self.assertTermsPresent(
            prime,
            [
                "Do not write this matrix for documentation-only",
                "mechanical wiring",
                "simple configuration",
                "pure scaffold work with no user-observable behavior",
                "smallest meaningful non-behavioral verification",
            ],
            "Prime non-behavior smoke terms",
        )
        self.assertTermsPresent(
            run_tdd,
            [
                "Do not force TDD for tasks that are not behavior changes",
                "documentation-only changes",
                "mechanical import/path wiring",
                "simple configuration changes",
                "scaffolding with no user-observable behavior yet",
                "smallest meaningful verification",
            ],
            "Run TDD non-behavior smoke terms",
        )
        self.assertTermsPresent(
            roadmap,
            [
                "Keep the matrix compact and omit it for non-behavioral work",
                "use a short non-matrix verification note instead",
                "Do not change `Leanforge:Set` for this stage.",
            ],
            "Stage 1 roadmap non-behavior smoke terms",
        )

    def test_over_engineering_scenario_is_reviewed_without_auto_rewrite_pressure(self):
        """Smoke scenario: reviewers can flag needless structure without forcing broad rewrites."""
        reviewer = read("src/skills/run/references/reviewer-prompt.md")

        self.assertTermsPresent(
            reviewer,
            [
                "Ceremony budget sub-lens",
                "one-use",
                "owner/contract/policy/result",
                "type names that add no validation",
                "interfaces with one implementation",
                "abstractions added before repeated use",
                "Do not demand removal automatically",
                "require a load-bearing reason",
                "advisory or blocking based on the maintenance risk",
            ],
            "ceremony budget smoke terms",
        )


if __name__ == "__main__":
    unittest.main()
