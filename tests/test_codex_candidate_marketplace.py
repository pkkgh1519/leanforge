import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import codex_candidate_marketplace as candidate  # noqa: E402


def run(args, cwd):
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(completed.stderr)
    return completed.stdout.strip()


def create_fixture_repo(root: Path) -> Path:
    repo = root / "repo"
    plugin = repo / "codex/plugin"
    manifest = plugin / ".codex-plugin/plugin.json"
    skill = plugin / "skills/prime/SKILL.md"
    build = repo / "build/build.sh"
    for path in (manifest, skill, build):
        path.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        '{"name":"leanforge","version":"1.9.0","skills":"./skills/"}\n',
        encoding="utf-8",
        newline="\n",
    )
    skill.write_text("---\nname: prime\n---\n\nFixture.\n", encoding="utf-8", newline="\n")
    build.write_text("#!/usr/bin/env bash\nset -euo pipefail\n", encoding="utf-8", newline="\n")
    os.chmod(build, 0o755)

    run(["git", "init", "-q"], repo)
    run(["git", "config", "user.email", "test@example.invalid"], repo)
    run(["git", "config", "user.name", "Test"], repo)
    run(["git", "add", "."], repo)
    run(["git", "commit", "-qm", "fixture"], repo)
    return repo


class CodexCandidateMarketplaceTests(unittest.TestCase):
    def test_prepare_and_verify_active_are_closed_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "candidate"

            manifest = candidate.prepare(repo, workspace)
            self.assertEqual(candidate.KIND, manifest["kind"])
            self.assertEqual(
                manifest["package"]["source_sha256"],
                manifest["package"]["staged_sha256"],
            )
            self.assertTrue(
                manifest["marketplace"]["name"].startswith("leanforge-candidate-")
            )
            self.assertEqual(manifest, candidate.verify_workspace(workspace))

            active = root / "active"
            shutil_source = workspace / manifest["marketplace"]["plugin_path"]
            import shutil

            shutil.copytree(shutil_source, active)
            verified = candidate.verify_active(workspace, active)
            self.assertTrue(verified["match"])
            self.assertEqual(
                manifest["package"]["staged_sha256"], verified["active_sha256"]
            )

    def test_prepare_refuses_dirty_repo_existing_or_inside_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(candidate.CandidateError, "must be clean"):
                candidate.prepare(repo, root / "candidate")
            (repo / "dirty.txt").unlink()

            with self.assertRaisesRegex(candidate.CandidateError, "outside"):
                candidate.prepare(repo, repo / "candidate")

            existing = root / "existing"
            existing.mkdir()
            with self.assertRaisesRegex(candidate.CandidateError, "already exists"):
                candidate.prepare(repo, existing)

    def test_verify_rejects_tampered_staged_and_active_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "candidate"
            manifest = candidate.prepare(repo, workspace)
            staged = workspace / manifest["marketplace"]["plugin_path"]
            (staged / "skills/prime/SKILL.md").write_text(
                "tampered\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(candidate.CandidateError, "no longer matches"):
                candidate.verify_workspace(workspace)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "candidate"
            manifest = candidate.prepare(repo, workspace)
            active = root / "active"
            import shutil

            shutil.copytree(workspace / manifest["marketplace"]["plugin_path"], active)
            (active / "extra.txt").write_text("extra\n", encoding="utf-8")
            with self.assertRaisesRegex(candidate.CandidateError, "digest mismatch"):
                candidate.verify_active(workspace, active)

    def test_manifest_and_marketplace_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "candidate"
            candidate.prepare(repo, workspace)

            manifest_path = workspace / candidate.MANIFEST_NAME
            value = json.loads(manifest_path.read_text(encoding="utf-8"))
            value["extra"] = True
            manifest_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(candidate.CandidateError):
                candidate.verify_workspace(workspace)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "candidate"
            candidate.prepare(repo, workspace)
            marketplace_path = workspace / candidate.MARKETPLACE_REL
            value = json.loads(marketplace_path.read_text(encoding="utf-8"))
            value["plugins"][0]["source"]["path"] = "./other"
            marketplace_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(candidate.CandidateError, "marketplace"):
                candidate.verify_workspace(workspace)

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = create_fixture_repo(root)
            workspace = root / "candidate"
            tool = ROOT / "tools/codex_candidate_marketplace.py"
            prepared = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "prepare",
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
                    "verify-workspace",
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

            digest = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "digest",
                    "--path",
                    str(workspace / candidate.STAGED_PLUGIN_REL),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, digest.returncode, digest.stderr)
            digest_value = json.loads(digest.stdout)
            self.assertEqual(
                json.loads(prepared.stdout)["package"]["staged_sha256"],
                digest_value["tree_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
