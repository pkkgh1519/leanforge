import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACES = ["src/skills", "codex/plugin/skills", "claude/skills"]
PRIME_DISPATCH_REFERENCES = [
    "prime/references/evidence-grounding-scout.md",
    "prime/references/intent-completeness.md",
    "prime/references/3-doc-gate.md",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def dispatch_block(rel: str) -> str:
    match = re.search(r"(?ms)^## Dispatch[^\n]*\n(.*?)(?=^## |\Z)", read(rel))
    if match is None:
        raise AssertionError(f"missing Dispatch block in {rel}")
    return match.group(1)


def host_dispatch_block(body: str, host: str) -> str:
    match = re.search(
        rf"(?ms)^  - \*\*{re.escape(host)}\.\*\*(.*?)(?=^  - \*\*|^- \*\*|\Z)",
        body,
    )
    if match is None:
        raise AssertionError(f"missing {host} dispatch block")
    return " ".join(match.group(1).split())


class RuntimeDispatchContractTests(unittest.TestCase):
    def test_prime_dispatch_contract_is_centralized_and_action_local(self):
        contract = " ".join(read("src/skills/prime/SKILL.md").lower().split())
        first_list = contract.find("list_agents")
        wait = contract.find("wait_agent", first_list + 1)
        relist = contract.find("re-list", wait + 1)
        spawn = contract.find("spawn_agent", relist + 1)
        self.assertTrue(
            -1 not in (first_list, wait, relist, spawn)
            and first_list < wait < relist < spawn,
            "Prime admission must order list -> wait/re-list -> spawn",
        )
        required = (
            "immediately before each",
            "one child at a time",
            "capacity-race",
            "second capacity rejection",
            "no state change",
            "capacity exhaustion",
            "bounded retry",
            "list failure",
            "never reactivate an idle child",
            "fresh child",
            "self-review",
        )
        missing = [term for term in required if term not in contract]
        self.assertFalse(missing, f"missing centralized Prime admission terms: {missing}")

        for rel in PRIME_DISPATCH_REFERENCES:
            with self.subTest(rel=rel):
                block = dispatch_block(f"src/skills/{rel}")
                self.assertIn("Apply Prime's action-local live-slot admission contract", block)
                self.assertIn('fork_turns: "none"', block)

    def test_codex_dispatches_are_explicit_fresh_leaf_children(self):
        required_paths = [
            "prime/SKILL.md",
            "prime/references/intent-completeness.md",
            "prime/references/evidence-grounding-scout.md",
            "prime/references/3-doc-gate.md",
            "run/SKILL.md",
            "run/references/implementer-prompt.md",
            "run/references/reviewer-prompt.md",
            "run/references/spec-review-prompt.md",
            "set/SKILL.md",
        ]
        for surface in SURFACES:
            for rel in required_paths:
                with self.subTest(surface=surface, rel=rel):
                    body = read(f"{surface}/{rel}")
                    self.assertIn('fork_turns: "none"', body)
                    self.assertRegex(body.lower(), r"\bleaf\b")
                    self.assertRegex(body.lower(), r"delegat|descendant")

    def test_compressed_dispatch_retains_role_capability_contract(self):
        for surface in SURFACES:
            with self.subTest(surface=surface, skill="prime"):
                prime = read(f"{surface}/prime/SKILL.md")
                for term in ("general-purpose", "full read/inspect tools", "plan-only", "search-only"):
                    self.assertIn(term, prime)

            with self.subTest(surface=surface, skill="run"):
                run = read(f"{surface}/run/SKILL.md")
                for term in ("general-purpose", "full read/edit/run tools", "plan-only", "search-only"):
                    self.assertIn(term, run)

    def test_compressed_prime_retains_state_recovery_choices(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                prime = read(f"{surface}/prime/SKILL.md")
                self.assertIn("ask which one is canonical", prime)
                self.assertIn("repair the active 3-doc", prime)

    def test_compressed_run_retains_integration_safety_details(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                run = read(f"{surface}/run/SKILL.md")
                flat = " ".join(run.split())
                self.assertIn("record what it skipped", flat)
                self.assertIn("fetch and confirm main has not moved", flat)
                self.assertIn("if it moved, re-integrate or escalate", flat)
                self.assertIn("Ask the user whether to resume or abandon", flat)
                self.assertIn("ask the user to regenerate the 3-doc through `Prime`", flat)
                self.assertIn("Force-load `references/harness-lifecycle.md` before any state-directory", flat)
                self.assertIn("branch task before its merge", flat)
                self.assertIn("collapsed or base-pinned work", flat)
                self.assertIn("exit codes captured and shown", flat)
                self.assertIn("After confirming the merge, clean up the feature branch", flat)
                self.assertIn(
                    "every spec requirement traces to a landed task, and every landed task traces to the spec",
                    flat,
                )
                gate = re.search(r"(?ms)^## Completion gate\n(.*?)(?=^## Finish)", run)
                self.assertIsNotNone(gate)
                self.assertNotIn("user approved", gate.group(1).lower())
                self.assertNotIn("final independent review", gate.group(1).lower())

    def test_compressed_run_completion_covers_every_planned_task_and_wave(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                run = read(f"{surface}/run/SKILL.md")
                gate = re.search(r"(?ms)^## Completion gate\n(.*?)(?=^## Finish)", run)
                self.assertIsNotNone(gate)
                body = " ".join(gate.group(1).split())
                for term in (
                    "every planned task",
                    "every wave",
                    "must not be counted complete",
                    "`BLOCKED`",
                    "worktree preserved",
                ):
                    self.assertIn(term, body)

    def test_successful_worktree_removal_waits_for_completion_gate(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                run = " ".join(read(f"{surface}/run/SKILL.md").split())
                orchestration = " ".join(
                    read(f"{surface}/run/references/orchestration.md").split()
                )
                self.assertIn(
                    "Do not remove successful task worktrees or branches before the completion gate passes",
                    run,
                )
                self.assertIn("after the completion gate passes", orchestration)
                self.assertIn("failed or ambiguous worktrees", orchestration)
                self.assertIn("in one batch", orchestration)
                self.assertIn("without `--force`", orchestration)
                self.assertIn("with `git branch -d`", orchestration)

                parallel = re.search(
                    r"(?ms)^### Parallel wave \(multiple tasks\)\n(.*?)(?=^### Advancing waves)",
                    read(f"{surface}/run/references/orchestration.md"),
                )
                self.assertIsNotNone(parallel)
                self.assertNotIn("**Clean up** task worktrees", parallel.group(1))

                failure = re.search(
                    r"(?ms)^## Failure handling\n(.*?)(?=^## Escalate)",
                    read(f"{surface}/run/references/orchestration.md"),
                )
                self.assertIsNotNone(failure)
                self.assertNotIn(
                    "Clean up only the successful worktrees",
                    failure.group(1),
                )
                self.assertNotIn("discarded failed task", failure.group(1))

    def test_reused_worktree_starts_a_fresh_branch_at_the_current_base_tip(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                run = " ".join(read(f"{surface}/run/SKILL.md").split())
                orchestration = read(
                    f"{surface}/run/references/orchestration.md"
                )
                pool = re.search(
                    r"(?ms)\*\*Worktree pool:\*\*(.*?)(?=^- \*\*Task worktrees)",
                    orchestration,
                )
                self.assertIsNotNone(pool)
                contract = " ".join(pool.group(1).split())

                required = (
                    "After the prior wave's gate/fix is green",
                    "serialize base writes through the next handoff",
                    "pin the current base-tip SHA",
                    "empty `git status --porcelain`",
                    "`git rev-parse HEAD`",
                    "require it to equal the previously verified `<prior-task-tip>` from the merge gate",
                    "`git merge-base --is-ancestor <prior-task-tip> <current-base-tip>`",
                    "new task branch name is absent",
                    "`git checkout -b <new-task-branch> <current-base-tip>`",
                    "Immediately before dispatch",
                    "base ref still resolves to `<current-base-tip>`",
                    "blocks and preserves the worktree",
                    "never force-reset or overwrite it",
                    "Preserve dirty, failed, ambiguous, stale-base, or branch-collision worktrees",
                )
                missing = [term for term in required if term not in contract]
                self.assertFalse(
                    missing,
                    f"missing safe pooled-worktree reuse terms: {missing}",
                )
                ordered = (
                    "After the prior wave's gate/fix is green",
                    "serialize base writes through the next handoff",
                    "pin the current base-tip SHA",
                    "empty `git status --porcelain`",
                    "`git rev-parse HEAD`",
                    "require it to equal the previously verified `<prior-task-tip>`",
                    "`git merge-base --is-ancestor",
                    "new task branch name is absent",
                    "`git checkout -b",
                    "Immediately before dispatch",
                    "base ref still resolves to `<current-base-tip>`",
                )
                positions = [contract.index(term) for term in ordered]
                self.assertEqual(
                    positions,
                    sorted(positions),
                    "pooled-worktree reuse checks must preserve the safe handoff order",
                )
                self.assertNotIn("reset --hard", contract)
                self.assertNotIn("git switch -C", contract)
                self.assertNotIn("git checkout -B", contract)

                for term in (
                    "current base-tip",
                    "prior task commit is an ancestor",
                    "new task branch",
                    "dirty, failed, ambiguous, stale-base, or branch-collision state",
                ):
                    self.assertIn(term, run)

    def test_conditional_spec_review_precedes_branch_merge(self):
        for surface in SURFACES:
            with self.subTest(surface=surface, wave="sequential"):
                orchestration = read(f"{surface}/run/references/orchestration.md")
                sequential = re.search(
                    r"(?ms)^### Sequential wave \(single task\)\n(.*?)(?=^### Parallel wave)",
                    orchestration,
                )
                self.assertIsNotNone(sequential)
                body = sequential.group(1)
                self.assertLess(
                    body.index("**Spec review**"),
                    body.index("**Land the RISKY branch**"),
                )

            with self.subTest(surface=surface, wave="parallel"):
                orchestration = read(f"{surface}/run/references/orchestration.md")
                parallel = re.search(
                    r"(?ms)^### Parallel wave \(multiple tasks\)\n(.*?)(?=^### Advancing waves)",
                    orchestration,
                )
                self.assertIsNotNone(parallel)
                body = parallel.group(1)
                self.assertLess(
                    body.index("**Spec review**"),
                    body.index("**Merge serially**"),
                )

    def test_runtime_capacity_contract_is_present(self):
        required = [
            "list_agents",
            "runtime_total_slots",
            "active_slot_consumers",
            "free_slots",
            "ready_dispatchable_tasks",
            "explicit_user_limit_or_infinity",
            "batch_size",
            "one child at a time",
        ]
        for surface in SURFACES:
            with self.subTest(surface=surface):
                combined = "\n".join(
                    [
                        read(f"{surface}/run/SKILL.md"),
                        read(f"{surface}/run/references/orchestration.md"),
                    ]
                )
                missing = [term for term in required if term not in combined]
                self.assertFalse(missing, f"missing dynamic-capacity terms: {missing}")

    def test_host_dispatch_paths_keep_codex_tools_out_of_claude_branch(self):
        paths = (
            "src/skills/prime/SKILL.md",
            "src/skills/run/references/orchestration.md",
            "src/skills/set/SKILL.md",
        )
        codex_tools = ("list_agents", "wait_agent", "spawn_agent")
        for rel in paths:
            body = read(rel)
            codex = host_dispatch_block(body, "Codex")
            claude = host_dispatch_block(body, "Claude Code")
            with self.subTest(rel=rel, host="Codex"):
                for tool in codex_tools:
                    self.assertIn(tool, codex)
            with self.subTest(rel=rel, host="Claude Code"):
                self.assertIn("`Agent`", claude)
                self.assertIn("one child at a time", claude)
                for tool in (*codex_tools, "followup_task", "send_message"):
                    self.assertNotIn(tool, claude)

                without_codex = re.sub(
                    r"(?ms)^  - \*\*Codex\.\*\*.*?(?=^  - \*\*|^- \*\*|\Z)",
                    "",
                    body,
                )
                for tool in (*codex_tools, "followup_task", "send_message"):
                    self.assertNotIn(tool, without_codex)

    def test_idle_child_reactivation_is_narrow_or_forbidden(self):
        for rel in ("src/skills/prime/SKILL.md", "src/skills/set/SKILL.md"):
            with self.subTest(rel=rel):
                codex = host_dispatch_block(read(rel), "Codex")
                self.assertIn("never reactivate an idle child", codex)
                self.assertIn("fresh child", codex)
                self.assertNotIn("followup_task", codex)

        run = host_dispatch_block(
            read("src/skills/run/references/orchestration.md"), "Codex"
        )
        for term in (
            "followup_task",
            "`NEEDS_CONTEXT`",
            "`BLOCKED`",
            "same graph task",
            "unchanged task contract",
            "same role",
            "same pinned work location",
            "different task or role",
            "any review or re-review",
            "`DONE`",
            "`DONE_WITH_CONCERNS`",
            "upgraded-model attempt",
            "fresh child",
        ):
            self.assertIn(term, run)

        run_claude = host_dispatch_block(
            read("src/skills/run/references/orchestration.md"), "Claude Code"
        )
        for term in (
            "`NEEDS_CONTEXT`",
            "`BLOCKED`",
            "immediately preceding structured status",
            "same task",
            "unchanged contract",
            "same role",
            "same pinned work location",
            "review",
            "re-review",
            "upgraded-model attempt",
            "`DONE`",
            "`DONE_WITH_CONCERNS`",
            "fix-dispatch",
            "fresh child",
        ):
            self.assertIn(term, run_claude)

    def test_run_dispatch_has_bounded_action_local_admission(self):
        orchestration = read("src/skills/run/references/orchestration.md")
        match = re.search(
            r"(?ms)^- \*\*Live-capacity contract\.\*\*(.*?)(?=^- \*\*Fresh leaf children\.\*\*)",
            orchestration,
        )
        self.assertIsNotNone(match)
        block = " ".join(match.group(1).lower().split())

        first_list = block.find("list_agents")
        wait = block.find("wait_agent", first_list + 1)
        relist = block.find("list_agents", wait + 1)
        spawn = block.find("spawn_agent", relist + 1)
        self.assertTrue(
            -1 not in (first_list, wait, relist, spawn)
            and first_list < wait < relist < spawn,
            "Run admission must order list -> bounded wait/re-list -> spawn",
        )
        required = (
            "immediately before each",
            "one child at a time",
            "capacity race",
            "second capacity rejection",
            "no state change",
            "capacity exhaustion",
            "bounded retry",
            "list failure",
            "followup_task",
            "send_message",
            "self-review",
        )
        missing = [term for term in required if term not in block]
        self.assertFalse(missing, f"missing bounded Run admission terms: {missing}")

    def test_set_review_has_bounded_action_local_admission(self):
        body = " ".join(read("src/skills/set/SKILL.md").lower().split())
        first_list = body.find("list_agents")
        wait = body.find("wait_agent", first_list + 1)
        relist = body.find("list_agents", wait + 1)
        spawn = body.find("spawn_agent", relist + 1)
        self.assertTrue(
            -1 not in (first_list, wait, relist, spawn)
            and first_list < wait < relist < spawn,
            "Set review admission must order list -> bounded wait/re-list -> spawn",
        )
        for term in (
            "one child at a time",
            "capacity race",
            "second capacity rejection",
            "no state change",
            "capacity exhaustion",
            "bounded retry",
            "self-review",
        ):
            self.assertIn(term, body)

    def test_stale_fixed_concurrency_contract_is_absent(self):
        stale = re.compile(
            r"≤\s*\d+\s*(?:concurrent|agents?|workers?)"
            r"|Practical parallelism\s*~\s*\d+"
            r"|(?:\d+|eight)\s+concurrent"
            r"|up to (?:\d+|eight)\s+(?:agents?|children|workers?)",
            re.IGNORECASE,
        )
        checked = [
            "prime/references/dependency-calc.md",
            "prime/references/output-format.md",
            "run/SKILL.md",
            "run/references/graph-contract.md",
            "run/references/orchestration.md",
        ]
        for surface in SURFACES:
            for rel in checked:
                with self.subTest(surface=surface, rel=rel):
                    body = read(f"{surface}/{rel}")
                    self.assertIsNone(stale.search(body))


if __name__ == "__main__":
    unittest.main()
