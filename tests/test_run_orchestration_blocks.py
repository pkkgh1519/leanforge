from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import run_orchestration_blocks as split  # noqa: E402


BASELINE_COMMIT = "e5b3cbc4778be190bd2c3c4477450e8f3c34e0cb"
BASELINE_TREE = "b87ec08e9c840c4d585e9cc7d89a9826a98c2c5f"
BASELINE_BLOB = "f2fd63356adb0ba47e806e87802392b0f8ce6d4a"
BASELINE_SHA256 = "e9aaca31d8b31d4a473ff9b9268b96b1eefe768a28bf2254ce8eff2228d79f03"
BASELINE_BYTES = 36790
SPLIT_RELEASE_COMMIT = "7607933eae58e166283789409ccd37a66fddcacd"
RUNTIME_SURFACES = (
    "src/skills/run",
    "claude/skills/run",
    "codex/plugin/skills/run",
)


def git(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout


def copy_minimal_repository(destination: Path) -> Path:
    repo = destination / "repo"
    manifest = split.load_manifest(ROOT)
    relatives = [
        split.MANIFEST_REL,
        Path(manifest["output"]["path"]),
        *[Path(item["path"]) for item in manifest["runtime_baseline"]],
        *[Path(item["path"]) for item in manifest["blocks"]],
    ]
    for relative in dict.fromkeys(relatives):
        source = ROOT / relative
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return repo


class RunOrchestrationBlockSplitTests(unittest.TestCase):
    def test_exact_baseline_and_closed_manifest_verify(self):
        manifest = split.load_manifest(ROOT)
        result = split.verify(ROOT)

        self.assertEqual(BASELINE_COMMIT, manifest["baseline"]["commit"])
        self.assertEqual(BASELINE_TREE, manifest["baseline"]["tree"])
        self.assertEqual(BASELINE_BLOB, manifest["baseline"]["blob_sha1"])
        self.assertEqual(BASELINE_BYTES, manifest["output"]["bytes"])
        self.assertEqual(BASELINE_SHA256, manifest["output"]["sha256"])
        self.assertEqual(9, len(manifest["blocks"]))
        self.assertTrue(result["baseline_verified"])
        self.assertEqual(9, result["block_count"])
        self.assertEqual(BASELINE_SHA256, result["output_sha256"])
        self.assertFalse(result["split_release_runtime_enforced"])
        self.assertEqual([], result["runtime_surfaces_verified"])

        for index, block in enumerate(manifest["blocks"]):
            data = (ROOT / block["path"]).read_bytes()
            self.assertTrue(data.endswith(b"\n"), block["path"])
            self.assertFalse(data.endswith(b"\n\n"), block["path"])
            self.assertEqual(index > 0, data.startswith(b"\n"), block["path"])

    def test_blocks_reconstruct_the_exact_baseline_git_blob(self):
        rendered = split.render(ROOT)
        historical = git("show", f"{BASELINE_COMMIT}:src/skills/run/references/orchestration.md")

        self.assertEqual(historical, rendered)
        self.assertEqual(BASELINE_BYTES, len(rendered))
        self.assertEqual(b"\n", rendered[-1:])
        self.assertNotIn(b"\r", rendered)

    def test_split_release_packaged_run_surface_was_unchanged_from_baseline(self):
        for surface in RUNTIME_SURFACES:
            with self.subTest(surface=surface):
                baseline_paths = tuple(
                    sorted(
                        line
                        for line in git(
                            "ls-tree", "-r", "--name-only", BASELINE_COMMIT, surface
                        ).decode("utf-8").splitlines()
                        if line
                    )
                )
                split_paths = tuple(
                    sorted(
                        line
                        for line in git(
                            "ls-tree", "-r", "--name-only", SPLIT_RELEASE_COMMIT, surface
                        ).decode("utf-8").splitlines()
                        if line
                    )
                )
                self.assertEqual(baseline_paths, split_paths)
                for relative in baseline_paths:
                    self.assertEqual(
                        git("show", f"{BASELINE_COMMIT}:{relative}"),
                        git("show", f"{SPLIT_RELEASE_COMMIT}:{relative}"),
                        relative,
                    )

    def test_blocks_are_source_only_and_not_runtime_load_nodes(self):
        graph = json.loads(
            (ROOT / "src/skills/run/references/load-graph.json").read_text(encoding="utf-8")
        )
        node_paths = {node["path"] for node in graph["nodes"]}
        self.assertTrue(all("instruction-blocks" not in path for path in node_paths))
        self.assertFalse((ROOT / "claude/instruction-blocks").exists())
        self.assertFalse((ROOT / "codex/plugin/instruction-blocks").exists())

    def test_ownership_and_release_boundary_are_documented(self):
        root_contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        claude_contract = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        source_contract = (ROOT / "src/AGENTS.md").read_text(encoding="utf-8")
        build_contract = (ROOT / "build/AGENTS.md").read_text(encoding="utf-8")
        decision = (
            ROOT
            / "docs/tracking/decisions/0004-run-orchestration-block-source.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(root_contract, claude_contract)
        self.assertIn("src/instruction-blocks/", root_contract)
        self.assertIn(
            "src/instruction-blocks/run/orchestration/",
            source_contract,
        )
        self.assertIn("자동 sync하거나 수리하지 않는다", build_contract)
        self.assertIn("conditional block loading", decision)
        self.assertIn("plugin package에 source block 포함", decision)
        self.assertIn("e5b3cbc4778be190bd2c3c4477450e8f3c34e0cb", decision)

    def test_bash_3_2_workflow_exercises_build_and_focused_contracts(self):
        workflow = (
            ROOT / ".github/workflows/bash-3.2.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("runs-on: macos-latest", workflow)
        self.assertIn("/bin/bash --version", workflow)
        self.assertIn("3.2.*", workflow)
        self.assertIn("/bin/bash build/build.sh", workflow)
        self.assertIn("tests.test_run_orchestration_blocks", workflow)
        self.assertIn("tests.test_release_consistency", workflow)
        self.assertIn("git diff --exit-code -- claude codex", workflow)

    def test_build_verifies_before_plugin_copy_and_never_auto_repairs(self):
        build = (ROOT / "build/build.sh").read_text(encoding="utf-8")
        sync_command = 'run_orchestration_blocks.py" sync --repo'
        verify_command = 'run_orchestration_blocks.py" verify --repo'
        first_copy = 'cp -R "$SRC" "$ROOT/claude/skills"'

        self.assertNotIn(sync_command, build)
        self.assertEqual(1, build.count(verify_command))
        self.assertLess(build.index(verify_command), build.index(first_copy))

    def test_sync_repairs_only_the_monolith_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_minimal_repository(Path(tmp))
            output = repo / split.EXPECTED_OUTPUT
            output.write_text("drift\n", encoding="utf-8")

            first = split.sync(repo)
            second = split.sync(repo)
            verified = split.verify(repo, require_git_baseline=False)

            self.assertTrue(first["changed"])
            self.assertFalse(second["changed"])
            self.assertEqual(BASELINE_SHA256, verified["output_sha256"])
            self.assertEqual(split.render(repo), output.read_bytes())

    def test_manifest_envelope_and_topology_mutations_fail_closed(self):
        mutations = (
            lambda value: value.update({"extra": True}),
            lambda value: value.pop("authority"),
            lambda value: value["blocks"].reverse(),
            lambda value: value["blocks"].append(copy.deepcopy(value["blocks"][0])),
            lambda value: value["blocks"][0].update({"path": "../outside.md"}),
            lambda value: value["blocks"][0].update({"start_heading": "# changed"}),
            lambda value: value["runtime_baseline"].reverse(),
            lambda value: value["output"].update({"path": "src/skills/run/references/other.md"}),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index), tempfile.TemporaryDirectory() as tmp:
                repo = copy_minimal_repository(Path(tmp))
                manifest_path = repo / split.MANIFEST_REL
                value = json.loads(manifest_path.read_text(encoding="utf-8"))
                mutation(value)
                manifest_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
                with self.assertRaises(split.SplitError):
                    split.load_manifest(repo)

    def test_reviewed_identity_cannot_be_rewritten_through_manifest_updates(self):
        mutations = (
            lambda value: value["baseline"].update(
                {"commit": "0" * 40}
            ),
            lambda value: (
                value["output"].update({"sha256": "0" * 64}),
                value["baseline"].update({"sha256": "0" * 64}),
            ),
            lambda value: value["runtime_baseline"][0].update(
                {"sha256": "0" * 64}
            ),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=index), tempfile.TemporaryDirectory() as tmp:
                repo = copy_minimal_repository(Path(tmp))
                manifest_path = repo / split.MANIFEST_REL
                value = json.loads(manifest_path.read_text(encoding="utf-8"))
                mutation(value)
                manifest_path.write_text(
                    json.dumps(value, indent=2) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    split.SplitError,
                    "reviewed Full baseline",
                ):
                    split.load_manifest(repo)

    def test_coordinated_block_manifest_and_monolith_rewrite_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_minimal_repository(Path(tmp))
            manifest_path = repo / split.MANIFEST_REL
            value = json.loads(manifest_path.read_text(encoding="utf-8"))
            block_path = repo / value["blocks"][0]["path"]
            block = block_path.read_bytes().replace(
                b"wave lifecycle", b"wave lifecyclf", 1
            )
            block_path.write_bytes(block)
            value["blocks"][0]["sha256"] = split._sha256(block)
            rendered = b"".join(
                (repo / item["path"]).read_bytes()
                for item in value["blocks"]
            )
            value["output"]["sha256"] = split._sha256(rendered)
            value["baseline"]["sha256"] = split._sha256(rendered)
            (repo / value["output"]["path"]).write_bytes(rendered)
            manifest_path.write_text(
                json.dumps(value, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                split.SplitError,
                "reviewed Full baseline",
            ):
                split.verify(repo, require_git_baseline=False)

    def test_block_byte_crlf_missing_and_output_mutations_fail_closed(self):
        mutation_names = ("byte", "crlf", "missing", "output")
        for mutation_name in mutation_names:
            with self.subTest(mutation=mutation_name), tempfile.TemporaryDirectory() as tmp:
                repo = copy_minimal_repository(Path(tmp))
                manifest = split.load_manifest(repo)
                block = repo / manifest["blocks"][0]["path"]
                if mutation_name == "byte":
                    block.write_bytes(block.read_bytes().replace(b"wave lifecycle", b"wave lifecyclf", 1))
                elif mutation_name == "crlf":
                    block.write_bytes(block.read_bytes().replace(b"\n", b"\r\n", 1))
                elif mutation_name == "missing":
                    block.unlink()
                else:
                    (repo / manifest["output"]["path"]).write_text("drift\n", encoding="utf-8")
                with self.assertRaises(split.SplitError):
                    split.verify(repo, require_git_baseline=False)

    def test_missing_runtime_surface_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_minimal_repository(Path(tmp))
            path = repo / split.EXPECTED_RUNTIME_PATHS[0]
            path.unlink()
            with self.assertRaisesRegex(
                split.SplitError,
                "runtime compatibility surface must be a regular file",
            ):
                split.verify(
                    repo,
                    require_git_baseline=False,
                    enforce_split_release_runtime=True,
                )

    def test_runtime_surface_mutation_is_rejected_against_git_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "clone"
            subprocess.run(
                ["git", "clone", "--shared", "--no-hardlinks", str(ROOT), str(clone)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            subprocess.run(
                ["git", "checkout", "--detach", BASELINE_COMMIT],
                cwd=clone,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            shutil.copytree(
                ROOT / "src/instruction-blocks",
                clone / "src/instruction-blocks",
            )
            path = clone / "src/skills/run/references/load-graph.json"
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(split.SplitError, "runtime compatibility surface changed"):
                split.verify(clone, enforce_split_release_runtime=True)


if __name__ == "__main__":
    unittest.main()
