import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import adaptive_assurance_study as study  # noqa: E402


PREFIX = """# grounds gate

## Existing contract

Keep this behavior.
"""
SHADOW = """
## Adaptive Assurance shadow observation

At the **ELICIT exit**, write the advisory sidecar.
"""


def run(args, cwd):
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return completed.stdout.strip()


def create_fixture_repo(root: Path, *, generated_drift: bool = False) -> Path:
    repo = root / "repo"
    grounds = repo / study.GROUND_REL
    claude = repo / study.CLAUDE_GROUND_REL
    codex = repo / study.CODEX_GROUND_REL
    contract = repo / study.CONTRACT_REL
    build = repo / "build/build.sh"
    for path in (grounds, claude, codex, contract, build):
        path.parent.mkdir(parents=True, exist_ok=True)

    source = PREFIX + SHADOW
    grounds.write_text(source, encoding="utf-8", newline="\n")
    generated = PREFIX if generated_drift else source
    claude.write_text(generated, encoding="utf-8", newline="\n")
    codex.write_text(generated, encoding="utf-8", newline="\n")
    contract.write_text('{"schema_version":1}\n', encoding="utf-8")
    build.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
mkdir -p claude/skills/prime/references codex/plugin/skills/prime/references
cp src/skills/prime/references/grounds-gate.md claude/skills/prime/references/grounds-gate.md
cp src/skills/prime/references/grounds-gate.md codex/plugin/skills/prime/references/grounds-gate.md
""",
        encoding="utf-8",
        newline="\n",
    )
    os.chmod(build, 0o755)
    (repo / "other.txt").write_text("stable\n", encoding="utf-8")

    run(["git", "init", "-q"], repo)
    run(["git", "config", "user.email", "test@example.invalid"], repo)
    run(["git", "config", "user.name", "Test"], repo)
    run(["git", "add", "."], repo)
    run(["git", "commit", "-qm", "fixture"], repo)
    return repo


class AdaptiveAssuranceStudyControlTests(unittest.TestCase):
    def test_prepare_and_verify_are_deterministic_and_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            first = root / "first"
            second = root / "second"

            manifest1 = study.prepare_control(repo, first)
            manifest2 = study.prepare_control(repo, second)
            self.assertEqual(manifest1, manifest2)
            self.assertEqual(
                list(study.ALLOWED_CHANGED_PATHS), manifest1["changed_paths"]
            )
            self.assertEqual(manifest1, study.verify_control(first))
            self.assertEqual(manifest2, study.verify_control(second))

            candidate = (first / "candidate" / study.GROUND_REL).read_text(
                encoding="utf-8"
            )
            control = (first / "control" / study.GROUND_REL).read_text(
                encoding="utf-8"
            )
            self.assertIn(study.SHADOW_HEADING, candidate)
            self.assertNotIn(study.SHADOW_HEADING, control)
            self.assertTrue(candidate.startswith(control.rstrip() + "\n\n"))

    def test_manifest_provenance_uses_the_exported_pinned_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            pinned_commit = study.git(
                repo, "rev-parse", "--verify", "HEAD^{commit}"
            )
            manifest = study.prepare_control(repo, root / "workspace")

            self.assertEqual(pinned_commit, manifest["candidate"]["commit"])
            self.assertEqual(
                study.git(repo, "rev-parse", f"{pinned_commit}^{{tree}}"),
                manifest["candidate"]["git_tree"],
            )
            self.assertEqual(
                study.git(
                    repo,
                    "rev-parse",
                    f"{pinned_commit}:{study.CONTRACT_REL.as_posix()}",
                ),
                manifest["candidate"]["contract_blob_sha1"],
            )

    def test_prepare_fails_closed_if_head_moves_after_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "workspace"
            original_export = study.export_commit

            def export_then_advance(
                repo_path: Path, commit: str, destination: Path
            ) -> None:
                original_export(repo_path, commit, destination)
                (repo_path / "other.txt").write_text(
                    "advanced\n", encoding="utf-8"
                )
                run(["git", "add", "other.txt"], repo_path)
                run(["git", "commit", "-qm", "advance-head"], repo_path)

            with mock.patch.object(
                study, "export_commit", side_effect=export_then_advance
            ):
                with self.assertRaisesRegex(
                    study.StudyError, "HEAD changed while preparing"
                ):
                    study.prepare_control(repo, workspace)
            self.assertFalse(workspace.exists())

    def test_verify_rejects_any_extra_control_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "workspace"
            study.prepare_control(repo, workspace)
            (workspace / "control/other.txt").write_text(
                "tampered\n", encoding="utf-8"
            )
            with self.assertRaises(study.StudyError):
                study.verify_control(workspace)

    def test_prepare_refuses_generated_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root, generated_drift=True)
            with self.assertRaisesRegex(
                study.StudyError, "generated surfaces are not clean"
            ):
                study.prepare_control(repo, root / "workspace")

    def test_prepare_refuses_dirty_repo_and_workspace_inside_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(study.StudyError, "must be clean"):
                study.prepare_control(repo, root / "workspace")
            (repo / "dirty.txt").unlink()
            with self.assertRaisesRegex(study.StudyError, "must be outside"):
                study.prepare_control(repo, repo / "workspace")

    def test_manifest_schema_and_workspace_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "workspace"
            study.prepare_control(repo, workspace)

            manifest_path = workspace / study.MANIFEST_NAME
            value = json.loads(manifest_path.read_text(encoding="utf-8"))
            value["extra"] = True
            manifest_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(study.StudyError):
                study.verify_control(workspace)

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "workspace"
            tool = ROOT / "tools/adaptive_assurance_study.py"
            prepared = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "prepare-control",
                    "--repo",
                    str(repo),
                    "--workspace",
                    str(workspace),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, prepared.returncode, prepared.stderr)
            verified = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "verify-control",
                    "--workspace",
                    str(workspace),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, verified.returncode, verified.stderr)
            self.assertEqual(json.loads(prepared.stdout), json.loads(verified.stdout))


if __name__ == "__main__":
    unittest.main()
