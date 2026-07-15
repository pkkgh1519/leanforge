import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def normalized(rel: str) -> str:
    text = read(rel).replace("`", "").replace("**", "")
    return " ".join(text.split())


def markdown_body(rel: str) -> str:
    text = read(rel)
    if text.startswith("---\n"):
        return text.split("---\n", 2)[2]
    return text


def graph_shape(text: str, source: str) -> tuple[set[str], set[str], set[str]]:
    blocks = re.findall(r"```yaml\n(.*?)\n```", text, flags=re.DOTALL)
    if len(blocks) != 1:
        raise AssertionError(f"unexpected YAML block count in {source}: {len(blocks)}")
    graph = blocks[0]
    task_part, barrier_part = graph.split("regen_barriers:", 1)
    top_level = set(re.findall(r"^([a-z0-9_]+):", graph, flags=re.MULTILINE))
    task_fields = set(
        re.findall(r"^\s+(?:-\s+)?([a-z_]+):", task_part, flags=re.MULTILINE)
    )
    barrier_fields = set(re.findall(r"\b([a-z_]+):", barrier_part))
    return top_level, task_fields, barrier_fields


def graph_example_shape(rel: str) -> tuple[set[str], set[str], set[str]]:
    return graph_shape(read(rel), rel)


def keyed_root_shape_errors(text: str, source: str) -> list[str]:
    errors: list[str] = []
    top_level, _, _ = graph_shape(text, source)
    if top_level != {"tasks", "regen_barriers"}:
        errors.append(f"root keys must be tasks and regen_barriers: {sorted(top_level)}")
    blocks = re.findall(r"```yaml\n(.*?)\n```", text, flags=re.DOTALL)
    task_section = re.search(
        r"^tasks:\s*\n(.*?)(?=^regen_barriers:)",
        blocks[0],
        flags=re.DOTALL | re.MULTILINE,
    )
    if task_section is None or re.search(r"^\s+-\s+id:\s*\S+", task_section.group(1), flags=re.MULTILINE) is None:
        errors.append("tasks must be a list of objects beginning with id")
    return errors


class PrimeOutcomePreservationContractTests(unittest.TestCase):
    def assertTermsPresent(self, rel: str, terms: list[str]):
        body = normalized(rel)
        missing = [term for term in terms if term not in body]
        self.assertFalse(missing, f"missing terms in {rel}: {missing}")

    def test_prime_preserves_outcome_while_slicing_execution(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                self.assertTermsPresent(
                    f"{surface}/prime/SKILL.md",
                    [
                        "Preserve value; slice delivery, not intent.",
                        "Broaden understanding, not execution commitments",
                        "user-confirmed outcome and meaningful target state",
                        "spec.md, plan.md, and the Execution Graph only to the Current Delivery Slice",
                        "otherwise the complete requested outcome remains the slice",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/prime/references/project-scoping.md",
                    [
                        "reduce machinery, not the destination",
                        "does not cap a user-confirmed outcome or meaningful target state",
                        "reduce only the Current Delivery Slice",
                        "Do not prebuild future capabilities",
                    ],
                )

    def test_outcome_target_and_slice_are_lenses_not_new_workflow(self):
        required = [
            "three related views of one intent",
            "not mandatory sequential checkpoints, required fields, or a one-question-per-level script",
            "When no broader target is confirmed, the requested change itself may be the slice",
            "Ask only when a load-bearing decision remains model-silent",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                self.assertTermsPresent(f"{surface}/prime/references/elicitation.md", required)

    def test_current_delivery_slice_supports_product_and_enabling_work(self):
        required = [
            "smallest coherent, independently verifiable increment",
            "delivers observable progress toward the confirmed target",
            "removes a named prerequisite or blocker",
            "product behavior, infrastructure, documentation, configuration, migration",
            "immediate consumer and completion evidence",
            "must not prebuild unapproved future capability or introduce speculative abstraction",
            "Without that confirmation, the complete requested outcome remains the Current Delivery Slice",
            "A scaffold, mock-only path, happy path, internal mechanism, or future-compatible shell is not a substitute",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                self.assertTermsPresent(f"{surface}/prime/references/elicitation.md", required)
                self.assertTermsPresent(
                    f"{surface}/prime/references/output-format.md",
                    [
                        "The term is an authoring boundary, not a required heading or machine field",
                        "required artifact or state transition, its immediate consumer, and completion evidence",
                    ],
                )

    def test_foundation_keeps_four_sections_and_non_executable_future_meanings(self):
        for surface in SURFACES:
            for skill in ("prime", "run"):
                rel = f"{surface}/{skill}/references/foundation-format.md"
                with self.subTest(surface=surface, skill=skill):
                    body = read(rel)
                    for heading in (
                        "Section 1 — Project identity",
                        "Section 2 — Domain model",
                        "Section 3 — Technical decisions",
                        "Section 4 — Future scope",
                    ):
                        self.assertEqual(body.count(heading), 1, f"unexpected heading count in {rel}: {heading}")
                    self.assertNotIn("Section 5 —", body)
                    self.assertTermsPresent(
                        rel,
                        [
                            "concrete remaining outcomes",
                            "future directions",
                            "Neither is implementation authorization",
                            "Concrete remaining outcomes may preserve priority or dependency facts only when they are user-confirmed or derivable",
                            "Future directions stay unordered",
                            "not as an implementation target or a source from which to infer constraints",
                            "does not infer work, constraints, abstractions, extension points, or compatibility steps",
                        ],
                    )

    def test_future_directions_round_trip_without_becoming_backlog(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                self.assertTermsPresent(
                    f"{surface}/run/references/harness-format.md",
                    [
                        "Remaining (concrete user-confirmed target outcomes that are still unimplemented)",
                        "Future directions (user-confirmed durable value or capability directions",
                        "unordered and non-executable",
                        "do not decompose, schedule, estimate, assign, dependency-order",
                        "Do not bulk-migrate or reinterpret it",
                        "Unclassified legacy context",
                        "mark it non-executable and unapproved",
                        "do not promote one into Remaining unless the user confirms it",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/run/references/harness-lifecycle.md",
                    [
                        "concrete remaining outcomes → status.md's \"Remaining\"",
                        "durable future directions → status.md's \"Future directions\"",
                        "Preserve priority or dependency facts for Remaining only when confirmed or derivable",
                        "never order Future directions",
                        "handoff non-executable context update",
                        "does not add implementation scope, tasks, constraints, abstractions, or ordering",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/run/references/harness-review.md",
                    [
                        "Future meaning survives without promotion",
                        "promoted into Remaining without user confirmation",
                        "neutral Unclassified legacy context",
                        "explicitly non-executable and unapproved",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/set/SKILL.md",
                    ["done, concrete Remaining outcomes, and non-executable Future directions"],
                )

    def test_harness_records_apply_section_specific_authority(self):
        forbidden = (
            "It is a **durable project constraint**",
            "treat it as the existing project constraint",
            "treat them as the existing project constraint",
        )
        required = [
            "durable project record and operating context",
            "Each record carries only the authority defined by its section",
            "Remaining may record a confirmed target commitment",
            "neither Remaining nor Future directions authorizes the current cycle",
            "Future directions are not commitments",
        ]
        for surface in SURFACES:
            for skill in ("run", "set"):
                rel = f"{surface}/{skill}/references/harness-format.md"
                with self.subTest(surface=surface, skill=skill):
                    body = read(rel)
                    self.assertTermsPresent(rel, required)
                    for phrase in forbidden:
                        self.assertNotIn(phrase, body)
            lifecycle_rel = f"{surface}/run/references/harness-lifecycle.md"
            with self.subTest(surface=surface, skill="run-lifecycle"):
                self.assertTermsPresent(
                    lifecycle_rel,
                    [
                        "Read all current project documentation first as the durable project record",
                        "Apply each item according to its section authority",
                        "Remaining and Future directions remain non-executable status or context",
                    ],
                )
                self.assertNotIn("treat them as the existing project constraint", read(lifecycle_rel))
            self.assertTermsPresent(
                f"{surface}/set/SKILL.md",
                ["durable project memory and operating context", "Only its normative records constrain later work"],
            )

    def test_future_direction_constraint_is_prime_owned_and_run_does_not_infer(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                self.assertTermsPresent(
                    f"{surface}/prime/references/elicitation.md",
                    [
                        "only when all three conditions hold",
                        "close a costly or irreversible option",
                        "concrete present boundary, data choice, or contract choice",
                        "does not implement the future capability or add speculative abstraction",
                        "Put only that present-tense constraint in spec.md or the handoff's hard gates",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/run/SKILL.md",
                    [
                        "not an implementation target or execution authority",
                        "Do not infer work, constraints, abstractions, extension points, or compatibility steps",
                        "Prime has already written that narrow constraint",
                    ],
                )

    def test_delta_reopens_only_material_outcome_conflicts(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                self.assertTermsPresent(
                    f"{surface}/prime/references/elicitation.md",
                    [
                        "do not re-elicit product strategy",
                        "For a candidate about a recorded outcome or future direction",
                        "materially contradict, invalidate, narrow, or close it",
                        "Mere non-implementation of a future direction",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/prime/references/intent-completeness.md",
                    [
                        "Outcome-preservation audit",
                        "without silently shrinking or inflating the user-confirmed outcome",
                        "must not trigger a strategy interview",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/prime/SKILL.md",
                    [
                        "does the proposed slice preserve the confirmed outcome",
                        "without unconfirmed narrowing or inflation",
                    ],
                )

    def test_source_differences_stay_candidates_until_delta_materiality(self):
        required = {
            "prime/SKILL.md": [
                "a source difference is only a candidate",
                "A difference is not yet a conflict or a question.",
                "additional delta rules below govern every input↔harness candidate",
                "ELICIT alone decides which candidates become questions",
                "DECOMPOSE decompose.md",
                "cycle-neutral source-difference disposition",
                "not product-strategy re-elicitation",
            ],
            "prime/references/decompose.md": [
                "source differences go to ELICIT as candidates",
                "A difference is a candidate, not yet a conflict",
                "do not resolve or ask here",
                "cycle-neutral source-difference disposition",
                "do not ask merely because it differs",
            ],
            "prime/references/elicitation.md": [
                                "Mere non-implementation of a future direction, a different time horizon, or a cheap reversible extension path is not a conflict.",
                "Disposition of source-difference candidates — cycle-neutral",
                "Source or section authority",
                "resolve the candidate with cited evidence and do not ask",
                "Scope and time horizon",
                "Only if the authority and scope/time steps did not resolve it",
                "materially incompatible at the same site",
                "not product-strategy re-elicitation",
                "applicable current invariant, contract, approved decision, or operating rule",
            ],
            "prime/references/evidence-grounding-scout.md": [
                "source difference candidate",
                "feed source differences into DECOMPOSE as candidates",
                "ELICIT alone decides whether it becomes a question",
            ],
            "prime/references/gap-analysis.md": [
                "source differences are DECOMPOSE's candidates",
            ],
            "prime/references/grounds-gate.md": [
                "source-difference candidate from DECOMPOSE",
                "For a probe-generated gap",
                "For a source-difference candidate",
                "one or both claims are already recorded",
                "authority, scope, time horizon, and settled context fail to resolve the claims",
                "must not be demoted merely because",
                "ELICIT applies this one standard",
            ],
        }
        forbidden = {
            "prime/SKILL.md": [
                "flagged in DECOMPOSE and asked in ELICIT",
                "the question is ELICIT's",
                "conflict→ELICIT",
                "DECOMPOSE catches it, ELICIT asks it",
                "source conflict candidate",
                "DECOMPOSE decompose.md · grounds-gate.md",
                "Force-load references/decompose.md and references/grounds-gate.md",
            ],
            "prime/references/decompose.md": [
                "conflicts go to ELICIT as questions",
                "A difference is a conflict",
                "Flag every source difference as a question candidate",
                '"if it differs, ask"',
            ],
            "prime/references/evidence-grounding-scout.md": [
                "source conflict candidate",
                "feed conflicts into DECOMPOSE",
                "ask during DECOMPOSE",
            ],
            "prime/references/gap-analysis.md": [
                "source conflicts are DECOMPOSE's flags",
            ],
            "prime/references/grounds-gate.md": [
                "a conflict flag from DECOMPOSE",
                "shared by DECOMPOSE and ELICIT",
            ],
        }

        for surface in SURFACES:
            for suffix, terms in required.items():
                rel = f"{surface}/{suffix}"
                with self.subTest(surface=surface, rel=suffix, contract="required"):
                    self.assertTermsPresent(rel, terms)
            for suffix, terms in forbidden.items():
                rel = f"{surface}/{suffix}"
                body = normalized(rel)
                with self.subTest(surface=surface, rel=suffix, contract="forbidden"):
                    for term in terms:
                        self.assertNotIn(term, body)

    def test_delta_new_future_context_has_a_non_executable_round_trip(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                self.assertTermsPresent(
                    f"{surface}/prime/references/output-format.md",
                    [
                        "Delta only",
                        "clearly labeled non-executable context update in the handoff",
                        "not a new Foundation, requirement, backlog item, or fixed heading",
                        "lets Run preserve the meaning in status.md",
                    ],
                )
                self.assertTermsPresent(
                    f"{surface}/run/references/harness-lifecycle.md",
                    [
                        "Read any handoff non-executable context update",
                        "Map a newly confirmed concrete target outcome to status.md's \"Remaining\"",
                        "durable value/capability direction to \"Future directions,\" by meaning",
                        "preserve it as unclassified non-executable context",
                    ],
                )

    def test_spec_plan_and_graph_are_current_slice_only_without_schema_change(self):
        expected_shape = (
            {"tasks", "regen_barriers"},
            {"id", "depends", "risk"},
            {"after", "run"},
        )
        for surface in SURFACES:
            rel = f"{surface}/prime/references/output-format.md"
            consumer_rel = f"{surface}/run/references/graph-contract.md"
            with self.subTest(surface=surface):
                self.assertTermsPresent(
                    rel,
                    [
                        "Artifact allocation boundary",
                        "spec.md contains only the Current Delivery Slice",
                        "plan.md and the Execution Graph contain only work required for that slice",
                        "Every plan task must be necessary to produce the Current Delivery Slice",
                    ],
                )
                author_shape = graph_example_shape(rel)
                consumer_shape = graph_example_shape(consumer_rel)
                self.assertEqual(author_shape, expected_shape)
                self.assertEqual(consumer_shape, expected_shape)
                self.assertEqual(author_shape, consumer_shape)

    def test_prime_requires_graph_contract_validation_not_parse_only(self):
        required = [
            "validates against the exact Execution Graph contract",
            "root keys are exactly tasks and regen_barriers",
            "tasks is a list of objects with id, depends, and optional risk",
            "every depends/after id names a graph task",
            "the dependency graph is acyclic",
            "plan body and graph task-id sets match",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface, owner="prime"):
                self.assertTermsPresent(f"{surface}/prime/SKILL.md", required)
            with self.subTest(surface=surface, owner="gate"):
                self.assertTermsPresent(
                    f"{surface}/prime/references/3-doc-gate.md",
                    ["graph contract validation, not syntax parsing alone"],
                )

    def test_known_model_output_fixture_rejects_keyed_task_root(self):
        fixture = "tests/fixtures/prime-model-output/invalid-keyed-task-plan.md"
        errors = keyed_root_shape_errors(read(fixture), fixture)
        self.assertIn("root keys must be tasks and regen_barriers: ['regen_barriers', 'task_1']", errors)
        self.assertIn("tasks must be a list of objects beginning with id", errors)

        for rel in (
            "src/skills/prime/references/output-format.md",
            "src/skills/run/references/graph-contract.md",
        ):
            with self.subTest(valid_contract_example=rel):
                self.assertEqual(keyed_root_shape_errors(read(rel), rel), [])

    def test_shared_contracts_and_generated_surfaces_match(self):
        self.assertEqual(
            read("src/skills/prime/references/foundation-format.md"),
            read("src/skills/run/references/foundation-format.md"),
        )
        self.assertEqual(
            read("src/skills/run/references/harness-format.md"),
            read("src/skills/set/references/harness-format.md"),
        )
        self.assertEqual(
            read("src/skills/run/references/harness-review.md"),
            read("src/skills/set/references/harness-review.md"),
        )

        exact_refs = [
            "prime/references/decompose.md",
            "prime/references/elicitation.md",
            "prime/references/evidence-grounding-scout.md",
            "prime/references/gap-analysis.md",
            "prime/references/grounds-gate.md",
            "prime/references/project-scoping.md",
            "prime/references/output-format.md",
            "prime/references/3-doc-gate.md",
            "prime/references/foundation-format.md",
            "prime/references/intent-completeness.md",
            "prime/references/first-cycle-review.md",
            "prime/references/example-3doc.md",
            "run/references/foundation-format.md",
            "run/references/harness-format.md",
            "run/references/harness-lifecycle.md",
            "run/references/harness-review.md",
            "run/references/reviewer-prompt.md",
            "set/references/harness-format.md",
            "set/references/harness-review.md",
        ]
        for rel in exact_refs:
            with self.subTest(rel=rel, surface="codex"):
                self.assertEqual(read(f"src/skills/{rel}"), read(f"codex/plugin/skills/{rel}"))
            with self.subTest(rel=rel, surface="claude"):
                self.assertEqual(read(f"src/skills/{rel}"), read(f"claude/skills/{rel}"))

        for skill in ("prime", "run", "set"):
            with self.subTest(skill=skill, surface="codex"):
                self.assertEqual(read(f"src/skills/{skill}/SKILL.md"), read(f"codex/plugin/skills/{skill}/SKILL.md"))
            with self.subTest(skill=skill, surface="claude"):
                self.assertEqual(
                    markdown_body(f"src/skills/{skill}/SKILL.md"),
                    markdown_body(f"claude/skills/{skill}/SKILL.md"),
                )

    def test_roadmap_records_minimalism_and_release_gate(self):
        rel = "docs/prime/outcome-preservation-patch-roadmap.md"
        self.assertTermsPresent(
            rel,
            [
                "Preserve value; slice delivery, not intent",
                "No fifth workflow stage or mandatory strategy interview",
                "No new gate, reviewer dispatch, roadmap parser, machine field, or YAML key",
                "No Execution Graph, scheduler, dependency, or risk-enum change",
                "No direct edits to generated surfaces or installed plugin caches",
                "Decide on a patch-version bump only after",
            ],
        )


if __name__ == "__main__":
    unittest.main()
