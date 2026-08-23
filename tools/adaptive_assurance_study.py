#!/usr/bin/env python3
"""Prepare and verify a deterministic shadow-disabled A/B study workspace."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class StudyError(RuntimeError):
    pass


SCHEMA_VERSION = 1
CONTROL_KIND = "leanforge.adaptive-assurance.shadow-disabled-control"
SHADOW_HEADING = "## Adaptive Assurance shadow observation"
GROUND_REL = Path("src/skills/prime/references/grounds-gate.md")
CLAUDE_GROUND_REL = Path("claude/skills/prime/references/grounds-gate.md")
CODEX_GROUND_REL = Path("codex/plugin/skills/prime/references/grounds-gate.md")
GROUND_PATHS = tuple(
    sorted(
        path.as_posix()
        for path in (GROUND_REL, CLAUDE_GROUND_REL, CODEX_GROUND_REL)
    )
)
ALLOWED_CHANGED_PATHS = GROUND_PATHS
CONTRACT_REL = Path(
    "src/skills/prime/references/adaptive-assurance-contract.json"
)
MANIFEST_NAME = "adaptive-assurance-control-manifest.json"


def run(args: Sequence[str], cwd: Path) -> bytes:
    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise StudyError(f"cannot execute {args[0]!r}: {exc}") from exc
    if result.returncode:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise StudyError(
            f"command failed ({result.returncode}): {' '.join(args)}"
            + (f"\n{error}" if error else "")
        )
    return result.stdout


def git(repo: Path, *args: str) -> str:
    return run(("git", *args), repo).decode("utf-8").strip()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def require_clean_repo(repo: Path) -> None:
    if not (repo / ".git").exists():
        raise StudyError(f"candidate repository has no .git entry: {repo}")
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise StudyError("candidate repository must be clean before study pinning")


def export_commit(repo: Path, commit: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    archive_path = destination.parent / f"{destination.name}.tar"
    try:
        run(
            (
                "git",
                "archive",
                "--format=tar",
                "--output",
                str(archive_path),
                commit,
            ),
            repo,
        )
        root = destination.resolve()
        with tarfile.open(archive_path, "r:") as archive:
            for member in archive.getmembers():
                try:
                    (destination / member.name).resolve().relative_to(root)
                except ValueError as exc:
                    raise StudyError(
                        f"git archive contains unsafe path: {member.name}"
                    ) from exc
            try:
                archive.extractall(destination, filter="data")
            except TypeError:  # Python < 3.12
                archive.extractall(destination)
    finally:
        archive_path.unlink(missing_ok=True)


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file() or path.is_symlink():
            yield path


def file_bytes(path: Path) -> bytes:
    return os.readlink(path).encode("utf-8") if path.is_symlink() else path.read_bytes()


def file_mode(path: Path) -> str:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISREG(mode):
        return "100755" if mode & stat.S_IXUSR else "100644"
    raise StudyError(f"unsupported file kind: {path}")


def tree_digest(root: Path) -> str:
    if not root.is_dir():
        raise StudyError(f"digest root is not a directory: {root}")
    digest = hashlib.sha256()
    for path in iter_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        mode = file_mode(path).encode("ascii")
        content = file_bytes(path)
        for value in (relative, mode, content):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    return digest.hexdigest()


def build(root: Path) -> None:
    if not (root / "build/build.sh").is_file():
        raise StudyError("exported tree is missing build/build.sh")
    run(("bash", "build/build.sh"), root)


def strip_shadow(path: Path) -> tuple[bytes, bytes]:
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StudyError("grounds-gate.md is not valid UTF-8") from exc
    marker = f"\n{SHADOW_HEADING}\n"
    if text.count(marker) != 1:
        raise StudyError("shadow heading must occur exactly once")
    control = text.split(marker, 1)[0].rstrip() + "\n"
    path.write_text(control, encoding="utf-8", newline="\n")
    return original, control.encode("utf-8")


def relative_files(root: Path) -> dict[str, Path]:
    return {path.relative_to(root).as_posix(): path for path in iter_files(root)}


def changed_paths(candidate: Path, control: Path) -> tuple[str, ...]:
    left, right = relative_files(candidate), relative_files(control)
    if left.keys() != right.keys():
        raise StudyError("candidate and control file sets differ")
    return tuple(
        path
        for path in sorted(left)
        if file_mode(left[path]) != file_mode(right[path])
        or file_bytes(left[path]) != file_bytes(right[path])
    )


def hook_surfaces(candidate: Path, control: Path) -> tuple[bytes, bytes]:
    candidate_values = [file_bytes(candidate / path) for path in GROUND_PATHS]
    control_values = [file_bytes(control / path) for path in GROUND_PATHS]
    if len(set(candidate_values)) != 1 or len(set(control_values)) != 1:
        raise StudyError("source/Claude/Codex grounds-gate bytes are not identical")
    candidate_bytes, control_bytes = candidate_values[0], control_values[0]
    marker = f"\n{SHADOW_HEADING}\n".encode()
    if candidate_bytes.count(marker) != 1 or marker in control_bytes:
        raise StudyError("candidate/control shadow-hook boundary is invalid")
    expected = candidate_bytes.split(marker, 1)[0].rstrip() + b"\n"
    if control_bytes != expected:
        raise StudyError("control is not the exact pre-hook candidate prefix")
    return candidate_bytes, control_bytes


def patch_digest(candidate: bytes, control: bytes) -> str:
    diff = difflib.unified_diff(
        candidate.decode().splitlines(keepends=True),
        control.decode().splitlines(keepends=True),
        fromfile=f"candidate/{GROUND_REL.as_posix()}",
        tofile=f"control/{GROUND_REL.as_posix()}",
        lineterm="\n",
    )
    return hashlib.sha256("".join(diff).encode()).hexdigest()


def identities(root: Path) -> dict[str, str]:
    return {
        "tree_sha256": tree_digest(root),
        "src_skills_sha256": tree_digest(root / "src/skills"),
        "claude_package_sha256": tree_digest(root / "claude"),
        "codex_package_sha256": tree_digest(root / "codex/plugin"),
    }


def exact_keys(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise StudyError(
            f"{where} keys must be closed; missing={sorted(expected-actual)}, "
            f"extra={sorted(actual-expected)}"
        )


def validate_manifest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StudyError("manifest root must be an object")
    exact_keys(
        value,
        {"schema_version", "control_kind", "candidate", "control", "hook", "changed_paths"},
        "manifest",
    )
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise StudyError("unsupported manifest schema_version")
    if value["control_kind"] != CONTROL_KIND:
        raise StudyError("unsupported manifest control_kind")
    candidate_keys = {
        "commit", "git_tree", "contract_blob_sha1", "tree_sha256",
        "src_skills_sha256", "claude_package_sha256", "codex_package_sha256",
    }
    identity_keys = {
        "tree_sha256", "src_skills_sha256", "claude_package_sha256", "codex_package_sha256",
    }
    hook_keys = {"heading", "candidate_sha256", "control_sha256", "patch_sha256"}
    for name, keys in (("candidate", candidate_keys), ("control", identity_keys), ("hook", hook_keys)):
        child = value[name]
        if not isinstance(child, dict):
            raise StudyError(f"manifest.{name} must be an object")
        exact_keys(child, keys, f"manifest.{name}")
        if not all(isinstance(item, str) and item for item in child.values()):
            raise StudyError(f"manifest.{name} values must be non-empty strings")
    if value["hook"]["heading"] != SHADOW_HEADING:
        raise StudyError("manifest hook heading mismatch")
    if value["changed_paths"] != list(GROUND_PATHS):
        raise StudyError("manifest changed_paths mismatch")
    return value


def manifest_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def write_manifest(path: Path, value: Mapping[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(manifest_bytes(value))
    os.replace(temporary, path)


def prepare_control(repo: Path, workspace: Path) -> dict[str, Any]:
    repo, workspace = repo.resolve(), workspace.resolve()
    pinned_commit = git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    require_clean_repo(repo)
    if git(repo, "rev-parse", "--verify", "HEAD^{commit}") != pinned_commit:
        raise StudyError("candidate HEAD changed while pinning the study revision")
    if is_inside(workspace, repo):
        raise StudyError("workspace must be outside the candidate repository")
    if workspace.exists():
        raise StudyError(f"workspace already exists: {workspace}")
    pinned_tree = git(repo, "rev-parse", f"{pinned_commit}^{{tree}}")
    pinned_contract = git(
        repo,
        "rev-parse",
        f"{pinned_commit}:{CONTRACT_REL.as_posix()}",
    )
    workspace.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=workspace.name + ".tmp-", dir=workspace.parent))
    try:
        candidate, control = staging / "candidate", staging / "control"
        export_commit(repo, pinned_commit, candidate)
        before = tree_digest(candidate)
        build(candidate)
        if before != tree_digest(candidate):
            raise StudyError("candidate generated surfaces are not clean at pinned commit")
        shutil.copytree(candidate, control, symlinks=True, copy_function=shutil.copy2)
        original, stripped = strip_shadow(control / GROUND_REL)
        build(control)
        actual = changed_paths(candidate, control)
        if actual != GROUND_PATHS:
            raise StudyError(
                f"A/B diff escaped the hook allowlist; expected={list(GROUND_PATHS)}, actual={list(actual)}"
            )
        candidate_hook, control_hook = hook_surfaces(candidate, control)
        if candidate_hook != original or control_hook != stripped:
            raise StudyError("built hook surfaces do not match the prepared source edit")
        if git(repo, "rev-parse", "--verify", "HEAD^{commit}") != pinned_commit:
            raise StudyError("candidate HEAD changed while preparing the study control")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "control_kind": CONTROL_KIND,
            "candidate": {
                "commit": pinned_commit,
                "git_tree": pinned_tree,
                "contract_blob_sha1": pinned_contract,
                **identities(candidate),
            },
            "control": identities(control),
            "hook": {
                "heading": SHADOW_HEADING,
                "candidate_sha256": hashlib.sha256(candidate_hook).hexdigest(),
                "control_sha256": hashlib.sha256(control_hook).hexdigest(),
                "patch_sha256": patch_digest(candidate_hook, control_hook),
            },
            "changed_paths": list(GROUND_PATHS),
        }
        validate_manifest(manifest)
        write_manifest(staging / MANIFEST_NAME, manifest)
        os.replace(staging, workspace)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        return validate_manifest(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StudyError(f"cannot read manifest {path}: {exc}") from exc


def verify_control(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    candidate, control = workspace / "candidate", workspace / "control"
    manifest = load_manifest(workspace / MANIFEST_NAME)
    actual = changed_paths(candidate, control)
    if actual != GROUND_PATHS:
        raise StudyError("verified A/B diff escaped the hook allowlist")
    candidate_hook, control_hook = hook_surfaces(candidate, control)
    for key, digest in identities(candidate).items():
        if manifest["candidate"][key] != digest:
            raise StudyError(f"candidate {key} no longer matches the manifest")
    if manifest["control"] != identities(control):
        raise StudyError("control tree no longer matches the manifest")
    expected_hook = {
        "heading": SHADOW_HEADING,
        "candidate_sha256": hashlib.sha256(candidate_hook).hexdigest(),
        "control_sha256": hashlib.sha256(control_hook).hexdigest(),
        "patch_sha256": patch_digest(candidate_hook, control_hook),
    }
    if manifest["hook"] != expected_hook or manifest["changed_paths"] != list(actual):
        raise StudyError("hook identity or changed_paths no longer match the workspace")
    return manifest


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-control")
    prepare.add_argument("--repo", type=Path, required=True)
    prepare.add_argument("--workspace", type=Path, required=True)
    verify = commands.add_parser("verify-control")
    verify.add_argument("--workspace", type=Path, required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    try:
        manifest = (
            prepare_control(args.repo, args.workspace)
            if args.command == "prepare-control"
            else verify_control(args.workspace)
        )
    except StudyError as exc:
        argument_parser.error(str(exc))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
