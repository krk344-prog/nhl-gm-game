from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("prepare_alpha_build", SCRIPTS / "prepare_alpha_build.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

build_spec = importlib.util.spec_from_file_location("build_alpha_apk_local", SCRIPTS / "build_alpha_apk_local.py")
assert build_spec and build_spec.loader
builder = importlib.util.module_from_spec(build_spec)
build_spec.loader.exec_module(builder)


def _passing_preflight(api_base_url, *, season_id, timeout, allow_loopback):
    assert timeout == 5.0
    assert allow_loopback is False
    return module.PreflightResult(
        api_base_url=api_base_url.rstrip("/"),
        health_status="ok",
        api_version="alpha",
        season_id=season_id,
        regular_season_games=84,
        ready=True,
    )


class PrepareAlphaBuildTests(unittest.TestCase):
    def test_explicit_endpoint_produces_exact_pr13_local_build_command(self):
        payload = module.prepare_build_handoff(
            api_base_url="http://192.168.1.20:8000/api/v1",
            preflight=_passing_preflight,
        )
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["endpoint_source"], "explicit")
        self.assertEqual(payload["ref"], "agent/alpha-rules-integration-v1")
        self.assertEqual(payload["build_script"], "scripts/build_alpha_apk_local.py")
        self.assertTrue((ROOT / payload["build_script"]).is_file())
        self.assertEqual(
            payload["build_argv"][-3:],
            ["--api-base-url", "http://192.168.1.20:8000/api/v1", "--execute"],
        )
        self.assertNotIn("gh workflow run", payload["build_command"])

    def test_discovered_endpoint_is_selected_preflighted_and_locked(self):
        payload = module.prepare_build_handoff(
            addresses=["127.0.0.1", "192.168.1.30"],
            preflight=_passing_preflight,
        )
        self.assertEqual(payload["endpoint_source"], "discovered")
        self.assertEqual(payload["api_base_url"], "http://192.168.1.30:8000/api/v1")
        self.assertEqual(payload["build_argv"][-2], "http://192.168.1.30:8000/api/v1")

    def test_failed_preflight_blocks_build_output(self):
        def failed_preflight(*args, **kwargs):
            raise RuntimeError("backend unavailable")

        with self.assertRaisesRegex(RuntimeError, "backend unavailable"):
            module.prepare_build_handoff(
                api_base_url="http://192.168.1.20:8000/api/v1",
                preflight=failed_preflight,
            )

    def test_local_builder_rejects_loopback_and_wrong_routes(self):
        for endpoint in (
            "http://127.0.0.1:8000/api/v1",
            "http://192.168.1.20:8000/api/v2",
            "http://192.168.1.20:8000/api/v1?debug=1",
        ):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ValueError):
                    builder.validate_api_base_url(endpoint)

    def test_local_builder_plan_contains_export_prebuild_and_apk_steps(self):
        plan = builder.command_plan("http://192.168.1.20:8000/api/v1")
        flattened = [item for command in plan for item in command]
        self.assertEqual(plan[0], ["npm", "ci"])
        self.assertIn("export", flattened)
        self.assertIn("prebuild", flattened)
        self.assertIn("assembleDebug", flattened)

    def test_build_environment_requires_ci_aligned_toolchain(self):
        passing = {
            "tools": {"node": "/node", "npm": "/npm", "npx": "/npx", "java": "/java"},
            "node_major": 20,
            "java_major": 17,
            "android_sdk": "/android-sdk",
        }
        self.assertIs(builder.validate_build_environment(passing), passing)

        for field, value, message in (
            ("node_major", 18, "Node.js 20"),
            ("java_major", 21, "Java 17"),
            ("android_sdk", None, "Android SDK"),
        ):
            report = dict(passing)
            report[field] = value
            with self.subTest(field=field):
                with self.assertRaisesRegex(RuntimeError, message):
                    builder.validate_build_environment(report)

    def test_missing_command_line_tool_blocks_before_packaging(self):
        report = {
            "tools": {"node": "/node", "npm": None, "npx": "/npx", "java": "/java"},
            "node_major": 20,
            "java_major": 17,
            "android_sdk": "/android-sdk",
        }
        with self.assertRaisesRegex(RuntimeError, "missing required tools: npm"):
            builder.validate_build_environment(report)


if __name__ == "__main__":
    unittest.main()
