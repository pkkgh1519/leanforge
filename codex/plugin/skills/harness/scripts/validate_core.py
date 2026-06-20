from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def is_safe_repo_file(path: Path, root: Path) -> bool:
    if path.is_symlink():
        return False
    resolved = path.resolve(strict=False)
    return is_within(resolved, root) and resolved.is_file()


def is_safe_repo_dir(path: Path, root: Path) -> bool:
    if path.is_symlink():
        return False
    resolved = path.resolve(strict=False)
    return is_within(resolved, root) and resolved.is_dir()


def split_issues(issues: list[Issue]) -> tuple[list[Issue], list[Issue]]:
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    return errors, warnings


def safe_markdown_files_under(directory: Path, root: Path) -> Iterable[Path]:
    if not is_safe_repo_dir(directory, root):
        return
    for path in sorted(directory.glob("**/*.md")):
        if is_safe_repo_file(path, root):
            yield path


def safe_files_under(directory: Path, root: Path) -> dict[str, Path]:
    if not is_safe_repo_dir(directory, root):
        return {}
    files: dict[str, Path] = {}
    for path in sorted(directory.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        if is_safe_repo_file(path, root):
            files[path.relative_to(directory).as_posix()] = path
    return files
