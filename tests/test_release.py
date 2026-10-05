"""The release workflow and the script that makes its notes (R1 9a, D039, D042).

Nothing here publishes: the workflows are parsed, and release_notes.py runs on
temporary changelogs. actionlint is not a dependency, so the parse is the check.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dev" / "release_notes.py"
WORKFLOWS = ROOT / ".github" / "workflows"

CHANGELOG = """# Changelog

## [Unreleased]

### Added

- Something not yet released.

## [0.3.0] - 2026-11-01

### Added

- The new thing.

  With a second paragraph, and an accent: café.

## [0.2.1] - 2026-10-01

### Fixed

- The old thing.
"""


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


class ReleaseNotesTests(unittest.TestCase):
    def run_script(self, version, changelog):
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: [p.unlink() for p in directory.iterdir()] or directory.rmdir())
        path = directory / "CHANGELOG.md"
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(changelog)
        return subprocess.run(
            [sys.executable, str(SCRIPT), version, "--changelog", str(path)],
            capture_output=True,
            timeout=30,
        )

    def test_found(self):
        done = self.run_script("0.3.0", CHANGELOG)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(
            done.stdout.decode("utf-8"),
            "### Added\n\n- The new thing.\n\n  With a second paragraph, and an accent: café.\n",
        )
        self.assertNotIn(b"\r", done.stdout)

    def test_found_with_v_prefix(self):
        done = self.run_script("v0.2.1", CHANGELOG)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.decode("utf-8"), "### Fixed\n\n- The old thing.\n")

    def test_last_section_in_the_file(self):
        done = self.run_script("0.1.0", CHANGELOG + "\n## [0.1.0] - 2026-09-01\n\n- First.\n\n")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.decode("utf-8"), "- First.\n")

    def test_trailing_link_definitions_are_not_notes(self):
        tail = (
            "\n## [0.1.0] - 2026-09-01\n\n- First.\n\n"
            "[Unreleased]: https://example.org/a\n[0.1.0]: https://example.org/b\n"
        )
        done = self.run_script("0.1.0", CHANGELOG + tail)
        self.assertEqual(done.stdout.decode("utf-8"), "- First.\n")

    def test_blank_lines_with_spaces_are_trimmed(self):
        done = self.run_script("0.1.0", "## [0.1.0] - 2026-09-01\n  \n\n- First.\n")
        self.assertEqual(done.stdout.decode("utf-8"), "- First.\n")

    def test_missing_section(self):
        done = self.run_script("0.9.9", CHANGELOG)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(done.stdout, b"")
        self.assertIn(b"0.9.9", done.stderr)
        self.assertEqual(len(done.stderr.strip().splitlines()), 1)

    def test_undated_section(self):
        for heading in ("## [0.3.0]", "## [0.3.0] - soon", "## [0.3.0] - 2026-13-45"):
            with self.subTest(heading=heading):
                done = self.run_script("0.3.0", CHANGELOG.replace("## [0.3.0] - 2026-11-01", heading))
                self.assertEqual(done.returncode, 1)
                self.assertEqual(done.stdout, b"")
                self.assertIn(b"no ISO date", done.stderr)
                self.assertEqual(len(done.stderr.strip().splitlines()), 1)

    def test_unreleased_is_not_a_release(self):
        done = self.run_script("Unreleased", CHANGELOG)
        self.assertEqual(done.returncode, 1)
        self.assertEqual(done.stdout, b"")
        self.assertIn(b"Unreleased", done.stderr)

    def test_empty_body(self):
        done = self.run_script("0.3.0", "## [0.3.0] - 2026-11-01\n\n\n## [0.2.1] - 2026-10-01\n\n- Old.\n")
        self.assertEqual(done.returncode, 1)
        self.assertEqual(done.stdout, b"")
        self.assertIn(b"empty", done.stderr)

    def test_bad_version_text_is_a_usage_error(self):
        for version in ("1.2", "latest", "v1.2.3.4", "0.3.0 ", "../x"):
            with self.subTest(version=version):
                done = self.run_script(version, CHANGELOG)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(done.stdout, b"")


class ReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        cls.workflow = yaml.safe_load(cls.text)
        # PyYAML reads the key `on` as the boolean True.
        cls.triggers = cls.workflow.get("on", cls.workflow.get(True))
        cls.jobs = cls.workflow["jobs"]

    def test_only_trigger_is_a_version_tag_push(self):
        self.assertEqual(self.triggers, {"push": {"tags": ["v*"]}})

    def test_top_level_permissions_only_read(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})

    def test_no_top_level_concurrency(self):
        # The called gate's group evaluates to this caller's values: the same group deadlocks.
        self.assertNotIn("concurrency", self.workflow)

    def test_gates_call_the_quality_gate(self):
        self.assertEqual(self.jobs["gates"]["uses"], "./.github/workflows/quality-gate.yml")

    def test_publish_waits_for_the_gates_and_the_owner(self):
        publish = self.jobs["publish"]
        self.assertEqual(publish["needs"], "gates")
        self.assertEqual(publish["environment"], "npm-release")
        self.assertEqual(publish["permissions"], {"id-token": "write", "contents": "read"})

    def test_publish_runs_from_the_package_directory(self):
        steps = [s for s in self.jobs["publish"]["steps"] if s.get("run") == "npm publish"]
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["working-directory"], "packages/fontkitstudio")

    def publish_steps(self):
        return self.jobs["publish"]["steps"]

    def step_index(self, predicate, what):
        found = [i for i, s in enumerate(self.publish_steps()) if predicate(s)]
        self.assertEqual(len(found), 1, f"expected exactly one {what} step")
        return found[0]

    def test_tag_must_equal_the_package_version_before_publishing(self):
        check = self.step_index(
            lambda s: "package.json" in s.get("run", "") and "exit 1" in s.get("run", ""),
            "tag-versus-version check",
        )
        publish = self.step_index(lambda s: s.get("run") == "npm publish", "npm publish")
        self.assertLess(check, publish)
        step = self.publish_steps()[check]
        self.assertEqual(step["env"], {"TAG": "${{ github.ref_name }}"})
        self.assertIn('[ "$TAG" != "v$version" ]', step["run"])
        self.assertIn("exit 1", step["run"])

    def test_changelog_section_is_checked_before_publishing(self):
        check = self.step_index(lambda s: "release_notes.py" in s.get("run", ""), "release-notes check")
        publish = self.step_index(lambda s: s.get("run") == "npm publish", "npm publish")
        self.assertLess(check, publish)
        step = self.publish_steps()[check]
        self.assertEqual(step["env"], {"TAG": "${{ github.ref_name }}"})
        self.assertIn('"${TAG#v}"', step["run"])

    def test_every_action_is_pinned_by_commit_sha(self):
        uses = [s["uses"] for job in self.jobs.values() for s in job.get("steps", []) if "uses" in s]
        self.assertTrue(uses)
        for ref in uses:
            self.assertRegex(ref, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$", ref)
        # The local reusable workflow is the one `uses` that is not an action.
        self.assertEqual(self.jobs["gates"]["uses"], "./.github/workflows/quality-gate.yml")

    def test_release_waits_for_the_publish(self):
        release = self.jobs["release"]
        self.assertEqual(release["needs"], "publish")
        self.assertEqual(release["permissions"], {"contents": "write"})

    def test_no_token_anywhere(self):
        for word in ("secrets.", "NODE_AUTH_TOKEN", "NPM_TOKEN"):
            self.assertNotIn(word, self.text)

    def test_no_expression_inside_a_script(self):
        # Values come through env, never interpolated into run text.
        runs = [s["run"] for job in ("publish", "release") for s in self.jobs[job]["steps"] if "run" in s]
        self.assertTrue(runs)
        for run in runs:
            self.assertNotIn("${{", run)

    def test_release_uses_the_tag_and_attaches_both_files(self):
        runs = [s["run"] for s in self.jobs["release"]["steps"] if "run" in s]
        text = "\n".join(runs)
        self.assertIn("gh release create", text)
        self.assertIn("--verify-tag", text)
        self.assertIn("fontkit-studio.html", text)
        self.assertIn("fontkit-bridge.js", text)


class QualityGateIsCallableTests(unittest.TestCase):
    def test_quality_gate_can_be_called(self):
        gate = load("quality-gate.yml")
        self.assertIn("workflow_call", gate.get("on", gate.get(True)))


if __name__ == "__main__":
    unittest.main()
