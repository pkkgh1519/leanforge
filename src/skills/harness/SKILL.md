---
name: harness
description: "Use for agent harness architecture: designing, auditing, repairing, or comparing durable repo-local agent workflows with team specs, role briefs, specialist/orchestrator skills, custom agents, validation loops, benchmark packs, or multi-role handoff contracts. Korean triggers include 하네스 만들기/점검/검토. Exclude one-off handoff document writing, skill install/update/review, standalone MCP/tool/plugin work, and local runtime update checks unless explicitly framed as harness architecture."
---

# Harness

Harness is a meta-skill for designing portable, repo-local agent workflows. Use it to analyze a project, decide which guidance belongs in `AGENTS.md`, choose the smallest collaboration pattern, generate reusable specialist skills, define deterministic handoff files, and preserve validation and maintenance evidence.

Within the dryforge plugin, Harness is the upper design layer over the per-cycle project harness that `dryforge go` writes: `go` creates or updates a repo's harness each cycle, while Harness turns recurring or team-worthy patterns into durable workflow specs and specialist skills instead of re-deriving them each cycle. For dryforge repositories, prefer repo-local review/explore/checklist skills that `go` can use as optional lenses; never generate a replacement execution scheduler.

The canonical skill tree is `.agents/skills/`, and Harness ships for both Claude and Codex. Optional repo-local `.codex/agents/` and `.codex/config.toml` files may support bounded project-specific subagent workflows, but generated harnesses must not depend on runtime-specific peer messaging or fixed model pins.

## Output Language Rule

Match the user's language — discovered at runtime, never assumed. Write all human-reviewable prose in generated harness artifacts in the language the user communicates in, natively (as a fluent speaker would, never translationese). This includes `AGENTS.md`, team specs, role briefs, handoff files, benchmark descriptions, validation notes, maintenance notes, and design docs. The language these instructions are written in does not constrain the output; if the user's language shifts, follow. An explicitly documented repository-level language convention outranks the session default.

Keep machine-facing keys, filenames, paths, commands, code identifiers, schemas, YAML field names, and API fields in their required language.

## When to Use

Use Harness when the user asks to:

- design a reusable workflow for a repository or domain
- create specialist skills, role briefs, team specs, or handoff conventions
- adapt an existing workflow into agent-discoverable repo skills
- distill repeated dryforge archives into go-compatible repo-local review/explore/checklist skills
- standardize recurring review, QA, research, experimentation, or harness-related documentation processes
- compare a no-harness baseline against a structured harness-guided run
- maintain or repair an existing harness that has path drift, overlapping skills, stale guidance, or missing validation

Do not use Harness for a one-off task that can be solved directly without adding durable workflow structure.

## Required Inputs

Discover or ask for the smallest missing set of inputs:

- repository or domain goal
- primary workflow and expected deliverables
- quality bar and failure tolerance
- existing repo guidance, skills, docs, and generated artifacts
- likely user expertise level and preferred explanation density
- whether repo-local subagents may improve read-heavy, review-heavy, or parallelizable work
- whether benchmarking or baseline comparison is needed

When inputs are missing but the repository is available, inspect the repository first and make the narrowest reasonable assumption. Record assumptions in the generated team spec or validation note.

## Purpose and Success Criteria Gate

Before generating or modifying harness artifacts, confirm that current evidence is sufficient to identify the final objective, served user or operator, target workflow, success criteria, validation evidence, non-goals, constraints, and side-effect boundaries.

Inspect repository evidence first. If missing information would materially change the harness architecture, work depth, or validation contract, do not proceed on assumptions.

Repository evidence must be broad enough to justify the harness design, not just the existing harness surface. Inspect the smallest relevant set of:

- root guidance and product/domain docs: `AGENTS.md`, README, CONTRIBUTING, PRD, WORKFLOW, ADRs, runbooks, and equivalent docs
- manifests, lockfiles, build config, package managers, framework markers, source layout, entry points, generated artifacts, and public contracts
- available validation surfaces: test, lint, typecheck, build, CI, local app, schema, fixture, benchmark, or manual verification paths
- runtime and risk surfaces when relevant: deploy, migrations, data repair, background jobs, automations, secrets handling, auth, payments, or live-service boundaries
- existing operation artifacts such as operations summaries, task logs, runbooks, status dashboards, or handoff notes when present

Treat this as evidence for choosing a harness architecture only. Do not turn Harness into ordinary repository operations, release management, or general project documentation unless the user explicitly frames the request as harness architecture.

Use the smallest discovery path:

- Ask a direct clarification when one missing fact blocks a reversible change.
- Interview the user with focused questions when an existing plan, design, or workflow needs
  decision-tree resolution, or when the product, problem, target user, or value proposition is
  unclear — resolve each open branch before choosing an architecture. A dedicated interviewing
  skill may be used when one is installed; never depend on one being available.

Produce a compact Purpose Brief before choosing a harness pattern. Proceed only when the brief is clear enough to select the smallest fitting workflow.

## Canonical Paths

Generated harnesses should prefer this layout:

```text
AGENTS.md                                  # short repo-wide guidance, only if needed
.agents/skills/{domain}-orchestrator/
  SKILL.md
  references/
.agents/skills/{specialist}/
  SKILL.md
  references/
docs/harness/{domain}/team-spec.md
docs/harness/{domain}/roles/{role}.md      # only when a role needs a durable brief
_workspace/{phase}_{role}_{artifact}.md
examples/benchmark-pack/scenarios.tsv       # when baseline comparison is part of the harness
examples/benchmark-pack/rubric.tsv
examples/benchmark-pack/expected-artifacts.md
_workspace/experiments/{run}/results.tsv    # benchmark run ledger
.codex/agents/{custom-agent}.toml           # optional repo-local helper only
.codex/config.toml                          # optional repo-local delegation config only
```

Every generated `SKILL.md` must begin with YAML frontmatter containing at least `name` and `description`. Keep descriptions concise and trigger-focused.

## Design Rules

- Keep root `AGENTS.md` short, human-written, and limited to repo-wide `WHAT / WHY / HOW`.
- Move bulky or conditional guidance into skill references or `docs/harness/`.
- Prefer file-based handoffs over assumed peer-to-peer runtime messaging.
- Keep the main agent responsible for requirements, synthesis, integration, and final acceptance.
- Allow bounded subagents when work is read-heavy, review-heavy, multi-part, or clearly parallelizable; do not ask for permission unless policy or user instructions require it.
- Prefer repo-local custom agents over global `default`, `explorer`, `worker`, or `reviewer` roles when the repo-local agent description is more specific to the task.
- Keep model-specific retries, brittle heuristics, and temporary recovery rules in removable reference sections.
- Keep task contracts model-agnostic: express outcome, success criteria, evidence, retrieval budget, validation, side-effect boundaries, and stop rules without pinning guidance to a specific model version.
- Avoid separate role files for roles that are too narrow, unstable, or single-use.
- Preserve intermediate artifacts when they help debugging, review, or repeatability.
- Keep generated names deterministic and repository-friendly.
- Restore user-facing clarity: adjust explanation density to the user's apparent expertise, but do not hide important limitations.
- If operation artifacts already exist, read and preserve them as current-state evidence. Operation documents own current status, task history, runbooks, and handoff notes; harness documents own durable workflow design, role contracts, review loops, and benchmark/scenario specifications.
- Do not duplicate long harness specs into operation summaries, and do not rewrite append-only task logs directly. When an operations record is needed, follow the repository's existing logging convention or leave a concise instruction for the main agent to record it.

## Phase 0: Existing Harness Audit

Before generating new artifacts, inspect current structure when available:

1. Read root `AGENTS.md` or equivalent project guidance.
2. List `.agents/skills/` and identify overlapping skill names or descriptions.
3. List `docs/harness/` and find team specs, role briefs, examples, or output contracts.
4. Check `_workspace/` conventions and whether old handoff files should be preserved.
5. Check optional `.codex/agents/` for custom-agent helpers.
6. Look for stale runtime assumptions, missing frontmatter, broken links, and duplicated responsibilities.
7. If the repository uses dryforge, inspect `.dryforge/NNN` archives when available to identify repeated review findings, missing evidence, failed gates, or repo-specific risk patterns. Do not rewrite archives.
8. Classify the request as one of:
   - new harness
   - extension of an existing harness
   - repair/refactor of a harness
   - maintenance/drift review
   - benchmark/evaluation pass

Output:

- audit summary
- reusable materials to preserve
- gaps or drift to repair
- narrow generation plan

## Phase 0.5: Instruction Surface Optimization

When a repository already has many instructions, optimize the existing instruction surface before adding new harness artifacts.

Classify guidance as:

- keep: safety rules, validation hard gates, durable repository conventions, and explicit user boundaries
- merge: duplicated rules across root guidance, skills, docs, or role briefs
- move: bulky conditional guidance into skill references or `docs/harness/`
- remove: stale runtime assumptions, obsolete recovery rules, and single-use workarounds
- upgrade: vague guidance that should become decision criteria, output contracts, validation rules, or stop/report rules

Preserve capability. Do not remove guidance solely because it is long. Prefer reducing duplication, trigger ambiguity, routing pressure, conflict, and stale specificity while keeping safety, validation, and repository-specific constraints intact.

Output an instruction inventory, findings, keep/merge/move/remove/upgrade plan, smallest safe patch plan, and validation note.

## Phase 1: Domain Analysis

1. Identify the domain, core task types, expected outputs, and quality bar.
2. Identify the user-facing outcome: code, research, review, documentation, experiment, or mixed workflow.
3. Detect the user's apparent expertise level:
   - beginner: explain concepts and avoid unexplained jargon
   - practitioner: keep guidance concise and operational
   - expert: preserve nuance, edge cases, and tradeoffs
4. Determine whether the workflow should be:
   - a single orchestrator skill
   - several specialist skills
   - role briefs plus a team spec
   - a benchmark/evaluation loop
   - optional Codex custom agents
5. Capture assumptions and constraints before generating files.
6. Define a model-agnostic outcome-first task contract with outcome, success criteria, scope, evidence requirements, retrieval budget, validation, side-effect boundary, stop/report rule, and completion packet.

Output:

- domain summary
- task inventory
- quality bar
- user-expertise note
- outcome-first task contract
- reuse notes from Phase 0

## Phase 2: Architecture Selection

Choose the smallest pattern that satisfies the final objective, success criteria, validation needs, and failure tolerance. Treat the current repository structure and maturity as constraints and sequencing evidence, not as a ceiling for the required work depth. See `references/agent-design-patterns.md`.

Use work depth deliberately:

- Lite: purpose clarification, audit, reversible recommendations, or a minimal repair plan.
- Standard: one orchestrator skill or team spec with handoff and validation contracts.
- Full: specialist skills, optional custom agents, benchmark packs, or review loops when final success requires repeatable multi-role execution or measured quality.

If the required depth is ambiguous, present 2-3 options instead of choosing silently. For each option, state the final success criteria it satisfies, what it does not satisfy, repository evidence, expected validation, overbuild/underbuild risk, and the recommended choice.

Avoid prescribing fixed repository archetypes. Choose from current evidence, user goals, structure, constraints, and validation needs. Use examples only to clarify file formats, schemas, or validation shape, not to imply a default architecture for unrelated repositories.

| Pattern | Best for | Portable Codex style |
| --- | --- | --- |
| Pipeline | sequential dependent work | orchestrator skill plus `_workspace/` handoffs |
| Fan-out/Fan-in | independent parallel slices with synthesis | bounded repo-local or global worker specs plus parent synthesis |
| Expert Pool | selective specialist routing | team spec with routing rules and reusable specialist skills |
| Producer-Reviewer | generation followed by quality review | producer skill, reviewer skill, and bounded repair loop |
| Supervisor | dynamic backlog allocation | top-level supervisor skill with explicit reassignment rules |
| Hierarchical Delegation | naturally layered decomposition | shallow hierarchy with one downstream coordination layer |

For autonomous experiment loops, read `references/autonomous-experimentation.md`. Treat autonomous experimentation as a workflow profile that composes with a pattern, not as a seventh architecture pattern.

Output:

- chosen pattern and why smaller patterns were insufficient
- role list
- handoff plan
- artifact naming convention
- optional subagent/custom-agent decision, including autonomous-use conditions

## Phase 3: Role and Artifact Definition

Define each stable role as one of:

- reusable specialist skill under `.agents/skills/`
- reusable orchestrator skill under `.agents/skills/`
- role brief under `docs/harness/{domain}/roles/`
- optional Codex custom agent under `.codex/agents/`

For each role, specify:

- responsibility
- inputs
- outputs
- handoff files
- review edges
- failure behavior
- whether the role should be invoked through skill matching, autonomous subagent routing, or explicit user request only

Output:

- role inventory
- file layout
- per-role input/output contract
- failure and escalation policy

## Phase 4: Skill Generation

1. Generate each reusable skill under `.agents/skills/`.
2. Start each `SKILL.md` with `name` and `description`.
3. Use concise trigger descriptions.
4. Move bulky details into `references/`.
5. Include:
   - when to use
   - when not to use
   - required inputs
   - workflow steps
   - expected outputs
   - validation notes
6. For a skill meant to help `dryforge go`, make it a review/explore/checklist lens and include a `## Dryforge go usage` section. Follow `references/go-compatible-skill-guide.md`.
7. Add helper scripts only when deterministic automation is safer than manual repetition.

Output:

- orchestrator skill, if needed
- specialist skills, if needed
- references for progressive disclosure
- optional helper scripts

## Phase 5: Integration and Orchestration

Define the end-to-end workflow in an orchestrator skill or team spec.

Include:

- phase order
- handoff filenames
- owner role for each artifact
- review and repair loops
- fallback rules
- optional subagent spawning instructions, including repo-local agent preference over generic global roles
- what stays stable versus what is removable recovery logic

For debate/synthesis tasks, use deterministic positions before synthesis:

```text
_workspace/{phase}_position_{role_or_view}.md
_workspace/{phase}_synthesis.md
_workspace/{phase}_decision.md
```

Do not collapse competing positions into one answer before recording the claims, evidence, and uncertainty that distinguish them.

Output:

- orchestrator/team spec
- `_workspace/` contract
- review and synthesis edges
- failure and retry policy

## Phase 6: Validation and Testing

Every generated harness should pass a structure and behavior review:

- Run this skill's helper as `python <harness-skill-dir>/scripts/validate_harness.py <repo>` when available; treat errors as blockers and warnings as review prompts.
- required paths exist
- skill frontmatter is valid
- references are linked and readable
- `AGENTS.md` remains short and pointer-heavy
- specialist skills and team specs agree on artifact names
- at least one normal scenario and one failure scenario are described
- QA/reviewer behavior is explicit when quality risk is high
- no platform-specific runtime assumption is required
- optional custom agents have `name`, `description`, and `developer_instructions`
- benchmark loops keep baseline, metric, and results ledger separate

When useful, compare:

- no-harness/manual baseline
- harness-guided output
- harness-guided output after review/repair

Output:

- validation checklist
- scenario tests
- issues found
- fixes applied or recommended

## Phase 7: Maintenance and Evolution

After validation, preserve a maintenance path:

1. Record adopted workflows in the generated harness maintenance notes or changelog, including the trigger, owner, validation evidence, and when to revisit it.
2. Record recurring failures and ambiguous triggers.
3. Track path drift across `AGENTS.md`, `.agents/skills/`, `docs/harness/`, and `_workspace/`.
4. Remove stale recovery logic when models or tools improve.
5. Keep a small changelog for generated harness revisions.
6. Update benchmarks when user goals, metrics, or accepted outputs change.
6. Preserve earlier useful artifacts instead of silently overwriting them.
7. Re-run validation after each material change.

Output:

- maintenance note
- drift findings
- changelog entry
- next benchmark or validation target

## Validation Expectations

A finished harness is acceptable when:

- the smallest sufficient architecture was selected
- generated files are discoverable by Codex and a repo-local skill discovery smoke test is recorded
- `python <harness-skill-dir>/scripts/validate_harness.py <repo>` passes when the helper script is available
- generated team specs or orchestrator skills include a model-agnostic outcome-first task contract
- root instructions are short
- handoff files are deterministic
- review loops are bounded
- user expertise needs are reflected in public instructions
- subagent usage is bounded, optional, scoped, and aligned with repo-local agent preference rules
- benchmark claims are backed by recorded results
- stale or legacy runtime assumptions are absent from canonical guidance

## Reference Pointers

- `references/agents-md-guide.md` for root guidance.
- `references/codex-subagents-guide.md` for optional custom agents and bounded subagent workflows.
- `references/agent-design-patterns.md` for architecture choice.
- `references/maintenance-and-drift.md` for Phase 0 and Phase 7 details.
- `references/user-expertise-and-tone.md` for adapting explanations.
- `references/benchmark-pack-guide.md` for baseline comparison.
- `references/skill-writing-guide.md` for skill authoring.
- `references/skill-testing-guide.md` for validation and iteration.
- `references/qa-agent-guide.md` for review methodology.
- `references/orchestrator-template.md` for reusable team specs.
- `references/team-examples.md` for examples.
