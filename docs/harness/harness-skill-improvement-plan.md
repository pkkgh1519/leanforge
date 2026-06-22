# Harness Skill Improvement Design and Roadmap

Date: 2026-06-10
Status: active implementation plan
Owner: Leanforge maintainers
Scope: `src/skills/harness` and its generated Claude/Codex plugin copies

## 1. Purpose

The `harness` skill is intended to turn recurring agent work into durable, repo-local workflows: concise root guidance, reusable skills, team specs, role briefs, deterministic handoffs, validation loops, and benchmark evidence.

The current design is directionally strong and already useful for experienced users, but the product proof surface is thinner than the architecture. The next improvement cycle should make the skill easier to trust, easier to validate, and easier to try without expanding it into a heavyweight framework.

## 2. Current Assessment

### What is already strong

- The skill has a clear product niche: reusable repo-local agent workflow architecture rather than ordinary task execution.
- It explicitly avoids one-off overuse and tells the agent not to create durable workflow machinery for simple tasks.
- It separates canonical guidance from bulky references.
- It prefers portable, model-agnostic contracts over fixed model pins or runtime-specific messaging.
- It includes a structural validator, `src/skills/harness/scripts/validate_harness.py`.
- The generated `claude/skills/harness` and `codex/plugin/skills/harness` copies match the canonical source, with Codex receiving only the expected `agents/openai.yaml` overlay.

### Main gaps

- The validator is useful but mostly checks structure and banned patterns; it does not prove scenario quality.
- There are no dedicated tests for `validate_harness.py` itself.
- Canonical source validation was not first-class at the time of this review; `validate_harness.py . --json` validates repo-local harness artifacts and docs, not the canonical `src/skills/harness` source tree.
- Trigger/discoverability behavior is documented as an expectation but not captured as a maintained smoke matrix.
- The Claude execution surface needed an explicit check; local Claude runtime smoke was unavailable, so the build now injects the same minimal Claude tool frontmatter for `harness` that `Prime`, `Run`, and `Set` already receive.
- There is no short quickstart or worked example for new users.
- There is no small benchmark/scenario pack that demonstrates what “better harness output” means.

## 3. Non-Goals

This improvement cycle should not:

- rewrite the `harness` skill from scratch;
- add broad runtime orchestration features;
- create a separate execution lifecycle competing with `Prime`, `Run`, or `Set`;
- pin the workflow to a specific model, service tier, or proprietary runtime behavior;
- introduce a large benchmark suite before small smoke scenarios exist;
- move durable project operations into `harness`; core `.leanforge/` state remains the execution-history source of truth.

## 4. Design Principles

1. Improve proof before adding scope.
2. Keep the skill useful as a single-agent workflow; subagents remain optional accelerators.
3. Validate canonical source and installed/generated forms separately.
4. Treat scenario tests as regression guards, not marketing benchmarks.
5. Keep quickstart material small enough that a new user can act within minutes.
6. Preserve the existing architecture unless evidence shows a concrete failure.

## 5. Target State

A maintainer should be able to run one local verification sequence and know:

- the canonical harness skill is structurally valid;
- generated Claude/Codex copies match the canonical source, except intentional platform overlays;
- validator failure modes are covered by tests;
- trigger expectations are documented and checked manually or semi-automatically;
- Claude and Codex installation surfaces are intentionally different only where needed;
- at least one normal path and one failure path demonstrate product behavior.

A user should be able to read a short quickstart and understand:

- when to use `harness`;
- when not to use it;
- what input to provide;
- what files it may create;
- how to validate the result.

## 6. Workstreams

### WS1 — Canonical validation surface

Goal: make `src/skills/harness` directly verifiable without temporary copying.

Planned changes:

- Add a validator mode such as `--skill-dir src/skills/harness` or `--install-check .`.
- Verify canonical `SKILL.md` frontmatter, linked references, and required helper script presence.
- Verify generated `claude/skills/harness` and `codex/plugin/skills/harness` parity against `src/skills/harness`.
- Allow declared platform overlays, currently `codex/plugin/skills/harness/agents/openai.yaml`.

Acceptance criteria:

- A single command validates the canonical source and generated copies.
- The command fails on missing references, source/generated drift, or unexpected generated-only files.
- The command is documented in the quickstart or maintenance notes.

### WS2 — Validator unit tests

Goal: make the validator trustworthy as a product component.

Minimum fixtures:

- missing or malformed `SKILL.md` frontmatter;
- missing `references/...` link;
- fixed model pin or runtime tuning field;
- peer-to-peer runtime messaging dependency;
- `team-spec.md` missing required contract sections;
- overly long root `AGENTS.md` warning.

Acceptance criteria:

- Tests run with the repository's existing Python tooling without new dependencies.
- Each fixture asserts a specific issue code.
- Tests include at least one clean fixture that produces zero errors.

### WS3 — Trigger and discoverability smoke matrix

Goal: make routing expectations explicit and repeatable.

Canonical artifact:

- `src/skills/harness/fixtures/trigger_matrix.tsv`

Optional explanatory reference:

- `src/skills/harness/references/trigger-smoke-matrix.md`, kept short and derived from the TSV.

Minimum cases:

| Case | Prompt class | Expected behavior |
| --- | --- | --- |
| positive-new | reusable workflow creation | `harness` should apply |
| positive-audit | existing harness review or drift check | `harness` should apply |
| positive-benchmark | harness baseline comparison | `harness` should apply |
| near-miss-one-off | one-off bug fix or explanation | `harness` should not add durable workflow files |
| overlap-skill-install | install/update a skill | skill-installer should win unless framed as harness architecture |
| overlap-mcp | build an MCP server | mcp-builder should win unless framed as harness architecture |

Acceptance criteria:

- The matrix is small, documented, and reviewed whenever the trigger description changes.
- Near-miss and overlap cases are present, not only happy paths.

### WS4 — Claude and Codex surface audit

Goal: remove ambiguity about platform support.

Current status:

- Local Claude CLI smoke was unavailable in this workspace.
- `build/build.sh` now treats `harness` as a Claude file-editing and validation skill and injects `disable-model-invocation` plus the same minimal `allowed-tools` set used by `Prime`, `Run`, and `Set`.
- Codex remains unchanged: it uses plugin `Write` capability plus per-skill `agents/openai.yaml` overlay.

Planned checks:

- Confirm whether Claude requires `allowed-tools` injection for `harness` to edit files and run validation.
- If required, update `build/build.sh` so Claude `harness` receives the minimal allowed tools.
- If not required, record the reason and smoke evidence in a maintenance note.
- Keep Codex `agents/openai.yaml` overlay as the only expected generated difference unless a new platform need is documented.

Acceptance criteria:

- The platform difference is intentional and recorded.
- Build output remains deterministic.
- Generated copies continue to pass parity checks with declared exceptions.

### WS5 — Quickstart and worked example

Goal: reduce user entry cost without diluting the expert workflow.

Planned artifact:

- `src/skills/harness/references/harness-quickstart.md`

Minimum sections:

- When to use it.
- When not to use it.
- Minimal prompt examples.
- Expected files.
- Validation command.
- One failure/recovery example.

Acceptance criteria:

- The quickstart is under 150 lines.
- It does not duplicate the full `SKILL.md` workflow.
- It points to deeper references instead of copying them.

### WS6 — Mini scenario pack

Goal: provide small regression evidence before any broad benchmark claim.

Minimum scenarios:

1. Create a reusable review workflow from a recurring task.
2. Audit and repair path/trigger drift in an existing harness.
3. Reject durable harness generation for a one-off request and recommend direct handling.

Acceptance criteria:

- Scenarios define expected artifacts and failure modes.
- Results are recorded as qualitative regression evidence, not aggregate performance claims.
- The pack can be run manually from a fresh session and produce comparable notes.

## 7. Roadmap

### Phase 0 — Baseline freeze

Purpose: record the current known-good state before edits.

Tasks:

- Run `python src/skills/harness/scripts/validate_harness.py . --json` and record that this command validates repo-local harness artifacts and docs, not canonical source parity by itself.
- Run `python src/skills/harness/scripts/validate_harness.py --install-check . --json` once WS1 is implemented.
- Run `python src/skills/harness/scripts/validate_harness.py --skill-dir src/skills/harness --json` when checking only the canonical skill directory.
- Run `python -m unittest discover -s src/skills/harness/tests -p "test*.py"` once WS2 fixtures exist.
- Record current source/generated parity for `harness`.
- Audit the Claude harness execution surface before user-facing adoption work; if `harness` needs explicit file edit or shell permissions in Claude, update the build before Phase 2.
- Confirm working tree is clean before implementation.

Exit criteria:

- Baseline validation result is recorded with its exact proof boundary.
- Claude/Codex surface differences are either confirmed acceptable or promoted to an implementation task.

### Phase 1 — Proof foundation

Purpose: make source validation and validator tests reliable.

Tasks:

1. Implement WS1 canonical validation mode.
2. Add WS2 validator unit tests.
3. Complete the Claude surface audit or make the minimal build change it requires.
4. Add a lightweight test command to documentation.
5. Run the validator, tests, and build if touched.

Exit criteria:

- Canonical source and generated copies can be validated directly.
- Validator tests pass and cover clean plus failing fixtures.
- Claude `harness` generated output carries the intended minimal tool frontmatter.

### Phase 2 — Routing and platform confidence

Purpose: reduce product ambiguity across trigger and platform surfaces.

Tasks:

1. Add WS3 trigger/discoverability smoke matrix.
2. Document the canonical trigger matrix and keep any prose reference derived from it.
3. Re-run parity and validator checks after adding fixtures/references.

Exit criteria:

- Trigger expectations include positive, near-miss, and overlap cases.
- Platform differences are either eliminated or documented with evidence.

### Phase 3 — User-facing adoption assets

Purpose: make the product easier to try and evaluate.

Tasks:

1. Add WS5 quickstart.
2. Add WS6 mini scenario pack.
3. Link new references from `src/skills/harness/SKILL.md` only where necessary.

Exit criteria:

- A new user can identify the right prompt, expected output, and validation command within minutes.
- Scenario pack covers at least one success and one refusal/near-miss path.

### Phase 4 — Release hardening

Purpose: prepare the improvement for publishing.

Tasks:

1. Run full relevant checks.
2. Run `build/build.sh` if source or platform output changed.
3. Verify generated Claude/Codex output.
4. Update `CHANGELOG.md` with concise release notes.

Exit criteria:

- Working tree contains only intended files.
- Validation evidence is current.
- Changelog states user-visible improvements.

## 8. Proposed Implementation Order

Recommended order:

1. WS1 canonical validation mode.
2. WS2 validator unit tests.
3. WS4 platform audit and any minimal build fix.
4. WS3 trigger matrix.
5. WS5 quickstart.
6. WS6 mini scenario pack.
7. Changelog and final build verification.

This order improves confidence before adding user-facing claims.

## 9. Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Validator becomes too strict and blocks valid lightweight harnesses | Medium | Keep warnings separate from errors; add clean fixture for minimal valid harness |
| Trigger matrix turns into a brittle hidden test | Medium | Keep it as smoke guidance, not a hard evaluator unless host routing can be observed reliably |
| Quickstart duplicates `SKILL.md` and drifts | Low | Keep it short and link to references |
| Platform audit causes unnecessary Claude/Codex divergence | Medium | Add build changes only when a concrete tool-surface gap is confirmed |
| Scenario pack becomes marketing instead of regression evidence | Medium | Include failures and near-misses; do not report aggregate improvement without stable scoring |

## 10. Open Questions

- Should canonical validation live in `validate_harness.py` or a repo-level release script?
- Should trigger smoke be stored as TSV fixtures, Markdown guidance, or both?
- Should a future release add a real Claude runtime smoke transcript once the Claude CLI is available locally?
- Should mini scenario results be committed as historical examples, or regenerated only during release checks?

## 11. Immediate Next Step

Continue with Phase 2 by adding the trigger/discoverability smoke matrix. The Phase 1 proof foundation now covers canonical validation, generated parity, validator unit tests, and the Claude `harness` tool surface.
