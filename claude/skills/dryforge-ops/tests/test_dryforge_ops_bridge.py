import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dryforge_ops.py"


class BridgeCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dryforge-ops-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def init_ops(self, repo):
        ops = repo / ".agents" / "ops"
        ops.mkdir(parents=True)
        (ops / "operations.md").write_text("# 운영 요약\n", encoding="utf-8")
        (ops / "task-log.jsonl").write_text("", encoding="utf-8")

    def init_ready(self, repo):
        dry = repo / ".dryforge"
        dry.mkdir()
        for name in ("handoff.md", "spec.md", "plan.md"):
            (dry / name).write_text(f"# {name}\n", encoding="utf-8")

    def init_archive(self, repo, evidence=None):
        dry = repo / ".dryforge"
        archive = dry / "001"
        archive.mkdir(parents=True)
        (archive / "spec.md").write_text("# spec\n", encoding="utf-8")
        (archive / "plan.md").write_text("# plan\n", encoding="utf-8")
        (archive / "result.md").write_text("# result\n", encoding="utf-8")
        (dry / "status.json").write_text(json.dumps({"initialized": True}), encoding="utf-8")
        if evidence is not None:
            (archive / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    def read_events(self, repo):
        path = repo / ".agents" / "ops" / "task-log.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_assess_empty_repo(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        (repo / "README.md").write_text("# repo\n", encoding="utf-8")
        proc = self.run_cli("assess", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("dryforge_active=false", proc.stdout)
        self.assertIn("ops_summary=missing", proc.stdout)
        self.assertIn("task_log=missing", proc.stdout)
        self.assertFalse((repo / ".agents").exists())

    def test_after_ready_appends_once_and_updates_summary(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        self.init_ready(repo)
        proc = self.run_cli("after-ready", "--date", "2026-06-10", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        events = self.read_events(repo)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "planned")
        self.assertEqual(events[0]["status"], "open")
        self.assertIn("idempotency_key", events[0])
        summary = (repo / ".agents" / "ops" / "operations.md").read_text(encoding="utf-8")
        self.assertEqual(summary.count("## Dryforge 실행 상태"), 1)
        self.assertIn("<!-- dryforge-ops:start -->", summary)

        proc2 = self.run_cli("after-ready", "--date", "2026-06-10", str(repo))
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        self.assertEqual(len(self.read_events(repo)), 1)
        summary2 = (repo / ".agents" / "ops" / "operations.md").read_text(encoding="utf-8")
        self.assertEqual(summary2.count("## Dryforge 실행 상태"), 1)

    def test_corrupt_jsonl_blocks_after_ready(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        self.init_ready(repo)
        log = repo / ".agents" / "ops" / "task-log.jsonl"
        log.write_text("{bad json\n", encoding="utf-8")
        before_summary = (repo / ".agents" / "ops" / "operations.md").read_text(encoding="utf-8")
        proc = self.run_cli("after-ready", str(repo))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("JSONL corruption", proc.stderr)
        self.assertEqual(log.read_text(encoding="utf-8"), "{bad json\n")
        self.assertEqual((repo / ".agents" / "ops" / "operations.md").read_text(encoding="utf-8"), before_summary)

    def test_after_go_completed_with_evidence(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        self.init_archive(repo, {"commands": [{"command": "npm run test", "exit_code": 0, "source": "test fixture"}]})
        proc = self.run_cli("after-go", "--date", "2026-06-10", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        events = self.read_events(repo)
        self.assertEqual(events[-1]["event"], "completed")
        self.assertEqual(events[-1]["status"], "completed")
        self.assertEqual(events[-1]["evidence"]["commands"][0]["exit_code"], 0)
        evidence_file = repo / ".agents" / "ops" / "evidence" / "task-2026-06-10-dryforge-go.evidence.json"
        self.assertTrue(evidence_file.exists())
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
        self.assertEqual(evidence["schema_version"], "dryforge-ops.evidence.v1")
        self.assertTrue(evidence["completion_allowed"])
        self.assertIn("npm run test", evidence["commands"][0]["command"])
        ledger_file = repo / ".agents" / "ops" / "ledger.json"
        self.assertTrue(ledger_file.exists())
        ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
        self.assertEqual(ledger["schema_version"], "dryforge-ops.ledger.v1")
        self.assertEqual(ledger["entries"][0]["evidence_json"], ".agents/ops/evidence/task-2026-06-10-dryforge-go.evidence.json")

        proc2 = self.run_cli("after-go", "--date", "2026-06-10", str(repo))
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        self.assertEqual(len(self.read_events(repo)), 1)

    def test_after_go_no_evidence_cannot_complete(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        self.init_archive(repo)
        proc = self.run_cli("after-go", "--date", "2026-06-10", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        event = self.read_events(repo)[-1]
        self.assertNotEqual((event["event"], event["status"]), ("completed", "completed"))
        self.assertEqual((event["event"], event["status"]), ("needs_review", "pending"))
        summary = (repo / ".agents" / "ops" / "operations.md").read_text(encoding="utf-8")
        self.assertIn("missing", summary)

    def test_after_go_failed_evidence_blocks_completion(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        self.init_archive(repo, {"commands": [{"command": "npm run test", "exit_code": 1}]})
        proc = self.run_cli("after-go", "--date", "2026-06-10", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        event = self.read_events(repo)[-1]
        self.assertEqual((event["event"], event["status"]), ("validated", "blocked"))
        self.assertIn("exit 1", event["validation"][0])

    def test_doctor_outputs_health_and_recommended_action(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        proc = self.run_cli("doctor", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("health=warn", proc.stdout)
        self.assertIn("recommended_next_action=", proc.stdout)

    def test_preflight_detects_latest_blocked_event(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        log = repo / ".agents" / "ops" / "task-log.jsonl"
        log.write_text(json.dumps({"task_id": "task-blocked", "event": "blocked", "status": "blocked", "date": "2026-06-10", "summary": "blocked"}, ensure_ascii=False) + "\n", encoding="utf-8")
        proc = self.run_cli("preflight", "--strict", str(repo))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("preflight_status=blocked", proc.stdout)
        self.assertIn("repo_ops_blocked", proc.stdout)

    def test_before_go_records_preflight_event(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        self.init_ready(repo)
        proc = self.run_cli("before-go", "--date", "2026-06-10", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        events = self.read_events(repo)
        self.assertEqual(events[-1]["event"], "preflight")
        self.assertIn(events[-1]["status"], {"open", "pending_review"})
        repeat = self.run_cli("before-go", "--date", "2026-06-10", str(repo))
        self.assertEqual(repeat.returncode, 0, repeat.stderr)
        self.assertEqual(len(self.read_events(repo)), 1)

    def test_after_ready_dry_run_writes_nothing(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        self.init_ready(repo)
        proc = self.run_cli("after-ready", "--dry-run", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.read_events(repo), [])
        summary = (repo / ".agents" / "ops" / "operations.md").read_text(encoding="utf-8")
        self.assertNotIn("Dryforge 실행 상태", summary)

    def test_handoff_does_not_overwrite(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        target = repo / ".agents" / "ops" / "handoffs" / "handoff-2026-06-10.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("keep\n", encoding="utf-8")
        proc = self.run_cli("handoff", ".agents/ops/handoffs/handoff-2026-06-10.md", str(repo))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("already exists", proc.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")

    def test_render_dashboard_uses_proposed_file_when_existing(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        dashboard = repo / ".agents" / "ops" / "dashboard.html"
        dashboard.write_text("keep\n", encoding="utf-8")
        proc = self.run_cli("dashboard", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(dashboard.read_text(encoding="utf-8"), "keep\n")
        self.assertTrue((repo / ".agents" / "ops" / "dashboard.proposed.html").exists())

    def test_suggest_delegates_to_harness(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        log = repo / ".agents" / "ops" / "task-log.jsonl"
        events = [
            {"task_id": f"task-{i}", "event": "completed", "status": "completed", "date": "2026-06-10", "type": "security-review", "summary": "보안 검토"}
            for i in range(3)
        ]
        log.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")
        proc = self.run_cli("workflow", "suggest", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("workflow_candidate=security-review", proc.stdout)
        self.assertIn("confidence=medium", proc.stdout)
        self.assertIn("evidence_task_ids=task-0,task-1,task-2", proc.stdout)
        self.assertIn("delegate_to=harness skill", proc.stdout)

    def test_legacy_task_log_is_read_for_workflow_suggest_but_preserved(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        legacy_ops = repo / "docs" / "operations"
        legacy_ops.mkdir(parents=True)
        legacy_log = legacy_ops / "task-log.jsonl"
        events = [
            {"task_id": f"legacy-{i}", "event": "completed", "status": "completed", "date": "2026-06-10", "type": "qa", "summary": "테스트"}
            for i in range(3)
        ]
        original = "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events)
        legacy_log.write_text(original, encoding="utf-8")

        proc = self.run_cli("workflow", "suggest", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("workflow_candidate=qa", proc.stdout)
        self.assertIn("evidence_task_ids=legacy-0,legacy-1,legacy-2", proc.stdout)
        self.assertEqual(legacy_log.read_text(encoding="utf-8"), original)
        self.assertFalse((repo / ".agents" / "ops" / "task-log.jsonl").exists())

    def write_event(self, payload):
        path = self.tmp / "event.json"
        path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def test_log_appends_adhoc_event_and_updates_summary(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        event = self.write_event({"task_id": "task-adhoc", "event": "progress", "status": "open", "date": "2026-06-10", "type": "docs", "summary": "ad-hoc 문서 작업"})
        proc = self.run_cli("log", "--event", str(event), str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        events = self.read_events(repo)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["task_id"], "task-adhoc")
        self.assertEqual(events[0]["type"], "docs")
        summary = (repo / ".agents" / "ops" / "operations.md").read_text(encoding="utf-8")
        self.assertIn("<!-- dryforge-ops:start -->", summary)

    def test_log_fills_date_and_task_id_defaults(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        event = self.write_event({"event": "progress", "status": "open", "summary": "기본값 채움"})
        proc = self.run_cli("log", "--event", str(event), "--date", "2026-06-10", str(repo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        recorded = self.read_events(repo)[0]
        self.assertEqual(recorded["date"], "2026-06-10")
        self.assertEqual(recorded["task_id"], "task-2026-06-10-ops-log")

    def test_log_refuses_completed_without_evidence(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        event = self.write_event({"task_id": "task-x", "event": "completed", "status": "completed", "date": "2026-06-10", "summary": "증거 없음"})
        proc = self.run_cli("log", "--event", str(event), str(repo))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("completed/completed refused", proc.stderr)
        self.assertEqual(self.read_events(repo), [])

    def test_log_allows_completed_with_evidence_via_stdin(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        payload = json.dumps({
            "task_id": "task-x", "event": "completed", "status": "completed", "date": "2026-06-10",
            "summary": "증거 포함", "evidence": {"commands": [{"command": "pytest", "exit_code": 0}]},
        }, ensure_ascii=False)
        proc = self.run_cli("log", "--event", "-", str(repo), stdin=payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.read_events(repo)[0]["status"], "completed")

    def test_log_refuses_missing_ops_plane(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        event = self.write_event({"task_id": "task-x", "event": "progress", "status": "open", "date": "2026-06-10", "summary": "plane 없음"})
        proc = self.run_cli("log", "--event", str(event), str(repo))
        self.assertEqual(proc.returncode, 2)
        self.assertIn(".agents/ops", proc.stderr)
        self.assertFalse((repo / ".agents").exists())

    def test_log_idempotency_key_skips_duplicate(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        event = self.write_event({"task_id": "task-x", "event": "progress", "status": "open", "date": "2026-06-10", "summary": "재실행 안전"})
        first = self.run_cli("log", "--event", str(event), "--idempotency-key", "adhoc-1", str(repo))
        second = self.run_cli("log", "--event", str(event), "--idempotency-key", "adhoc-1", str(repo))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(len(self.read_events(repo)), 1)

    def test_workflow_suggest_suppresses_adopted_until_recurrence(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ops(repo)
        log = repo / ".agents" / "ops" / "task-log.jsonl"

        def qa_events(start, count):
            return "".join(
                json.dumps({"task_id": f"task-qa-{i}", "event": "completed", "status": "completed", "date": "2026-06-10", "type": "qa", "summary": "테스트"}, ensure_ascii=False) + "\n"
                for i in range(start, start + count)
            )

        log.write_text(qa_events(0, 3), encoding="utf-8")
        before = self.run_cli("workflow", "suggest", str(repo))
        self.assertIn("workflow_candidate=qa", before.stdout)

        adopted = self.write_event({"task_id": "task-qa-adopt", "event": "workflow_adopted", "status": "adopted", "date": "2026-06-10", "workflow": "qa", "summary": "qa workflow 채택"})
        logged = self.run_cli("log", "--event", str(adopted), str(repo))
        self.assertEqual(logged.returncode, 0, logged.stderr)
        suppressed = self.run_cli("workflow", "suggest", str(repo))
        self.assertNotIn("workflow_candidate=qa", suppressed.stdout)
        self.assertIn("adopted_workflows=qa", suppressed.stdout)

        with log.open("a", encoding="utf-8") as fh:
            fh.write(qa_events(10, 3))
        recurred = self.run_cli("workflow", "suggest", str(repo))
        self.assertIn("workflow_candidate=qa", recurred.stdout)
        self.assertIn("evidence_task_ids=task-qa-10,task-qa-11,task-qa-12", recurred.stdout)

    def test_unsafe_operations_symlink_rejected_when_supported(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.init_ready(repo)
        outside = self.tmp / "outside"
        outside.mkdir()
        agents = repo / ".agents"
        agents.mkdir()
        link = agents / "ops"
        try:
            os.symlink(outside, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is not supported in this environment")
        (outside / "operations.md").write_text("# outside\n", encoding="utf-8")
        (outside / "task-log.jsonl").write_text("", encoding="utf-8")
        proc = self.run_cli("after-ready", str(repo))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unsafe", proc.stderr.lower())
        self.assertEqual((outside / "task-log.jsonl").read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()

