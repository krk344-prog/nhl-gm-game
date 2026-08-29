from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "check_alpha_execution_readiness", SCRIPTS / "check_alpha_execution_readiness.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CheckAlphaExecutionReadinessTests(unittest.TestCase):
    def setUp(self):
        self.handoff = {
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "season_id": "2026-27",
            "endpoint_source": "explicit",
        }

    def test_reports_ready_without_running_qualification_or_build(self):
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff) as prepare_mock:
            result = module.check_execution_readiness(
                api_base_url=self.handoff["api_base_url"],
                serial="device-123",
                runner=runner,
            )

        self.assertTrue(result["ready"])
        self.assertTrue(result["device_ready"])
        self.assertTrue(result["endpoint_ready"])
        self.assertEqual(result["api_base_url"], self.handoff["api_base_url"])
        self.assertEqual(calls, [[sys.executable, module.DEVICE_PREFLIGHT_SCRIPT, "--serial", "device-123"]])
        prepare_mock.assert_called_once_with(
            api_base_url=self.handoff["api_base_url"],
            season_id="2026-27",
            timeout=5.0,
        )
        self.assertEqual(
            result["next_command_argv"],
            [
                sys.executable,
                module.RELEASE_HANDOFF_SCRIPT,
                "--api-base-url",
                self.handoff["api_base_url"],
                "--season-id",
                "2026-27",
                "--timeout",
                "5.0",
                "--serial",
                "device-123",
            ],
        )

    def test_device_failure_stops_before_endpoint_preflight(self):
        def runner(argv, *, check):
            return SimpleNamespace(returncode=4)

        with patch.object(module, "prepare_build_handoff") as prepare_mock:
            with self.assertRaisesRegex(RuntimeError, "device_preflight failed with exit code 4"):
                module.check_execution_readiness(runner=runner)

        prepare_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
