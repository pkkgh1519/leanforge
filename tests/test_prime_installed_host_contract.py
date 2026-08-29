import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVOCATION_START = "<!-- leanforge:prime-invocation-precedence:start -->"
INVOCATION_END = "<!-- leanforge:prime-invocation-precedence:end -->"
FAST_PATH_START = "<!-- leanforge:prime-closed-input-fast-path:start -->"
FAST_PATH_END = "<!-- leanforge:prime-closed-input-fast-path:end -->"
FIRST_CYCLE_START = "<!-- leanforge:prime:FIRST-CYCLE-EVIDENCE-DISPOSITION:start -->"
FIRST_CYCLE_END = "<!-- leanforge:prime:FIRST-CYCLE-EVIDENCE-DISPOSITION:end -->"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def extract(document: str, start: str, end: str) -> str:
    if document.count(start) != 1 or document.count(end) != 1:
        return ""
    start_index = document.index(start) + len(start)
    end_index = document.index(end, start_index)
    return " ".join(document[start_index:end_index].split())


def validate_prime_contract(documents: dict[str, str]) -> list[str]:
    errors: list[str] = []
    prime = documents["src/skills/prime/SKILL.md"]
    invocation = extract(prime, INVOCATION_START, INVOCATION_END)
    fast_path = extract(prime, FAST_PATH_START, FAST_PATH_END)
    first_cycle = extract(
        documents["src/skills/prime/references/elicitation.md"],
        FIRST_CYCLE_START,
        FIRST_CYCLE_END,
    )

    required_invocation = (
        "Invoking the `Prime` skill is already the user's planning choice.",
        "do **not** request direct implementation",
        "never justify a Prime-versus-Run mode question",
        "Do not ask the user to choose Prime after the host has already invoked this skill.",
    )
    required_fast_path = (
        "ask **zero** questions",
        "explicit current-request intent",
        "authoritative repository evidence for an unchanged fact",
        "a reasoned `N/A`",
        "write `.leanforge/spec.md`, `.leanforge/plan.md`, and `.leanforge/handoff.md`",
        "do not return a questionnaire, workflow menu, or prose-only pseudo-contract instead",
    )
    required_first_cycle = (
        "Foundation artifact required; Foundation interview is not",
        "It does not erase project knowledge",
        "explicit user intent → authoritative repository evidence for unchanged current facts → reasoned `N/A`",
        "one user question only for a surviving load-bearing user-owned decision",
        "do not re-present them as greenfield choices",
        "evidence floors, not mandatory-question quotas",
    )

    for label, section, required in (
        ("invocation", invocation, required_invocation),
        ("closed-input", fast_path, required_fast_path),
        ("first-cycle", first_cycle, required_first_cycle),
    ):
        if not section:
            errors.append(f"missing or duplicate {label} contract section")
            continue
        missing = [term for term in required if term not in section]
        if missing:
            errors.append(f"{label} contract missing {missing}")

    required_prime_global = (
        "Explicit requirements and constraints in the current request are settled user intent",
        "unless they conflict with one another or are clearly marked",
        "never ask the user to reconfirm them",
    )
    missing_global = [term for term in required_prime_global if term not in " ".join(prime.split())]
    if missing_global:
        errors.append(f"Prime global invocation contract missing {missing_global}")

    forbidden_prime = (
        "If invocation also requests implementation",
        "ask whether to update planning documents or switch to Run/direct implementation",
        "Do not ask the user to choose Prime unless",
        "may still offer a generic mode menu",
        "unless manually accepted",
    )
    for phrase in forbidden_prime:
        if phrase in prime:
            errors.append(f"Prime contains fail-open or legacy phrase: {phrase}")

    references = {
        "src/skills/prime/references/project-scoping.md": (
            "confirmation only when needed",
            "record the evidence-backed read silently and continue",
            "Never ask the user to choose Prime/direct implementation",
        ),
        "src/skills/prime/references/project-design-domain.md": (
            "finish with zero questions",
            "ceremonial",
            "A new or changed product rule must come from the user's words or be one the user confirmed",
        ),
        "src/skills/prime/references/project-design-technical.md": (
            "must not be re-presented as a greenfield choice",
            "inventing a security interview",
            "Every **new or changed user-owned** technical decision is settled by user confirmation",
        ),
        "src/skills/prime/references/gap-analysis.md": (
            "the absence of user dialogue is not itself insufficiency",
            "ask only if a load-bearing user-owned gap survives",
        ),
        "src/skills/prime/references/intent-completeness.md": (
            "authoritative repository evidence",
            "reasoned `N/A`",
        ),
        "src/skills/prime/references/first-cycle-review.md": (
            "Question inflation",
            "zero** avoidable user questions",
        ),
        "src/skills/prime/references/foundation-format.md": (
            "zero foundation questions",
            "interview for unrelated hypothetical future scope",
        ),
    }
    for relative, required in references.items():
        body = " ".join(documents[relative].split())
        missing = [term for term in required if term not in body]
        if missing:
            errors.append(f"{relative} missing {missing}")

    codex_manifest = json.loads(documents["platform/codex/plugin.json"])
    prompts = "\n".join(codex_manifest["interface"]["defaultPrompt"])
    if "/leanforge:" in prompts:
        errors.append("Codex plugin default prompts advertise unsupported /leanforge:* commands")
    for skill in ("$prime", "$run"):
        if skill not in prompts:
            errors.append(f"Codex plugin default prompts missing {skill}")

    yaml_outcomes = {
        "prime": "Prepare an approval-ready change contract",
        "run": "Implement and verify the approved Leanforge change",
        "set": "Capture durable project context",
        "run-tdd": "Implement and verify the approved change with selective TDD",
    }
    for skill, outcome in yaml_outcomes.items():
        relative = f"platform/codex/skills/{skill}/agents/openai.yaml"
        body = documents[relative]
        if "/leanforge:" in body:
            errors.append(f"{relative} advertises unsupported /leanforge:* commands")
        if outcome not in body:
            errors.append(f"{relative} missing direct selected-skill outcome prompt")

    installation = documents["docs/installation.md"]
    troubleshooting = documents["docs/troubleshooting.md"]
    contracts = documents["docs/contracts.md"]
    for relative, body in (
        ("docs/installation.md", installation),
        ("docs/troubleshooting.md", troubleshooting),
        ("docs/contracts.md", contracts),
    ):
        for term in ("/skills", "$prime"):
            if term not in body:
                errors.append(f"{relative} missing Codex invocation term {term}")
    if "Claude Code와 Codex의 `/leanforge:prime`" in contracts:
        errors.append("contracts still claim a shared Claude/Codex slash command")
    if "they do not create `/leanforge:*` slash commands" not in installation:
        errors.append("installation does not state the Codex slash-command boundary")

    return errors


class PrimeInstalledHostContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = (
            "src/skills/prime/SKILL.md",
            "src/skills/prime/references/elicitation.md",
            "src/skills/prime/references/project-scoping.md",
            "src/skills/prime/references/project-design-domain.md",
            "src/skills/prime/references/project-design-technical.md",
            "src/skills/prime/references/gap-analysis.md",
            "src/skills/prime/references/intent-completeness.md",
            "src/skills/prime/references/first-cycle-review.md",
            "src/skills/prime/references/foundation-format.md",
            "platform/codex/plugin.json",
            "platform/codex/skills/prime/agents/openai.yaml",
            "platform/codex/skills/run/agents/openai.yaml",
            "platform/codex/skills/set/agents/openai.yaml",
            "platform/codex/skills/run-tdd/agents/openai.yaml",
            "docs/installation.md",
            "docs/troubleshooting.md",
            "docs/contracts.md",
        )
        cls.documents = {path: read(path) for path in cls.paths}

    def mutated(self, relative: str, old: str, new: str) -> dict[str, str]:
        documents = dict(self.documents)
        self.assertEqual(1, documents[relative].count(old), (relative, old))
        documents[relative] = documents[relative].replace(old, new)
        return documents

    def assert_rejected(self, documents: dict[str, str]) -> None:
        self.assertTrue(validate_prime_contract(documents))

    def test_current_contract_passes(self):
        self.assertEqual([], validate_prime_contract(self.documents))

    def test_codex_default_prompts_fit_host_limit_and_preserve_skill_routing(self):
        manifest = json.loads(self.documents["platform/codex/plugin.json"])
        prompts = manifest["interface"]["defaultPrompt"]

        self.assertTrue(prompts)
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertIsInstance(prompt, str)
                self.assertTrue(prompt.strip())
                self.assertLessEqual(len(prompt), 128)

        combined = "\n".join(prompts)
        for skill in ("$prime", "$run"):
            with self.subTest(skill=skill):
                self.assertIn(skill, combined)

    def test_generated_prime_contract_matches_canonical_after_build(self):
        canonical = read("src/skills/prime/SKILL.md")
        codex = read("codex/plugin/skills/prime/SKILL.md")
        claude = read("claude/skills/prime/SKILL.md")
        for start, end in (
            (INVOCATION_START, INVOCATION_END),
            (FAST_PATH_START, FAST_PATH_END),
        ):
            expected = extract(canonical, start, end)
            self.assertTrue(expected)
            self.assertEqual(expected, extract(codex, start, end))
            self.assertEqual(expected, extract(claude, start, end))

        expected_first = extract(read("src/skills/prime/references/elicitation.md"), FIRST_CYCLE_START, FIRST_CYCLE_END)
        for relative in (
            "codex/plugin/skills/prime/references/elicitation.md",
            "claude/skills/prime/references/elicitation.md",
        ):
            self.assertEqual(expected_first, extract(read(relative), FIRST_CYCLE_START, FIRST_CYCLE_END))

    def test_explicit_prime_can_not_be_mutated_back_into_mode_selection(self):
        self.assert_rejected(
            self.mutated(
                "src/skills/prime/SKILL.md",
                "Prime-versus-Run mode question",
                "Prime-versus-Run mode selection",
            )
        )

    def test_closed_existing_repo_can_not_be_mutated_to_require_a_question(self):
        self.assert_rejected(
            self.mutated(
                "src/skills/prime/SKILL.md",
                "**zero**",
                "at least one",
            )
        )

    def test_first_cycle_can_not_erase_repository_knowledge(self):
        self.assert_rejected(
            self.mutated(
                "src/skills/prime/references/elicitation.md",
                "does not erase",
                "erases",
            )
        )

    def test_unqualified_manual_waiver_is_rejected(self):
        documents = dict(self.documents)
        documents["src/skills/prime/SKILL.md"] += "\nA mode question may still be used unless manually accepted.\n"
        self.assert_rejected(documents)

    def test_codex_slash_command_regression_is_rejected(self):
        self.assert_rejected(
            self.mutated(
                "platform/codex/plugin.json",
                "$prime",
                "/leanforge:prime",
            )
        )

    def test_real_user_owned_decision_can_not_be_silenced(self):
        self.assert_rejected(
            self.mutated(
                "src/skills/prime/references/elicitation.md",
                "one user question only",
                "no user question",
            )
        )

    def test_repository_evidence_can_not_invent_new_product_behavior(self):
        self.assert_rejected(
            self.mutated(
                "src/skills/prime/references/project-design-domain.md",
                "must come from the user's words",
                "may be inferred from existing code",
            )
        )

    def test_repository_grounded_stack_reconfirmation_is_rejected(self):
        self.assert_rejected(
            self.mutated(
                "src/skills/prime/references/project-design-technical.md",
                "must not be re-presented as a greenfield choice",
                "must be re-presented as a greenfield choice",
            )
        )

    def test_three_doc_persistence_requirement_can_not_be_removed(self):
        self.assert_rejected(
            self.mutated(
                "src/skills/prime/SKILL.md",
                "prose-only pseudo-contract",
                "chat-only contract",
            )
        )


if __name__ == "__main__":
    unittest.main()
