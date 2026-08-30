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

        def runner(argv, *, check, capture_output, text):
            calls.append(
                {
                    "argv": list(argv),
                    "check": check,
                    "capture_output": capture_output,
                    "text": text,
                }
            )
            return SimpleNamespace(returncode=0, stdout='{"status":"ready"}\n', stderr="")

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
        self.assertEqual(
            calls,
            [
                {
                    "argv": [sys.executable, module.DEVICE_PREFLIGHT_SCRIPT, "--serial", "device-123"],
                    "check": False,
                    "capture_output": True,
                    "text": True,
                }
            ],
        )
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

    def test_device_failure_stops_before_endpoint_preflight_and_is_classified(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(
                returncode=4,
                stdout='{"status":"block","error":"multiple authorized Android devices are connected; rerun with --serial"}\n',
                stderr="",
            )

        with patch.object(module, "prepare_build_handoff") as prepare_mock:
            with self.assertRaisesRegex(
                module.ExecutionReadinessError,
                "device_preflight blocked: multiple authorized Android devices are connected; rerun with --serial",
            ) as raised:
                module.check_execution_readiness(runner=runner)

        self.assertEqual(raised.exception.blocker_scope, "device")
        prepare_mock.assert_not_called()

    def test_endpoint_failure_is_classified_after_device_preflight(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout='{"status":"ready"}\n', stderr="")

        with patch.object(
            module,
            "prepare_build_handoff",
            side_effect=RuntimeError("backend did not respond"),
        ):
            with self.assertRaisesRegex(
                module.ExecutionReadinessError,
                "endpoint_preflight blocked: backend did not respond",
            ) as raised:
                module.check_execution_readiness(runner=runner)

        self.assertEqual(raised.exception.blocker_scope, "endpoint")


if __name__ == "__main__":
    unittest.main()
