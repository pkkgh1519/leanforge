import json
import unittest
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/adaptive-assurance/pilot-readiness-study.md"
OBSERVATION = ROOT / "research/adaptive-assurance/observation-template.md"
REPORT = ROOT / "research/adaptive-assurance/pilot-readiness-report-template.md"
PHASE1 = ROOT / "docs/adaptive-assurance-phase1.md"
STATUS = ROOT / "docs/tracking/status.md"
PILOT = ROOT / "src/skills/prime/references/adaptive-assurance-lite-pilot.json"
ATTRIBUTES = ROOT / ".gitattributes"

RESEARCH_ROOT = "research/adaptive-assurance"
EXPECTED_RESEARCH_FILES = {
    "research/adaptive-assurance/pilot-readiness-study.md",
    "research/adaptive-assurance/observation-template.md",
    "research/adaptive-assurance/pilot-readiness-report-template.md",
}
SCAN_ROOTS = (
    "research/adaptive-assurance/",
    "docs/",
    "src/skills/",
    "claude/skills/",
    "codex/plugin/skills/",
)
FORBIDDEN_RESEARCH_ROOTS = SCAN_ROOTS[1:]
SUMMARY_ALLOWLIST = {
    "docs/adaptive-assurance-phase1.md",
    "docs/tracking/status.md",
}
TEXT_EXTENSIONS = {
    ".md",
    ".json",
    ".jsonl",
    ".csv",
    ".tsv",
    ".txt",
    ".log",
    ".yaml",
    ".yml",
}
RESEARCH_DETAIL_ATOMS = (
    "5 cases × 2 hosts × 2 versions × 5 repetitions = 100 runs",
    "paired a/b shadow-tax benchmark",
    "study version: `3`",
    "adaptive assurance contract git blob",
    "counts by shadow mode",
    "binary reversibility gate",
    "weighted removable benefit",
    "installed-package digest",
    "study_batch",
    "case_id",
    "time_to_g7",
    "shadow_mode",
    "removable_seconds",
)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def normalized(path: Path) -> str:
    return normalize_text(path.read_text(encoding="utf-8"))


def _is_under(path: str, roots: tuple[str, ...]) -> bool:
    return any(path.startswith(root) for root in roots)


def validate_research_placement(files: Mapping[str, str]) -> None:
    violations: list[str] = []
    research_files = {
        path for path in files if path.startswith(RESEARCH_ROOT + "/")
    }
    if research_files != EXPECTED_RESEARCH_FILES:
        violations.append(
            "research allowlist mismatch: "
            f"missing={sorted(EXPECTED_RESEARCH_FILES - research_files)}, "
            f"extra={sorted(research_files - EXPECTED_RESEARCH_FILES)}"
        )

    allowed_bodies = {
        normalize_text(files[path]): path
        for path in EXPECTED_RESEARCH_FILES
        if path in files
    }
    for path, body in files.items():
        normalized_body = normalize_text(body)
        if path not in EXPECTED_RESEARCH_FILES and normalized_body in allowed_bodies:
            violations.append(
                f"{path}: exact research artifact copy outside {allowed_bodies[normalized_body]}"
            )

        if _is_under(path, FORBIDDEN_RESEARCH_ROOTS):
            lowered = body.lower()
            detail_score = sum(atom.lower() in lowered for atom in RESEARCH_DETAIL_ATOMS)
            threshold = 6 if path in SUMMARY_ALLOWLIST else 2
            if detail_score >= threshold:
                violations.append(
                    f"{path}: detailed or raw Adaptive Assurance study data leaked into default/live context"
                )

    if violations:
        raise AssertionError("\n".join(violations))


def collect_contract_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative_root in SCAN_ROOTS:
        scan_root = root / relative_root
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
            except UnicodeError as exc:
                raise AssertionError(f"non-UTF-8 study-adjacent file: {path}: {exc}") from exc
    return files


class AdaptiveAssurancePilotReadinessTests(unittest.TestCase):
    def assert_terms(self, body: str, terms: tuple[str, ...], context: str) -> None:
        missing = [term for term in terms if normalize_text(term) not in body]
        self.assertFalse(missing, f"missing {context}: {missing}")

    def test_detailed_study_is_allowlisted_outside_default_and_live_context(self):
        validate_research_placement(collect_contract_files(ROOT))

    def test_renamed_and_non_markdown_study_copies_are_rejected(self):
        files = collect_contract_files(ROOT)
        protocol = files[PROTOCOL.relative_to(ROOT).as_posix()]
        mutations = (
            ("docs/renamed-pilot-study.md", protocol),
            (
                "src/skills/prime/references/renamed-pilot-study.md",
                protocol.replace(
                    "# Adaptive Assurance Pilot-Readiness Study",
                    "# Internal Pilot Evaluation Notes",
                    1,
                ),
            ),
            (
                "docs/adaptive-assurance-benchmark.csv",
                "study_batch,case_id,shadow_mode,time_to_g7,removable_seconds\n",
            ),
            (
                "src/skills/prime/references/pilot-observation.json",
                '{"study_batch":"x","case_id":"y","installed-package digest":"z"}',
            ),
        )
        for path, body in mutations:
            mutated = dict(files)
            mutated[path] = body
            with self.subTest(path=path):
                with self.assertRaises(AssertionError):
                    validate_research_placement(mutated)

    def test_study_is_net_benefit_not_classifier_accuracy_only(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "Time to Trusted Change",
                "Safety:",
                "Shadow tax:",
                "Quality:",
                "User burden:",
                "Potential value and reversibility:",
                "A classifier can be accurate and still fail this study",
                "Phase 1.2 does not activate Lite and cannot prove actual Lite net benefit.",
            ),
            "north-star dimensions",
        )

    def test_first_pilot_topology_is_binary_internal_and_monotonic(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "The user never selects `lite | standard | assurance`.",
                "The first live pilot has only two execution paths:",
                "strict Lite",
                "existing Full Assurance",
                "`standard` remains an observational label.",
                "promotes monotonically to the existing Full Assurance path",
                "three independent live workflows",
                "outside this study's admissible Phase 2 design",
            ),
            "binary internal pilot boundary",
        )

    def test_batch_pins_installed_identity_and_per_host_coverage(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "rebuilt generated-package tree digest for each host",
                "installed-package tree digest actually executed by each host",
                "compare the installed package digest with the pinned generated package digest",
                "marketplace version label alone is not package identity",
                "remove any existing advisory `.leanforge/assurance-shadow.json` and verify the path is absent",
                "A sidecar counts as present only when the current cycle subsequently reaches ELICIT exit",
                "for each host, at least 15 usable observations",
                "at least 5 shadow-Lite, 3 shadow-Standard, and 3 shadow-Assurance",
            ),
            "installed identity and host floors",
        )

    def test_safety_requires_run_evidence_escalation_and_removal_interventions(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "Every one of the 15 required shadow-Lite activation observations must reach Run completion or a Run terminal blocker.",
                "apply every later runtime escalation signal monotonically in event order",
                "unknown signal fails closed to Assurance",
                "Safety-relevant interventions by removable gates",
                "success depended on such an intervention",
                "Zero unresolved removal-dependent strict-Lite cases",
                "both transitions are wrong-path decisions",
                "unresolved instance of either transition makes the batch NO-GO",
                "A `material_false_negative` cannot be accepted, waived, or declared Lite-irrelevant.",
                "re-observation in a fresh pinned batch",
            ),
            "Run-qualified and escalated safety evidence",
        )

    def test_reportable_coverage_dimensions_are_closed(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "counts by host, coarse task category, evidence endpoint",
                "Lite required-true failure",
                "Lite required-false violation",
                "later escalation family",
                "hard-trigger family",
                "removable-gate intervention",
            ),
            "representative coverage reporting",
        )

    def test_shadow_tax_is_host_stratified_and_endpoint_safe(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "Time-to-G7 statistics include only matched A/B pairs where both runs reach G7 successfully.",
                "A terminal stop is never counted as a faster G7 result.",
                "A B-only stop or lower successful-G7 rate fails the gate",
                "evaluate every proposed host independently",
                "An aggregate result cannot mask a failed or unavailable host stratum.",
                "median successful time-to-G7 regression: no more than `5%`",
                "p90 successful time-to-G7 regression: no more than `10%`",
            ),
            "endpoint and host-stratified shadow tax",
        )

    def test_quality_margins_are_predeclared_and_objective(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "predeclare the blinded rubric, aggregation, and margins",
                "1-to-5 executability score",
                "zero critical defects not present in its paired A result",
                "median executability score is no more than 0.25 below A",
                "no more than 10% of pairs score B at least one full point below A",
                "no case scoring 2 or lower when A scores 4 or higher",
                "3-doc-gate blocker rate does not exceed A's",
            ),
            "quality non-inferiority",
        )

    def test_value_gate_uses_seconds_and_prevalence_weighting(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "The common cost unit is wall-clock seconds.",
                "Do not divide seconds by tokens, tool calls, or files read.",
                "Shadow tax is paid by every enrolled cycle",
                "final strict-Lite prevalence × conservative median removable seconds",
                "Use all enrolled eligible cycles in the prevalence denominator.",
                "weighted removable benefit to be at least `2×` expected cost",
                "expected net seconds per enrolled cycle to be positive",
            ),
            "common-unit cohort value",
        )

    def test_templates_capture_all_release_gates(self):
        observation = normalized(OBSERVATION)
        report = normalized(REPORT)
        self.assert_terms(
            observation,
            (
                "Installed-package digest:",
                "Pre-cycle sidecar removed and absence verified:",
                "Current cycle reached ELICIT exit:",
                "Run-qualified for strict-Lite activation coverage:",
                "Later escalation signals in event order:",
                "Successful outcome depended on a gate proposed for removal:",
                "Prime invocation to G7:",
                "Conservative removable seconds:",
            ),
            "observation worksheet",
        )
        self.assert_terms(
            report,
            (
                "Every proposed host must pass independently.",
                "Counts by evidence endpoint:",
                "Run-qualified shadow-Lite count by host:",
                "Counts by removable-gate intervention:",
                "For each proposed host provide a separate table. Do not pool host strata.",
                "B-only stop / both stop",
                "Predeclared quality and user burden by host",
                "Cohort-level potential value in wall-clock seconds",
                "Any unresolved instance is NO-GO.",
                "A material false negative has only two valid dispositions",
                "It cannot be accepted, waived, or marked not Lite-relevant.",
            ),
            "pilot-readiness report",
        )

    def test_phase1_status_lf_and_dormant_activation_match_the_study(self):
        phase1 = normalized(PHASE1)
        status = normalized(STATUS)
        attributes = ATTRIBUTES.read_text(encoding="utf-8")
        pilot = json.loads(PILOT.read_text(encoding="utf-8"))
        self.assert_terms(
            phase1,
            (
                "research/adaptive-assurance/pilot-readiness-study.md",
                "The first live activation, if separately approved, must be binary",
                "It never activates Lite.",
                "claim actual Time to Trusted Change improvement",
            ),
            "Phase 1 handoff",
        )
        self.assert_terms(
            status,
            (
                "Time to Trusted Change",
                "100회를 수행",
                "strict Lite와 기존 Full Assurance 두 실행 경로",
            ),
            "tracked study commitments",
        )
        self.assertIn("research/adaptive-assurance/** text eol=lf", attributes)
        self.assertIn("tests/test_product_north_star.py text eol=lf", attributes)
        self.assertEqual("shadow", pilot["activation"])


if __name__ == "__main__":
    unittest.main()
