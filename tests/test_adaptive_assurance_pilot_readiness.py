import json
import re
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


HOST_STUDY_REQUIRED_RULES = {
    "protocol": (
        (
            "## Pinned study batch and installed identity",
            "Before the batch opens, predeclare one execution-provenance method per host. "
            "Give it a stable method ID and version, identify the authoritative command, UI, "
            "trace, or readback, list the fields and deterministic comparison required to "
            "bind that evidence to the installed-package digest, state fresh-session, reload, "
            "and cache conditions, and define a redaction-safe retained artifact. Apply the "
            "method unchanged to A and B. A method selected or relaxed after outcomes are "
            "visible is invalid. Missing, unverifiable, mismatched, precondition-failed, or "
            "redaction-destroyed binding is unqualified; no waiver or manual acceptance can "
            "convert it to qualified evidence.",
        ),
        (
            "### Arms and workload",
            "Before each run, record the declared arm, pinned installed-package digest, "
            "predeclared execution-provenance method ID and version, whether its fresh-session, "
            "reload, and cache precondition was satisfied, authoritative binding or readback, "
            "whether that binding identifies the pinned installed package for the declared arm, "
            "provenance-qualified status, and exclusion reason. Both arms must independently "
            "satisfy the precondition and identify their declared arm before a pair can enter "
            "endpoint, latency, quality, or user-burden analysis. A missing, unverifiable, "
            "mismatched, precondition-failed, or redaction-destroyed binding does not count "
            "toward the planned repetition floor, remains in batch accounting, and may be "
            "replaced only under a predeclared same-batch rerun rule applied without inspecting "
            "its performance or quality outcome. No waiver, manual acceptance, repository-local "
            "source read, or opposite-arm result can qualify it.",
        ),
        (
            "### Endpoint integrity",
            "Time-to-G7, quality, and user-burden statistics include only matched A/B pairs "
            "where both runs are provenance-qualified for their declared arms and both reach G7 "
            "successfully.",
        ),
        (
            "## Part D: predeclared quality and user-burden comparison",
            "For every paired case admitted by Part C's provenance and endpoint rules, record "
            "critical defects:",
        ),
    ),
    "observation": (
        (
            "## F. Integrity and disposition",
            "If any identity, execution-provenance, fixture-state, or Prime-persistence "
            "integrity item above is unchecked, Usable safety observation must be `no`.",
        ),
    ),
    "report": (
        (
            "## 6. Host-stratified paired A/B shadow-tax benchmark",
            "Only pairs whose A and B runs independently satisfy the predeclared "
            "session/reload/cache precondition and match their declared arm and pinned installed "
            "package may enter the table. A declared-arm mismatch, a planned run left unqualified "
            "after any permitted same-batch replacement, a B-only stop, lower B successful-G7 "
            "rate, unavailable required metric, or failed margin fails this host. Any replacement "
            "must follow the predeclared rule without inspecting performance or quality outcomes. "
            "No waiver, manual acceptance, repository-local source read, or opposite-arm result "
            "may qualify a run.",
        ),
        (
            "## 7. Predeclared quality and user burden by host",
            "Use only Part 6's both-arm-qualified matched successful-G7 comparison set.",
        ),
    ),
}

HOST_STUDY_REQUIRED_FIELDS = {
    ("protocol", "### Measurements"): (
        "- declared arm: `A | B`;",
        "- pinned installed-package digest for that arm;",
        "- execution-provenance method ID and version;",
        "- execution session/reload/cache precondition satisfied: `yes | no | unverifiable`;",
        "- authoritative execution binding or readback;",
        "- binding matches the declared arm's pinned installed package: `yes | no | unverifiable`;",
        "- execution provenance qualified: `yes | no`;",
        "- exclusion reason: `<closed reason | none>`;",
    ),
    ("protocol", "### Host-stratified shadow-tax gates"): (
        "- declared-arm execution mismatches: exactly `0`;",
        "- every planned A and B repetition is provenance-qualified after any permitted "
        "same-batch replacement;",
    ),
    ("observation", "## A. Cohort, identity, and sealed prediction"): (
        "- Execution-provenance method ID/version:",
        "- Execution session/reload/cache precondition satisfied:",
        "- Installed-package execution binding/readback:",
        "- Execution binding identifies pinned installed package:",
        "- Execution provenance qualified:",
        "- Execution-provenance exclusion reason:",
    ),
    ("report", "## 1. Decision"): (
        "- Predeclared execution-provenance method ID/version and binding/precondition rule by host:",
        "- A/B executed-package binding and precondition verified by host:",
    ),
    ("report", "## 6. Host-stratified paired A/B shadow-tax benchmark"): (
        "- Execution-provenance method ID/version and binding/precondition rule:",
        "- Planned A runs / provenance-qualified A runs:",
        "- Planned B runs / provenance-qualified B runs:",
        "- Declared-arm mismatches A/B:",
        "- Execution session/reload/cache precondition failures A/B:",
        "- Unqualified execution provenance A/B by reason:",
        "- Exclusions by reason:",
        "- Both-arm-qualified matched pairs:",
        "Metric on both-arm-qualified matched successful-G7 pairs",
    ),
}

HOST_STUDY_INVERSION_PATTERNS = (
    r"repository-local source skill (?:counts|may count) as installed-package provenance",
    r"marker-loss state is an eligible small-delta smoke",
    r"prime-owned `?\.leanforge/`? planning writes (?:are|must be) prohibited",
    r"inline pseudo-documents (?:count|counts) as a completed prime observation",
    r"(?:may|can) manually accept an? unqualified execution binding",
    r"unqualified a/b pair (?:may|can) enter .* statistics",
    r"unchecked execution-provenance item (?:may|can) still set usable safety observation to `yes`",
    r"declared-arm mismatch (?:may|can) be waived",
    r"installed-package smoke counts toward the 20-smoke floor even when execution provenance is absent",
    r"execution session/reload/cache precondition failure (?:may|can) be waived",
    r"(?:may|can) select a same-batch replacement after inspecting (?:its )?(?:performance|quality)",
)


def markdown_section(value: str, heading: str) -> str:
    matches = list(
        re.finditer(rf"^{re.escape(heading)}[ \t]*$", value, re.MULTILINE)
    )
    if len(matches) != 1:
        raise AssertionError(
            f"Markdown section cardinality drift: {heading}: {len(matches)}"
        )
    match = matches[0]
    level = len(heading) - len(heading.lstrip("#"))
    following = value[match.end():]
    next_match = re.search(rf"^#{{1,{level}}}[ \t]+.+$", following, re.MULTILINE)
    return following[: next_match.start()] if next_match else following


def validate_host_study_semantics(
    protocol: str, observation: str, report: str
) -> None:
    documents = {
        "protocol": protocol,
        "observation": observation,
        "report": report,
    }
    for document, rules in HOST_STUDY_REQUIRED_RULES.items():
        for heading, rule in rules:
            section = normalize_text(markdown_section(documents[document], heading))
            if section.count(normalize_text(rule)) != 1:
                raise AssertionError(
                    f"{document} {heading}: missing or duplicate canonical rule"
                )
    for (document, heading), fields in HOST_STUDY_REQUIRED_FIELDS.items():
        section = normalize_text(markdown_section(documents[document], heading))
        missing_or_duplicate = [
            field for field in fields if section.count(normalize_text(field)) != 1
        ]
        if missing_or_duplicate:
            raise AssertionError(
                f"{document} {heading}: missing or duplicate fields: "
                f"{missing_or_duplicate}"
            )

    combined = normalize_text("\n".join(documents.values()))
    inversions = [
        pattern
        for pattern in HOST_STUDY_INVERSION_PATTERNS
        if re.search(pattern, combined, re.IGNORECASE)
    ]
    if inversions:
        raise AssertionError(f"host-study semantic inversions: {inversions}")


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

    def test_batch_pins_each_arm_installed_identity_and_per_host_coverage(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "rebuilt generated-package tree digest for each host",
                "installed-package tree digest actually executed by each host",
                "compare each installed package digest with its pinned generated package digest",
                "marketplace version label alone is not package identity",
                "installed-package execution provenance",
                "A repository-local source skill does not count as installed-package provenance.",
                "predeclare one execution-provenance method per host",
                "stable method ID and version",
                "Apply the method unchanged to A and B.",
                "no waiver or manual acceptance can convert it to qualified evidence",
                "B candidate arm:",
                "A shadow-disabled control arm:",
                "A/B source diff is exactly the allowlisted hook removal",
                "prohibit identity drift within either arm",
                "remove any existing advisory `.leanforge/assurance-shadow.json` and verify the path is absent",
                "For a declared delta case, a valid `.leanforge/status.json` is present before Prime starts.",
                "JSON-parses to exactly `{ \"initialized\": true }`",
                "A marker-loss state is not an eligible small-delta smoke or benchmark fixture.",
                "A first-cycle fixture has neither the marker nor a Leanforge-shaped harness.",
                "no `.leanforge/run.json`, registered Leanforge worktree, active root 3-doc, or conflicting `.dryforge/` state",
                "The cycle-state fixture is byte-identical across A and B.",
                "Prime-owned `.leanforge/` planning and shadow writes are allowed and required",
                "Product, test, config, dependency, and generated-package files remain read-only.",
                "inline pseudo-documents without the normal Prime files is not a completed Prime observation",
                "Each smoke records authoritative installed-package execution provenance",
                "does not count toward the 20-smoke floor",
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
                "Time-to-G7, quality, and user-burden statistics include only matched A/B pairs where both runs are provenance-qualified for their declared arms and both reach G7 successfully.",
                "planned and provenance-qualified run counts",
                "declared-arm mismatches",
                "A terminal stop is never counted as a faster G7 result.",
                "A declared-arm mismatch, a planned repetition left unqualified after any permitted same-batch replacement, a B-only stop, or a lower successful-G7 rate fails the gate.",
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
                "sum(conservative removable seconds across all enrolled cycles) / enrolled cycle count",
                "sum(shadow-tax seconds) + sum(promotion/recovery seconds)",
                "rather than prevalence multiplied by a Lite-case median",
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
                "Execution-provenance method ID/version:",
                "Execution session/reload/cache precondition satisfied:",
                "Installed-package execution binding/readback:",
                "Execution binding identifies pinned installed package:",
                "Execution provenance qualified:",
                "Execution-provenance exclusion reason:",
                "Prime-owned `.leanforge/` writes permitted:",
                "Sidecar absence disposition:",
                "Pre-cycle sidecar removed and absence verified:",
                "Pre-cycle state valid for declared cycle:",
                "Pre-cycle active-state guard clear:",
                "Current cycle reached ELICIT exit:",
                "Run-qualified for strict-Lite activation coverage:",
                "Later escalation signals in event order:",
                "Successful outcome depended on a gate proposed for removal:",
                "Prime invocation to G7:",
                "Conservative removable seconds:",
                "Approval-step count:",
                "The predeclared execution-provenance method was applied unchanged, its session/reload/cache precondition was satisfied, and its authoritative binding identifies the pinned installed package.",
                "Missing, unverifiable, mismatched, precondition-failed, or redaction-destroyed execution binding was not waived or manually accepted.",
                "An unexplained absent sidecar makes this observation unusable.",
                "Usable safety observation must be `no`",
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
                "A shadow-disabled control patch/tree digest",
                "A/B allowlisted source and generated diff verified",
                "Reply-turn delta",
                "Approval-step delta",
                "Sum removable seconds",
                "Any unresolved instance is NO-GO.",
                "A material false negative has only two valid dispositions",
                "It cannot be accepted, waived, or marked not Lite-relevant.",
                "Execution provenance qualified",
                "Provenance method ID/version",
                "A/B arm execution provenance",
                "Predeclared execution-provenance method ID/version and binding/precondition rule by host:",
                "A/B executed-package binding and precondition verified by host:",
                "Planned A runs / provenance-qualified A runs:",
                "Planned B runs / provenance-qualified B runs:",
                "Declared-arm mismatches A/B:",
                "Execution session/reload/cache precondition failures A/B:",
                "Unqualified execution provenance A/B by reason:",
                "Both-arm-qualified matched pairs:",
                "Usable smokes",
            ),
            "pilot-readiness report",
        )

    def test_host_study_semantic_contract_is_closed(self):
        validate_host_study_semantics(
            PROTOCOL.read_text(encoding="utf-8"),
            OBSERVATION.read_text(encoding="utf-8"),
            REPORT.read_text(encoding="utf-8"),
        )

    def test_host_study_semantic_mutations_fail_closed(self):
        protocol = PROTOCOL.read_text(encoding="utf-8")
        observation = OBSERVATION.read_text(encoding="utf-8")
        report = REPORT.read_text(encoding="utf-8")
        mutations = (
            (
                "repository-local-provenance",
                protocol + "\nA repository-local source skill counts as installed-package provenance.\n",
                observation,
                report,
            ),
            (
                "marker-loss-eligible",
                protocol + "\nA marker-loss state is an eligible small-delta smoke.\n",
                observation,
                report,
            ),
            (
                "prime-persistence-inverted",
                protocol + "\nPrime-owned `.leanforge/` planning writes are prohibited, and inline pseudo-documents count as a completed Prime observation.\n",
                observation,
                report,
            ),
            (
                "manual-provenance-acceptance",
                protocol + "\nA collector may manually accept an unqualified execution binding.\n",
                observation,
                report,
            ),
            (
                "unqualified-pair-admitted",
                protocol + "\nAn unqualified A/B pair may enter latency, quality, and user-burden statistics.\n",
                observation,
                report,
            ),
            (
                "unchecked-observation-passes",
                protocol,
                observation + "\nAn unchecked execution-provenance item may still set Usable safety observation to `yes`.\n",
                report,
            ),
            (
                "declared-arm-mismatch-waived",
                protocol,
                observation,
                report + "\nA declared-arm mismatch may be waived.\n",
            ),
            (
                "provenance-free-smoke-counted",
                protocol + "\nEvery installed-package smoke counts toward the 20-smoke floor even when execution provenance is absent.\n",
                observation,
                report,
            ),
            (
                "execution-precondition-waived",
                protocol + "\nAn execution session/reload/cache precondition failure may be waived.\n",
                observation,
                report,
            ),
            (
                "outcome-aware-replacement",
                protocol
                + "\nA collector may select a same-batch replacement after inspecting its performance outcome.\n",
                observation,
                report,
            ),
            (
                "missing-run-arm-field",
                protocol.replace("- declared arm: `A | B`;\n", "", 1),
                observation,
                report,
            ),
            (
                "missing-run-precondition-field",
                protocol.replace(
                    "- execution session/reload/cache precondition satisfied: `yes | no | unverifiable`;\n",
                    "",
                    1,
                ),
                observation,
                report,
            ),
            (
                "missing-observation-precondition-field",
                protocol,
                observation.replace(
                    "- Execution session/reload/cache precondition satisfied: `<yes | no | unverifiable>`\n",
                    "",
                    1,
                ),
                report,
            ),
            (
                "missing-qualified-pair-accounting",
                protocol,
                observation,
                report.replace("- Both-arm-qualified matched pairs: `<n>`\n", "", 1),
            ),
            (
                "missing-precondition-failure-accounting",
                protocol,
                observation,
                report.replace(
                    "- Execution session/reload/cache precondition failures A/B: `<counts>`\n",
                    "",
                    1,
                ),
            ),
            (
                "duplicate-report-section-shadowing",
                protocol,
                observation,
                report
                + "\n## 6. Host-stratified paired A/B shadow-tax benchmark\n\nA declared-arm mismatch may be waived.\n",
            ),
        )
        for name, mutated_protocol, mutated_observation, mutated_report in mutations:
            with self.subTest(mutation=name):
                with self.assertRaises(AssertionError):
                    validate_host_study_semantics(
                        mutated_protocol, mutated_observation, mutated_report
                    )

    def test_private_sanitized_benchmark_fixtures_are_permitted_but_public_raw_data_is_not(self):
        body = normalized(PROTOCOL)
        self.assert_terms(
            body,
            (
                "private study workspace may retain the exact sanitized or synthetic benchmark prompts",
                "fixed repository fixtures",
                "predeclared answers",
                "randomization seed",
                "must remain outside the public repository",
                "Real-observation raw prompts",
            ),
            "reproducible private benchmark fixtures",
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
                "control is derived from the same candidate tree with only the live shadow hook disabled",
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
                "live shadow hook만 제거한 control A와 candidate B",
            ),
            "tracked study commitments",
        )
        self.assertIn("research/adaptive-assurance/** text eol=lf", attributes)
        self.assertIn("tests/test_product_north_star.py text eol=lf", attributes)
        self.assertEqual("shadow", pilot["activation"])


if __name__ == "__main__":
    unittest.main()
