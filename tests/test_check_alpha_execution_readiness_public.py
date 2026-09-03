from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "check_alpha_execution_readiness_public",
    SCRIPTS / "check_alpha_execution_readiness_public.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicExecutionReadinessTests(unittest.TestCase):
    def test_ready_result_emits_only_private_checkers_public_summary(self):
        private_payload = {
            "ready": True,
            "output_sensitivity": "private",
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "selected_device": {"model": "Pixel 10 XL"},
            "next_command_argv": ["python", "handoff.py", "--device-identity-key", "secret-key"],
            "public_summary": {
                "ready": True,
                "source_ready": True,
                "device_ready": True,
                "endpoint_ready": True,
                "season_id": "2026-27",
            },
        }

        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout=json.dumps(private_payload), stderr="")

        returncode, result = module.public_readiness_status(runner=runner)
        self.assertEqual(returncode, 0)
        self.assertEqual(result, private_payload["public_summary"])
        rendered = json.dumps(result)
        self.assertNotIn("192.168.1.20", rendered)
        self.assertNotIn("Pixel 10 XL", rendered)
        self.assertNotIn("secret-key", rendered)

    def test_failure_does_not_echo_private_diagnostic(self):
        private_error = {
            "ready": False,
            "blocker_scope": "endpoint",
            "error": "endpoint_preflight blocked: http://192.168.1.20:8000/api/v1 did not respond",
        }

        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=1, stdout=json.dumps(private_error), stderr="")

        returncode, result = module.public_readiness_status(
            api_base_url="http://192.168.1.20:8000/api/v1",
            serial="private-device-selector",
            runner=runner,
        )
        self.assertEqual(returncode, 1)
        self.assertEqual(result["blocker_scope"], "endpoint")
        rendered = json.dumps(result)
        self.assertNotIn("192.168.1.20", rendered)
        self.assertNotIn("private-device-selector", rendered)
        self.assertNotIn("did not respond", rendered)
        self.assertIn("rerun readiness", result["next_action"])

    def test_invalid_private_output_fails_closed_without_echoing_it(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=2, stdout="not-json private detail", stderr="")

        returncode, result = module.public_readiness_status(runner=runner)
        self.assertEqual(returncode, 1)
        self.assertEqual(result["blocker_scope"], "unknown")
        self.assertNotIn("not-json", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
