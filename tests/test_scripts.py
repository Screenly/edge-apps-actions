"""Tests for the shell scripts the initialize and update actions run."""

import json
import os
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


class MockApi:
    """Serves canned responses for the two endpoints the scripts call."""

    def __init__(self):
        self.users = (200, "[]")
        self.apps = (200, "[]")
        api = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/api/v4.1/users/"):
                    status, body = api.users
                elif self.path.startswith("/v4/edge-apps"):
                    status, body = api.apps
                else:
                    status, body = 404, ""
                self.send_response(status)
                self.end_headers()
                self.wfile.write(body.encode())

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class ScriptTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.github_env = self.dir / "github_env"
        self.github_output = self.dir / "github_output"
        self.github_env.touch()
        self.github_output.touch()

    def run_script(self, name, *args, **env):
        full_env = {
            "PATH": os.environ["PATH"],
            "GITHUB_ENV": str(self.github_env),
            "GITHUB_OUTPUT": str(self.github_output),
            "SCREENLY_API_TOKEN_INPUT": "token",
            "ENVIRONMENT_INPUT": "stage",
            **env,
        }
        return subprocess.run(
            ["bash", str(SCRIPTS / name), *args],
            cwd=self.dir,
            env=full_env,
            capture_output=True,
            text=True,
        )


class PrepareTest(ScriptTestCase):
    def update(self, **env):
        return self.run_script("prepare.sh", "update", **{"EDGE_APP_ID_INPUT": "01ABC", **env})

    def initialize(self, **env):
        env = {"EDGE_APP_NAME_INPUT": "My App", "EDGE_APP_TITLE_INPUT": "My App", **env}
        return self.run_script("prepare.sh", "initialize", **env)

    def test_rejects_unknown_mode(self):
        self.assertNotEqual(self.run_script("prepare.sh", "deploy").returncode, 0)

    def test_rejects_empty_token(self):
        result = self.update(SCREENLY_API_TOKEN_INPUT="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("screenly_api_token is empty", result.stdout)

    def test_rejects_unknown_environment(self):
        result = self.update(ENVIRONMENT_INPUT="dev")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be 'stage' or 'production'", result.stdout)

    def test_sets_api_base_url_per_environment(self):
        self.assertEqual(self.update(ENVIRONMENT_INPUT="production").returncode, 0)
        self.assertIn("API_BASE_URL=https://api.screenlyapp.com\n", self.github_env.read_text())
        self.github_env.write_text("")
        self.assertEqual(self.update(ENVIRONMENT_INPUT="stage").returncode, 0)
        self.assertIn("API_BASE_URL=https://api.screenlyappstage.com\n", self.github_env.read_text())

    def test_update_exports_trimmed_id(self):
        result = self.update(EDGE_APP_ID_INPUT="  01ABC \n")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Using EDGE_APP_ID=01ABC", result.stdout)
        lines = self.github_env.read_text().splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("EDGE_APP_ID<<"))
        self.assertEqual(lines[start + 1], "01ABC")
        self.assertEqual(lines[start + 2], lines[start].removeprefix("EDGE_APP_ID<<"))

    def test_update_requires_id(self):
        for value in ["", "0", "false", "NULL", " none "]:
            with self.subTest(value=value):
                result = self.update(EDGE_APP_ID_INPUT=value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Set repo variable STAGE_EDGE_APP_ID", result.stdout)

    def test_initialize_refuses_when_already_initialized(self):
        result = self.initialize(EDGE_APP_ID_INPUT="01ABC", ENVIRONMENT_INPUT="production")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already initialized", result.stdout)
        self.assertIn("PRODUCTION_EDGE_APP_ID", result.stdout)

    def test_initialize_treats_placeholder_id_as_empty(self):
        result = self.initialize(EDGE_APP_ID_INPUT="false")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("EDGE_APP_ID", self.github_env.read_text())

    def test_initialize_rejects_unsafe_name_and_title(self):
        for bad in ['a"b', "a$b", "a`b", "a\\b", "a\nb", ""]:
            with self.subTest(bad=bad):
                self.assertNotEqual(self.initialize(EDGE_APP_NAME_INPUT=bad).returncode, 0)
                self.assertNotEqual(self.initialize(EDGE_APP_TITLE_INPUT=bad).returncode, 0)

    def test_update_ignores_name_and_title(self):
        self.assertEqual(self.update(EDGE_APP_NAME_INPUT='a"b').returncode, 0)

    def test_detects_build_step(self):
        (self.dir / "package.json").write_text(json.dumps({"scripts": {"build": "vite build"}}))
        self.assertEqual(self.update().returncode, 0)
        self.assertIn("has_build_step=true", self.github_output.read_text())
        self.assertFalse((self.dir / ".ignore").exists())

    def test_plain_html_app_ignores_repo_internals(self):
        (self.dir / "package.json").write_text(json.dumps({"scripts": {"lint": "eslint"}}))
        (self.dir / ".ignore").write_text("docs/\n.git/")
        self.assertEqual(self.update().returncode, 0)
        self.assertEqual(self.update().returncode, 0)
        self.assertIn("has_build_step=false", self.github_output.read_text())
        self.assertEqual(
            (self.dir / ".ignore").read_text().splitlines(),
            ["docs/", ".git/", ".github/", ".claude/", "node_modules/"],
        )


class ApiScriptTestCase(ScriptTestCase):
    def setUp(self):
        super().setUp()
        self.api = MockApi()
        self.addCleanup(self.api.close)

    def run_api_script(self, name, **env):
        return self.run_script(name, API_BASE_URL=self.api.url, **env)


class VerifyTokenTest(ApiScriptTestCase):
    def test_accepts_valid_token(self):
        result = self.run_api_script("verify-token.sh")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Token is valid", result.stdout)

    def test_rejects_invalid_token(self):
        self.api.users = (401, "")
        result = self.run_api_script("verify-token.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("validation failed for stage (HTTP 401)", result.stdout)

    def test_reports_unreachable_api(self):
        result = self.run_script("verify-token.sh", API_BASE_URL="http://127.0.0.1:9")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("(HTTP 000)", result.stdout)


class CheckDuplicateNameTest(ApiScriptTestCase):
    def check(self):
        return self.run_api_script("check-duplicate-name.sh", EDGE_APP_NAME_INPUT="My App")

    def test_continues_when_no_app_has_the_name(self):
        self.api.apps = (200, json.dumps([{"id": "01A", "name": "Other"}]))
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_refuses_when_the_name_exists(self):
        self.api.apps = (200, json.dumps([{"id": "01A", "name": "My App"}, {"id": "01B", "name": "My App"}]))
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists in stage (id: 01A, 01B)", result.stdout)

    def test_fails_closed(self):
        cases = {
            "HTTP error": (403, "[]"),
            "invalid JSON": (200, "not json"),
            "JSON object": (200, '{"message": "error"}'),
        }
        for label, response in cases.items():
            with self.subTest(label):
                self.api.apps = response
                result = self.check()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Could not list existing Edge Apps", result.stdout)

    def test_fails_closed_when_api_is_down(self):
        result = self.run_script(
            "check-duplicate-name.sh", API_BASE_URL="http://127.0.0.1:9", EDGE_APP_NAME_INPUT="My App"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("(HTTP 000)", result.stdout)

    def test_ignores_non_object_entries(self):
        self.api.apps = (200, json.dumps(["My App", None, {"id": 7, "name": "Other"}]))
        self.assertEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
