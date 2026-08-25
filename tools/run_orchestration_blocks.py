#!/usr/bin/env python3
"""Render and verify the behavior-preserving Run orchestration block split."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


MANIFEST_REL = Path("src/instruction-blocks/run/orchestration/manifest.json")
TOP_LEVEL_KEYS = {
    "schema_version",
    "split_id",
    "authority",
    "compatibility_mode",
    "output",
    "baseline",
    "runtime_baseline",
    "blocks",
}
OUTPUT_KEYS = {"path", "bytes", "sha256"}
BASELINE_KEYS = {
    "commit",
    "tree",
    "path",
    "blob_sha1",
    "bytes",
    "sha256",
    "load_graph_path",
    "load_graph_blob_sha1",
}
RUNTIME_BASELINE_KEYS = {"path", "blob_sha1", "bytes", "sha256"}
BLOCK_KEYS = {"path", "start_heading", "bytes", "sha256"}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_SPLIT_ID = "leanforge.run.orchestration-blocks.v1"
EXPECTED_COMPATIBILITY_MODE = "materialized_monolith"
EXPECTED_BASELINE = {
    "commit": "e5b3cbc4778be190bd2c3c4477450e8f3c34e0cb",
    "tree": "b87ec08e9c840c4d585e9cc7d89a9826a98c2c5f",
    "path": "src/skills/run/references/orchestration.md",
    "blob_sha1": "f2fd63356adb0ba47e806e87802392b0f8ce6d4a",
    "bytes": 36790,
    "sha256": "e9aaca31d8b31d4a473ff9b9268b96b1eefe768a28bf2254ce8eff2228d79f03",
    "load_graph_path": "src/skills/run/references/load-graph.json",
    "load_graph_blob_sha1": "4d619bd160c334e2497c8f16de077c0428f8073a",
}
EXPECTED_RUNTIME_BASELINE = (
    (
        "src/skills/run/SKILL.md",
        "7bba81a50fe399f49275d981d9ec765ca180d82f",
        26071,
        "76786dc604c3be1a6e634015f7666df0a505b0be2c8cab84fb9ebccf06de75d2",
    ),
    (
        "src/skills/run/references/load-graph.json",
        "4d619bd160c334e2497c8f16de077c0428f8073a",
        4084,
        "e956bc0eed66c111422a9e62e5c02037a19411a29f224f9244a8c3a4dd448d4d",
    ),
    (
        "src/skills/run/references/semantic-contract.json",
        "ba98ce4fadf4c173c774cb342455a3bef085f6ee",
        21600,
        "1fe9818bbb91101007bd4b87fdb325c7c606515406ac3eec475cb2805cfb4dac",
    ),
)
EXPECTED_BLOCK_ROOT = PurePosixPath("src/instruction-blocks/run/orchestration")
EXPECTED_OUTPUT = "src/skills/run/references/orchestration.md"
EXPECTED_RUNTIME_PATHS = (
    "src/skills/run/SKILL.md",
    "src/skills/run/references/load-graph.json",
    "src/skills/run/references/semantic-contract.json",
)
EXPECTED_BLOCKS = (
    (
        "src/instruction-blocks/run/orchestration/00-preamble-and-verification.md",
        "# orchestration.md — wave lifecycle (force-load)",
    ),
    (
        "src/instruction-blocks/run/orchestration/10-routing-and-dispatch-roi.md",
        "## Wave scheduling",
    ),
    (
        "src/instruction-blocks/run/orchestration/20-sequential-execution.md",
        "## Sequential wave — execution",
    ),
    (
        "src/instruction-blocks/run/orchestration/30-parallel-worktree-constraints.md",
        "## Parallel wave — dispatch constraints (safety, non-negotiable; unordered)",
    ),
    (
        "src/instruction-blocks/run/orchestration/40-agent-status-and-context.md",
        "## Agent status protocol",
    ),
    (
        "src/instruction-blocks/run/orchestration/50-sequential-wave-lifecycle.md",
        "### Sequential wave (single task)",
    ),
    (
        "src/instruction-blocks/run/orchestration/60-parallel-wave-lifecycle.md",
        "### Parallel wave (multiple tasks)",
    ),
    (
        "src/instruction-blocks/run/orchestration/70-wave-advancement-and-concerns.md",
        "### Advancing waves",
    ),
    (
        "src/instruction-blocks/run/orchestration/80-remediation-and-failure.md",
        "### Fix-dispatch and lightweight fix",
    ),
)


class SplitError(RuntimeError):
    """Closed validation failure for the orchestration split."""


def _closed(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise SplitError(
            f"{where} keys must be closed; "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )


def _object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SplitError(f"{where} must be an object")
    return value


def _non_empty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise SplitError(f"{where} must be a non-empty string")
    return value


def _strict_int(value: Any, where: str) -> int:
    if type(value) is not int or value < 0:
        raise SplitError(f"{where} must be a non-negative integer")
    return value


def _digest(value: Any, pattern: re.Pattern[str], where: str) -> str:
    text = _non_empty_string(value, where)
    if pattern.fullmatch(text) is None:
        raise SplitError(f"{where} has an invalid digest")
    return text


def _safe_relative(value: Any, where: str) -> PurePosixPath:
    text = _non_empty_string(value, where)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise SplitError(f"{where} must be a safe relative POSIX path")
    if "\\" in text or path.as_posix() != text:
        raise SplitError(f"{where} must use a normalized relative POSIX path")
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_regular_bytes(path: Path, where: str) -> bytes:
    if path.is_symlink():
        raise SplitError(f"{where} must not be a symlink: {path}")
    try:
        if not path.is_file():
            raise SplitError(f"{where} must be a regular file: {path}")
        return path.read_bytes()
    except OSError as exc:
        raise SplitError(f"cannot read {where} {path}: {exc}") from exc


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            _read_regular_bytes(path, "manifest").decode("utf-8")
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SplitError(f"cannot parse manifest {path}: {exc}") from exc
    return _object(value, "manifest")


def load_manifest(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    manifest_path = repo / MANIFEST_REL
    manifest = _read_json(manifest_path)
    _closed(manifest, TOP_LEVEL_KEYS, "manifest")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise SplitError("unsupported manifest schema_version")
    if manifest["split_id"] != EXPECTED_SPLIT_ID:
        raise SplitError("unexpected split_id")
    if manifest["authority"] != "ordered_blocks":
        raise SplitError("authority must be ordered_blocks")
    if manifest["compatibility_mode"] != EXPECTED_COMPATIBILITY_MODE:
        raise SplitError(
            f"compatibility_mode must be {EXPECTED_COMPATIBILITY_MODE}"
        )

    output = _object(manifest["output"], "manifest.output")
    _closed(output, OUTPUT_KEYS, "manifest.output")
    output_path = _safe_relative(output["path"], "manifest.output.path")
    if output_path.as_posix() != EXPECTED_OUTPUT:
        raise SplitError("manifest.output.path is not the compatibility monolith")
    _strict_int(output["bytes"], "manifest.output.bytes")
    _digest(output["sha256"], SHA256_RE, "manifest.output.sha256")

    baseline = _object(manifest["baseline"], "manifest.baseline")
    _closed(baseline, BASELINE_KEYS, "manifest.baseline")
    _digest(baseline["commit"], SHA1_RE, "manifest.baseline.commit")
    _digest(baseline["tree"], SHA1_RE, "manifest.baseline.tree")
    _digest(baseline["blob_sha1"], SHA1_RE, "manifest.baseline.blob_sha1")
    _digest(
        baseline["load_graph_blob_sha1"],
        SHA1_RE,
        "manifest.baseline.load_graph_blob_sha1",
    )
    baseline_path = _safe_relative(baseline["path"], "manifest.baseline.path")
    if baseline_path != output_path:
        raise SplitError("baseline path must equal the compatibility output path")
    load_graph_path = _safe_relative(
        baseline["load_graph_path"], "manifest.baseline.load_graph_path"
    )
    if load_graph_path.as_posix() != "src/skills/run/references/load-graph.json":
        raise SplitError("baseline load graph path is unexpected")
    _strict_int(baseline["bytes"], "manifest.baseline.bytes")
    _digest(baseline["sha256"], SHA256_RE, "manifest.baseline.sha256")
    if baseline["bytes"] != output["bytes"] or baseline["sha256"] != output["sha256"]:
        raise SplitError("baseline and output identities must match")
    if baseline != EXPECTED_BASELINE:
        raise SplitError("manifest baseline identity differs from the reviewed Full baseline")
    if output != {
        "path": EXPECTED_BASELINE["path"],
        "bytes": EXPECTED_BASELINE["bytes"],
        "sha256": EXPECTED_BASELINE["sha256"],
    }:
        raise SplitError("manifest output identity differs from the reviewed Full baseline")

    runtime = manifest["runtime_baseline"]
    if not isinstance(runtime, list):
        raise SplitError("manifest.runtime_baseline must be an array")
    runtime_paths: list[str] = []
    for index, entry_value in enumerate(runtime):
        entry = _object(entry_value, f"manifest.runtime_baseline[{index}]")
        _closed(entry, RUNTIME_BASELINE_KEYS, f"manifest.runtime_baseline[{index}]")
        path = _safe_relative(entry["path"], f"manifest.runtime_baseline[{index}].path")
        runtime_paths.append(path.as_posix())
        _digest(
            entry["blob_sha1"],
            SHA1_RE,
            f"manifest.runtime_baseline[{index}].blob_sha1",
        )
        _strict_int(entry["bytes"], f"manifest.runtime_baseline[{index}].bytes")
        _digest(entry["sha256"], SHA256_RE, f"manifest.runtime_baseline[{index}].sha256")
    if tuple(runtime_paths) != EXPECTED_RUNTIME_PATHS:
        raise SplitError("runtime_baseline paths or order changed")
    runtime_identity = tuple(
        (entry["path"], entry["blob_sha1"], entry["bytes"], entry["sha256"])
        for entry in runtime
    )
    if runtime_identity != EXPECTED_RUNTIME_BASELINE:
        raise SplitError("runtime baseline identity differs from the reviewed Full baseline")

    blocks = manifest["blocks"]
    if not isinstance(blocks, list) or not blocks:
        raise SplitError("manifest.blocks must be a non-empty array")
    paths: list[str] = []
    headings: list[str] = []
    for index, block_value in enumerate(blocks):
        block = _object(block_value, f"manifest.blocks[{index}]")
        _closed(block, BLOCK_KEYS, f"manifest.blocks[{index}]")
        path = _safe_relative(block["path"], f"manifest.blocks[{index}].path")
        if path.parent != EXPECTED_BLOCK_ROOT or path.suffix != ".md":
            raise SplitError("block paths must be Markdown files under the canonical block root")
        paths.append(path.as_posix())
        headings.append(
            _non_empty_string(
                block["start_heading"],
                f"manifest.blocks[{index}].start_heading",
            )
        )
        _strict_int(block["bytes"], f"manifest.blocks[{index}].bytes")
        _digest(block["sha256"], SHA256_RE, f"manifest.blocks[{index}].sha256")
    if len(paths) != len(set(paths)):
        raise SplitError("block paths must be unique")
    if paths != sorted(paths):
        raise SplitError("block paths must be in deterministic lexical order")
    if len(headings) != len(set(headings)):
        raise SplitError("block start headings must be unique")
    if tuple(zip(paths, headings)) != EXPECTED_BLOCKS:
        raise SplitError("block paths, headings, or order changed")
    return manifest


def render(repo: Path, manifest: Mapping[str, Any] | None = None) -> bytes:
    repo = repo.resolve()
    value = load_manifest(repo) if manifest is None else dict(manifest)
    chunks: list[bytes] = []
    for index, block in enumerate(value["blocks"]):
        path = repo / block["path"]
        data = _read_regular_bytes(path, "block")
        if len(data) != block["bytes"]:
            raise SplitError(f"block byte length mismatch: {block['path']}")
        if _sha256(data) != block["sha256"]:
            raise SplitError(f"block digest mismatch: {block['path']}")
        heading_prefix = block["start_heading"].encode("utf-8") + b"\n"
        expected_prefix = heading_prefix if index == 0 else b"\n" + heading_prefix
        if not data.startswith(expected_prefix):
            raise SplitError(f"block start heading or boundary separator mismatch: {block['path']}")
        if b"\r" in data:
            raise SplitError(f"block contains CR bytes: {block['path']}")
        if not data.endswith(b"\n"):
            raise SplitError(f"block must end with exactly one LF: {block['path']}")
        if data.endswith(b"\n\n"):
            raise SplitError(f"block must not add a blank line at EOF: {block['path']}")
        chunks.append(data)
    result = b"".join(chunks)
    output = value["output"]
    if len(result) != output["bytes"]:
        raise SplitError("rendered monolith byte length mismatch")
    if _sha256(result) != output["sha256"]:
        raise SplitError("rendered monolith digest mismatch")
    return result


def _git(repo: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise SplitError(f"cannot execute git: {exc}") from exc
    if completed.returncode:
        details = completed.stderr.decode("utf-8", errors="replace").strip()
        raise SplitError(f"git {' '.join(args)} failed: {details}")
    return completed.stdout


def verify(repo: Path, *, require_git_baseline: bool = True) -> dict[str, Any]:
    repo = repo.resolve()
    manifest = load_manifest(repo)
    rendered = render(repo, manifest)
    output_path = repo / manifest["output"]["path"]
    output = _read_regular_bytes(output_path, "compatibility monolith")
    if output != rendered:
        raise SplitError("compatibility monolith differs from ordered block rendering")

    baseline = manifest["baseline"]
    runtime_verified: list[str] = []
    for entry in manifest["runtime_baseline"]:
        current = _read_regular_bytes(
            repo / entry["path"],
            "runtime compatibility surface",
        )
        if len(current) != entry["bytes"] or _sha256(current) != entry["sha256"]:
            raise SplitError(f"runtime compatibility surface changed: {entry['path']}")
        runtime_verified.append(entry["path"])

    if require_git_baseline:
        commit = baseline["commit"]
        commit_object = _git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
        if commit_object != commit:
            raise SplitError("baseline commit identity mismatch")
        tree = _git(repo, "rev-parse", f"{commit}^{{tree}}").decode().strip()
        if tree != baseline["tree"]:
            raise SplitError("baseline tree identity mismatch")
        blob = _git(repo, "rev-parse", f"{commit}:{baseline['path']}").decode().strip()
        if blob != baseline["blob_sha1"]:
            raise SplitError("baseline orchestration blob identity mismatch")
        baseline_bytes = _git(repo, "show", f"{commit}:{baseline['path']}")
        if baseline_bytes != rendered:
            raise SplitError("ordered blocks do not reconstruct the exact baseline Git blob")
        load_graph_blob = _git(
            repo, "rev-parse", f"{commit}:{baseline['load_graph_path']}"
        ).decode().strip()
        if load_graph_blob != baseline["load_graph_blob_sha1"]:
            raise SplitError("baseline load graph blob identity mismatch")

        for entry in manifest["runtime_baseline"]:
            current = _read_regular_bytes(
            repo / entry["path"],
            "runtime compatibility surface",
        )
            historical_blob = _git(
                repo, "rev-parse", f"{commit}:{entry['path']}"
            ).decode().strip()
            if historical_blob != entry["blob_sha1"]:
                raise SplitError(f"runtime baseline blob identity mismatch: {entry['path']}")
            historical = _git(repo, "show", f"{commit}:{entry['path']}")
            if historical != current:
                raise SplitError(f"runtime compatibility bytes changed: {entry['path']}")

    return {
        "schema_version": 1,
        "split_id": manifest["split_id"],
        "output_path": manifest["output"]["path"],
        "output_bytes": len(rendered),
        "output_sha256": _sha256(rendered),
        "block_count": len(manifest["blocks"]),
        "baseline_commit": baseline["commit"] if require_git_baseline else None,
        "baseline_verified": require_git_baseline,
        "runtime_surfaces_verified": runtime_verified,
    }


def sync(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    manifest = load_manifest(repo)
    rendered = render(repo, manifest)
    output_path = repo / manifest["output"]["path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    previous = (
        _read_regular_bytes(output_path, "compatibility monolith")
        if output_path.exists()
        else None
    )
    changed = previous != rendered
    if changed:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=output_path.name + ".",
            suffix=".tmp",
            dir=output_path.parent,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, output_path)
        finally:
            temporary.unlink(missing_ok=True)
    return {
        "schema_version": 1,
        "split_id": manifest["split_id"],
        "output_path": manifest["output"]["path"],
        "output_bytes": len(rendered),
        "output_sha256": _sha256(rendered),
        "changed": changed,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("sync", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo", type=Path, required=True)
    verify_command = commands.choices["verify"]
    verify_command.add_argument(
        "--no-git-baseline",
        action="store_true",
        help="verify block and monolith bytes without historical Git objects",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    try:
        if args.command == "sync":
            result = sync(args.repo)
        else:
            result = verify(args.repo, require_git_baseline=not args.no_git_baseline)
    except SplitError as exc:
        argument_parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
