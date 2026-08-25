import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_SURFACES = (
    "README.md",
    "README_KO.md",
    "CHANGELOG.md",
    "platform/claude/plugin.json",
    "platform/codex/plugin.json",
    "claude/.claude-plugin/plugin.json",
    "codex/plugin/.codex-plugin/plugin.json",
)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def readme_title_version(rel: str) -> str:
    titles = re.findall(r"(?m)^# Leanforge v([0-9]+(?:\.[0-9]+)*)\s*$", read(rel))
    if len(titles) != 1:
        raise AssertionError(f"{rel} must contain exactly one Leanforge release title")
    return titles[0]


def changelog_top_version() -> str:
    match = re.search(r"(?m)^## v([0-9]+(?:\.[0-9]+)*)\s+\(", read("CHANGELOG.md"))
    if match is None:
        raise AssertionError("CHANGELOG.md must start with a versioned release entry")
    return match.group(1)


def changelog_top_heading() -> str:
    match = re.search(
        r"(?m)^## v[0-9]+(?:\.[0-9]+)*\s+\([^)]*\)\s*$",
        read("CHANGELOG.md"),
    )
    if match is None:
        raise AssertionError("CHANGELOG.md must start with a versioned release entry")
    return match.group(0)


def plugin_version(rel: str) -> str:
    return json.loads(read(rel))["version"]


def find_bash() -> str | None:
    candidates = []
    if os.name == "nt":
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            program_files = os.environ.get(env_name)
            if program_files:
                candidates.append(Path(program_files) / "Git" / "bin" / "bash.exe")
    path_bash = shutil.which("bash")
    if path_bash:
        candidates.append(Path(path_bash))
    return next((str(candidate) for candidate in candidates if candidate.is_file()), None)


def replace_once(path: Path, old: str, new: str) -> None:
    body = path.read_text(encoding="utf-8")
    if body.count(old) != 1:
        raise AssertionError(f"expected exactly one mutation target in {path}: {old!r}")
    path.write_text(body.replace(old, new), encoding="utf-8")


class ReleaseConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bash = find_bash()
        if cls.bash is None:
            raise unittest.SkipTest("bash is required to exercise build/build.sh")
        cls.current_release = changelog_top_version()
        cls.changelog_heading = changelog_top_heading()

    def run_isolated_build(self, mutate=None, inspect=None):
        with tempfile.TemporaryDirectory(prefix="leanforge-release-guard-") as temp:
            fixture = Path(temp) / "repo"
            fixture.mkdir()
            for rel in (
                "build/build.sh",
                "tools/run_orchestration_blocks.py",
                "README.md",
                "README_KO.md",
                "CHANGELOG.md",
            ):
                destination = fixture / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, destination)
            shutil.copytree(ROOT / "src", fixture / "src")
            shutil.copytree(ROOT / "platform", fixture / "platform")

            if mutate is not None:
                mutate(fixture)

            env = os.environ.copy()
            if os.name == "nt":
                git_root = Path(self.bash).resolve().parents[1]
                env["PATH"] = os.pathsep.join(
                    (
                        str(git_root / "bin"),
                        str(git_root / "usr" / "bin"),
                        env.get("PATH", ""),
                    )
                )

            completed = subprocess.run(
                [self.bash, "build/build.sh"],
                cwd=fixture,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=30,
                check=False,
            )
            if inspect is not None:
                inspect(fixture, completed)
            return completed

    def test_release_surfaces_share_current_version(self):
        versions = {
            "README.md title": readme_title_version("README.md"),
            "README_KO.md title": readme_title_version("README_KO.md"),
            "CHANGELOG.md top entry": changelog_top_version(),
            "platform/claude/plugin.json": plugin_version("platform/claude/plugin.json"),
            "platform/codex/plugin.json": plugin_version("platform/codex/plugin.json"),
            "claude/.claude-plugin/plugin.json": plugin_version(
                "claude/.claude-plugin/plugin.json"
            ),
            "codex/plugin/.codex-plugin/plugin.json": plugin_version(
                "codex/plugin/.codex-plugin/plugin.json"
            ),
        }

        self.assertEqual({self.current_release}, set(versions.values()), versions)

    def test_run_tdd_is_explicit_only_in_canonical_and_generated_codex_metadata(self):
        for rel in (
            "platform/codex/skills/run-tdd/agents/openai.yaml",
            "codex/plugin/skills/run-tdd/agents/openai.yaml",
        ):
            with self.subTest(rel=rel):
                body = read(rel)
                self.assertEqual(1, body.count("allow_implicit_invocation: false"))
                self.assertRegex(
                    body,
                    r"(?m)^policy:\n  allow_implicit_invocation: false\s*$",
                )

    def test_build_release_guard_accepts_baseline(self):
        completed = self.run_isolated_build()

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(f"version OK: v{self.current_release}", completed.stdout)

    def test_build_rejects_stale_orchestration_monolith_without_repair(self):
        observed = {}

        def drift_monolith(fixture: Path) -> None:
            path = fixture / "src/skills/run/references/orchestration.md"
            path.write_bytes(
                path.read_bytes().replace(
                    b"wave lifecycle",
                    b"wave lifecyclf",
                    1,
                )
            )

        def inspect_monolith(fixture: Path, completed) -> None:
            path = fixture / "src/skills/run/references/orchestration.md"
            observed["monolith"] = path.read_bytes()

        completed = self.run_isolated_build(
            mutate=drift_monolith,
            inspect=inspect_monolith,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn(
            "compatibility monolith differs from ordered block rendering",
            completed.stderr,
        )
        self.assertIn(b"wave lifecyclf", observed["monolith"])

    def test_build_normalizes_codex_run_agent_overlay_to_lf(self):
        observed = {}

        def force_crlf_overlay(fixture: Path) -> None:
            overlay = fixture / "platform/codex/skills/run/agents/openai.yaml"
            overlay.write_bytes(
                overlay.read_bytes().replace(b"\r\n", b"\n").replace(
                    b"\n", b"\r\n"
                )
            )

        def inspect_generated(fixture: Path, completed) -> None:
            generated = fixture / "codex/plugin/skills/run/agents/openai.yaml"
            observed["generated"] = generated.read_bytes()

        completed = self.run_isolated_build(
            mutate=force_crlf_overlay,
            inspect=inspect_generated,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertNotIn(b"\r", observed["generated"])

    def test_build_release_guard_ignores_non_label_versions(self):
        def add_unrelated_versions(fixture: Path) -> None:
            replace_once(
                fixture / "README.md",
                "### From a software goal to a reviewed, verified change ready to integrate.",
                "### From a software goal to a reviewed, verified change ready to integrate.\n\n"
                "Migration notes may mention Leanforge v0.0.1 in body text.",
            )
            for rel in ("platform/claude/plugin.json", "platform/codex/plugin.json"):
                manifest = json.loads((fixture / rel).read_text(encoding="utf-8"))
                manifest["metadata"] = {"version": "0.0.1"}
                (fixture / rel).write_text(
                    json.dumps(manifest, indent=2) + "\n",
                    encoding="utf-8",
                )

        completed = self.run_isolated_build(add_unrelated_versions)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(f"version OK: v{self.current_release}", completed.stdout)

    def test_build_release_guard_ignores_exact_title_in_fenced_code_block(self):
        def add_fenced_title(fixture: Path) -> None:
            title = f"# Leanforge v{self.current_release}"
            replace_once(
                fixture / "README.md",
                title,
                f"{title}\n\n```markdown\n# Leanforge v9.9.9\n```",
            )

        completed = self.run_isolated_build(add_fenced_title)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(f"version OK: v{self.current_release}", completed.stdout)

    def test_build_release_guard_ignores_exact_title_in_html_comment(self):
        def add_commented_title(fixture: Path) -> None:
            title = f"# Leanforge v{self.current_release}"
            replace_once(
                fixture / "README.md",
                title,
                f"{title}\n\n<!--\n# Leanforge v9.9.9\n-->",
            )

        completed = self.run_isolated_build(add_commented_title)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(f"version OK: v{self.current_release}", completed.stdout)

    def test_build_release_guard_rejects_missing_label_on_every_surface(self):
        def remove_labels(fixture: Path) -> None:
            for rel in ("README.md", "README_KO.md"):
                replace_once(
                    fixture / rel,
                    f"# Leanforge v{self.current_release}",
                    "# Leanforge",
                )
            replace_once(
                fixture / "CHANGELOG.md",
                self.changelog_heading,
                "## Current release",
            )
            for rel in ("platform/claude/plugin.json", "platform/codex/plugin.json"):
                replace_once(
                    fixture / rel,
                    f'  "version": "{self.current_release}",\n',
                    "",
                )

        completed = self.run_isolated_build(remove_labels)

        self.assertNotEqual(0, completed.returncode, completed.stdout)
        for surface in RELEASE_SURFACES:
            with self.subTest(surface=surface):
                self.assertIn(f"release version missing: {surface}", completed.stderr)

    def test_build_release_guard_rejects_ambiguous_label_on_every_surface(self):
        def duplicate_labels(fixture: Path) -> None:
            for rel in ("README.md", "README_KO.md"):
                title = f"# Leanforge v{self.current_release}"
                replace_once(fixture / rel, title, f"{title}\n\n{title}")
            heading = self.changelog_heading
            replace_once(
                fixture / "CHANGELOG.md",
                heading,
                f"{heading}\n\n{heading}",
            )
            version_line = f'  "version": "{self.current_release}",\n'
            for rel in ("platform/claude/plugin.json", "platform/codex/plugin.json"):
                replace_once(fixture / rel, version_line, version_line * 2)

        completed = self.run_isolated_build(duplicate_labels)

        self.assertNotEqual(0, completed.returncode, completed.stdout)
        for surface in RELEASE_SURFACES:
            with self.subTest(surface=surface):
                self.assertIn(f"release version ambiguous: {surface}", completed.stderr)

    def test_build_release_guard_rejects_unique_version_mismatch(self):
        def change_readme_version(fixture: Path) -> None:
            replace_once(
                fixture / "README.md",
                f"# Leanforge v{self.current_release}",
                "# Leanforge v9.9.9",
            )

        completed = self.run_isolated_build(change_readme_version)

        self.assertNotEqual(0, completed.returncode, completed.stdout)
        self.assertIn("release version mismatch", completed.stderr)
        self.assertIn("README.md: v9.9.9", completed.stderr)
        self.assertIn(
            f"README_KO.md: v{self.current_release}", completed.stderr
        )

    def test_ci_orders_build_drift_tests_and_whitespace_checks(self):
        ci = read(".github/workflows/ci.yml")
        commands = (
            "bash build/build.sh",
            "git diff --exit-code -- claude codex",
            'test -z "$(git status --porcelain --untracked-files=all -- claude codex)"',
            "python -m unittest discover -s tests -v",
            "git diff --check",
        )
        positions = [ci.index(command) for command in commands]

        self.assertEqual(sorted(positions), positions)
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(1, ci.count(command))


if __name__ == "__main__":
    unittest.main()
