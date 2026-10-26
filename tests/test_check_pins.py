"""Tests for the release guard, scripts/check_pins.py."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

CHECK_PINS = Path(__file__).resolve().parent.parent / "scripts" / "check_pins.py"


class CheckPinsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q")
        self.write_pins("v1.2.3")
        self.write("update/action.yml", "name: Update\n")
        self.write("scripts/prepare.sh", "echo prepare\n")
        self.write("CONTRIBUTING.md", "Contributing\n")
        self.commit()
        self.git("tag", "v1.2.3")

    def git(self, *args):
        subprocess.run(
            ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", *args],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def write_pins(self, version, checks_version=None):
        self.write(
            ".github/workflows/update.yml",
            f"    - uses: Screenly/edge-apps-actions/update@{version}\n",
        )
        self.write(
            ".github/workflows/checks.yml",
            f"    - uses: Screenly/edge-apps-actions/checks@{checks_version or version}\n",
        )
        self.write(
            "examples/update-edge-app.yml",
            f"    uses: Screenly/edge-apps-actions/.github/workflows/update.yml@{version}\n",
        )
        self.write(
            "README.md",
            f"```yaml\nuses: Screenly/edge-apps-actions/.github/workflows/update.yml@{version}\n```\n",
        )

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "change")

    def check(self, ref="refs/heads/feature"):
        env = {**os.environ, "GITHUB_REF": ref}
        return subprocess.run(
            ["python3", str(CHECK_PINS)], cwd=self.repo, env=env, capture_output=True, text=True
        )

    def assertPasses(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assertFailsWith(self, result, message):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stdout)

    def test_bumped_pins_pass(self):
        self.write_pins("v1.2.4")
        self.write("update/action.yml", "name: Update (changed)\n")
        self.commit()
        self.assertPasses(self.check())

    def test_main_mixed_in_fails(self):
        self.write_pins("v1.2.4", checks_version="main")
        self.commit()
        self.assertFailsWith(self.check(), "one exact vYY.M.PATCH version, found: main v1.2.4")

    def test_all_main_fails(self):
        self.write_pins("main")
        self.commit()
        self.assertFailsWith(self.check(), "found: main")

    def test_suffixed_version_fails(self):
        self.write_pins("v1.2.4", checks_version="v1.2.4-rc.1")
        self.commit()
        self.assertFailsWith(self.check(), "found: v1.2.4 v1.2.4-rc.1")

    def test_two_versions_fail(self):
        self.write_pins("v1.2.4", checks_version="v1.2.3")
        self.commit()
        self.assertFailsWith(self.check(), "found: v1.2.3 v1.2.4")

    def test_no_refs_fails_with_a_message(self):
        for path in [".github/workflows/update.yml", ".github/workflows/checks.yml", "examples/update-edge-app.yml"]:
            (self.repo / path).unlink()
        self.write("README.md", "No pins here\n")
        self.commit()
        self.assertFailsWith(self.check(), "Found no Screenly/edge-apps-actions refs")

    def test_matching_tag_passes(self):
        self.assertPasses(self.check("refs/tags/v1.2.3"))

    def test_mismatched_tag_fails(self):
        self.assertFailsWith(self.check("refs/tags/v1.2.4"), "Tag v1.2.4, but the pins point at v1.2.3")

    def test_unbumped_action_change_fails(self):
        self.write("update/action.yml", "name: Update (changed)\n")
        self.commit()
        self.assertFailsWith(self.check(), "changed since v1.2.3")

    def test_unbumped_script_change_fails(self):
        self.write("scripts/prepare.sh", "echo changed\n")
        self.commit()
        self.assertFailsWith(self.check(), "changed since v1.2.3")

    def test_docs_only_change_passes(self):
        self.write("CONTRIBUTING.md", "Contributing (changed)\n")
        self.commit()
        self.assertPasses(self.check())

    def test_backticked_readme_ref_passes(self):
        self.write("README.md", "Use `Screenly/edge-apps-actions/update@v1.2.3`.\n")
        self.commit()
        self.assertPasses(self.check())


if __name__ == "__main__":
    unittest.main()
