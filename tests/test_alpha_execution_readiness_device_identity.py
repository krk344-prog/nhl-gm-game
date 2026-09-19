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


class AlphaExecutionReadinessDeviceIdentityTests(unittest.TestCase):
    def test_ready_result_keeps_serial_private_and_pins_ephemeral_identity(self):
        commit = "a" * 40
        identity = "b" * 64
        handoff = {
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "season_id": "2026-27",
            "endpoint_source": "explicit",
        }
        device_stdout = (
            '{"status":"ready","authorized_device_count":1,'
            '"selected_device":{"model":"Pixel 10 XL","android_version":"16","sdk_level":"36"},'
            f'"device_identity":"{identity}"}}\n'
        )

        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout=device_stdout, stderr="")

        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", return_value=commit):
                with patch.object(module, "prepare_build_handoff", return_value=handoff):
                    with patch.object(module.secrets, "token_hex", return_value="11" * 32):
                        result = module.check_execution_readiness(
                            api_base_url=handoff["api_base_url"],
                            serial="private-adb-serial",
                            runner=runner,
                        )

        self.assertEqual(
            result["selected_device"],
            {"model": "Pixel 10 XL", "android_version": "16", "sdk_level": "36"},
        )
        self.assertNotIn("serial", result["selected_device"])
        self.assertNotIn("private-adb-serial", str(result["selected_device"]))
        self.assertNotIn("device_identity", result)
        self.assertIn("--expected-device-identity", result["next_command_argv"])
        self.assertIn(identity, result["next_command_argv"])


if __name__ == "__main__":
    unittest.main()
