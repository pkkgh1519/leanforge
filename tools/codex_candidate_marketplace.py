#!/usr/bin/env python3
"""Prepare and verify a reversible local Codex marketplace for one Git commit."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from adaptive_assurance_study import tree_digest


class CandidateError(RuntimeError):
    pass


SCHEMA_VERSION = 1
KIND = "leanforge.codex-local-candidate"
MANIFEST_NAME = "leanforge-candidate-manifest.json"
PLUGIN_REL = Path("codex/plugin")
MARKETPLACE_REL = Path(".agents/plugins/marketplace.json")
STAGED_PLUGIN_REL = Path("plugins/leanforge")


def run(args: Sequence[str], cwd: Path) -> bytes:
    try:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise CandidateError(f"cannot execute {args[0]!r}: {exc}") from exc
    if completed.returncode:
        stdout = completed.stdout.decode("utf-8", errors="replace").strip()
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        details = "\n".join(part for part in (stdout, stderr) if part)
        raise CandidateError(
            f"command failed ({completed.returncode}): {' '.join(args)}"
            + (f"\n{details}" if details else "")
        )
    return completed.stdout


def bash_executable() -> str:
    candidates: list[Path] = []
    if os.name == "nt":
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(env_name)
            if root:
                candidates.append(Path(root) / "Git" / "bin" / "bash.exe")
    discovered = shutil.which("bash")
    if discovered:
        candidates.append(Path(discovered))
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    raise CandidateError("Git Bash or bash is required to run build/build.sh")


def git(repo: Path, *args: str) -> str:
    return run(("git", *args), repo).decode("utf-8").strip()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def exact_keys(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise CandidateError(
            f"{where} keys must be closed; missing={sorted(expected-actual)}, "
            f"extra={sorted(actual-expected)}"
        )


def require_repo_root(repo: Path) -> None:
    try:
        top = Path(git(repo, "rev-parse", "--show-toplevel")).resolve()
    except CandidateError as exc:
        raise CandidateError(f"candidate repository is not a Git worktree: {repo}") from exc
    if top != repo.resolve():
        raise CandidateError(f"--repo must be the Git worktree root: expected {top}")


def require_clean(repo: Path) -> None:
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise CandidateError("candidate repository must be clean")


def marketplace_name(commit: str) -> str:
    return f"leanforge-candidate-{commit[:12]}"


def marketplace_value(name: str, short_commit: str) -> dict[str, Any]:
    return {
        "name": name,
        "interface": {"displayName": f"Leanforge Candidate {short_commit}"},
        "plugins": [
            {
                "name": "leanforge",
                "source": {
                    "source": "local",
                    "path": "./plugins/leanforge",
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Productivity",
            }
        ],
    }


def validate_manifest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CandidateError("candidate manifest root must be an object")
    exact_keys(
        value,
        {"schema_version", "kind", "candidate", "marketplace", "package"},
        "candidate manifest",
    )
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise CandidateError("unsupported candidate manifest schema_version")
    if value["kind"] != KIND:
        raise CandidateError("unsupported candidate manifest kind")

    candidate = value["candidate"]
    marketplace = value["marketplace"]
    package = value["package"]
    if not isinstance(candidate, dict) or not isinstance(marketplace, dict) or not isinstance(package, dict):
        raise CandidateError("candidate manifest children must be objects")
    exact_keys(candidate, {"commit", "git_tree"}, "candidate manifest.candidate")
    exact_keys(
        marketplace,
        {"name", "manifest_path", "plugin_path"},
        "candidate manifest.marketplace",
    )
    exact_keys(
        package,
        {"source_sha256", "staged_sha256"},
        "candidate manifest.package",
    )
    for where, child in (
        ("candidate", candidate),
        ("marketplace", marketplace),
        ("package", package),
    ):
        if not all(isinstance(item, str) and item for item in child.values()):
            raise CandidateError(f"candidate manifest.{where} values must be non-empty strings")
    if marketplace["manifest_path"] != MARKETPLACE_REL.as_posix():
        raise CandidateError("candidate marketplace manifest path mismatch")
    if marketplace["plugin_path"] != STAGED_PLUGIN_REL.as_posix():
        raise CandidateError("candidate marketplace plugin path mismatch")
    if package["source_sha256"] != package["staged_sha256"]:
        raise CandidateError("candidate source and staged package digests differ")
    return value


def manifest_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        return validate_manifest(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateError(f"cannot read candidate manifest {path}: {exc}") from exc


def prepare(repo: Path, workspace: Path) -> dict[str, Any]:
    repo, workspace = repo.resolve(), workspace.resolve()
    require_repo_root(repo)
    require_clean(repo)
    if is_inside(workspace, repo):
        raise CandidateError("candidate workspace must be outside the repository")
    if workspace.exists():
        raise CandidateError(f"candidate workspace already exists: {workspace}")

    pinned_commit = git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    pinned_tree = git(repo, "rev-parse", f"{pinned_commit}^{{tree}}")
    source = repo / PLUGIN_REL
    if not (source / ".codex-plugin/plugin.json").is_file():
        raise CandidateError("candidate repository is missing codex/plugin/.codex-plugin/plugin.json")

    run((bash_executable(), "build/build.sh"), repo)
    if git(repo, "rev-parse", "--verify", "HEAD^{commit}") != pinned_commit:
        raise CandidateError("candidate HEAD changed during build")
    require_clean(repo)

    source_digest = tree_digest(source)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=workspace.name + ".tmp-", dir=workspace.parent))
    try:
        staged_plugin = staging / STAGED_PLUGIN_REL
        staged_plugin.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, staged_plugin, symlinks=True, copy_function=shutil.copy2)
        staged_digest = tree_digest(staged_plugin)
        if staged_digest != source_digest:
            raise CandidateError("copied candidate package digest differs from source")

        name = marketplace_name(pinned_commit)
        marketplace_path = staging / MARKETPLACE_REL
        marketplace_path.parent.mkdir(parents=True, exist_ok=True)
        marketplace_path.write_text(
            json.dumps(marketplace_value(name, pinned_commit[:12]), indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "kind": KIND,
            "candidate": {"commit": pinned_commit, "git_tree": pinned_tree},
            "marketplace": {
                "name": name,
                "manifest_path": MARKETPLACE_REL.as_posix(),
                "plugin_path": STAGED_PLUGIN_REL.as_posix(),
            },
            "package": {
                "source_sha256": source_digest,
                "staged_sha256": staged_digest,
            },
        }
        validate_manifest(manifest)
        (staging / MANIFEST_NAME).write_bytes(manifest_bytes(manifest))
        os.replace(staging, workspace)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def verify_workspace(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    manifest = load_manifest(workspace / MANIFEST_NAME)
    staged = workspace / manifest["marketplace"]["plugin_path"]
    actual = tree_digest(staged)
    if actual != manifest["package"]["staged_sha256"]:
        raise CandidateError("staged candidate package no longer matches its manifest")
    marketplace_path = workspace / manifest["marketplace"]["manifest_path"]
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateError(f"cannot read candidate marketplace: {exc}") from exc
    if marketplace != marketplace_value(
        manifest["marketplace"]["name"], manifest["candidate"]["commit"][:12]
    ):
        raise CandidateError("candidate marketplace no longer matches its manifest")
    return manifest


def verify_active(workspace: Path, active_path: Path) -> dict[str, Any]:
    manifest = verify_workspace(workspace)
    active = active_path.resolve()
    actual = tree_digest(active)
    expected = manifest["package"]["staged_sha256"]
    if actual != expected:
        raise CandidateError(
            f"active Codex package digest mismatch: expected={expected}, actual={actual}"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "leanforge.codex-local-candidate-verification",
        "candidate_commit": manifest["candidate"]["commit"],
        "marketplace_name": manifest["marketplace"]["name"],
        "expected_sha256": expected,
        "active_sha256": actual,
        "match": True,
    }


def digest_path(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "leanforge.package-identity",
        "path": str(resolved),
        "tree_sha256": tree_digest(resolved),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    prepare_command = commands.add_parser("prepare")
    prepare_command.add_argument("--repo", type=Path, required=True)
    prepare_command.add_argument("--workspace", type=Path, required=True)

    verify_command = commands.add_parser("verify-workspace")
    verify_command.add_argument("--workspace", type=Path, required=True)

    active_command = commands.add_parser("verify-active")
    active_command.add_argument("--workspace", type=Path, required=True)
    active_command.add_argument("--active-path", type=Path, required=True)

    digest_command = commands.add_parser("digest")
    digest_command.add_argument("--path", type=Path, required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    try:
        if args.command == "prepare":
            value = prepare(args.repo, args.workspace)
        elif args.command == "verify-workspace":
            value = verify_workspace(args.workspace)
        elif args.command == "verify-active":
            value = verify_active(args.workspace, args.active_path)
        else:
            value = digest_path(args.path)
    except CandidateError as exc:
        argument_parser.error(str(exc))
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
