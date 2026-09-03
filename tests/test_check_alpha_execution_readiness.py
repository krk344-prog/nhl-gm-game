from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime
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
        self.commit = "a" * 40
        self.identity_key = "11" * 32
        self.device_identity = "b" * 64
        self.ready_device_stdout = (
            '{"status":"ready","authorized_device_count":1,'
            '"selected_device":{"model":"Pixel 10 XL","android_version":"16","sdk_level":"36"},'
            f'"device_identity":"{self.device_identity}"}}\n'
        )

    def _ready(self, *, serial: str | None = None, runner=None):
        if runner is None:
            def runner(argv, *, check, capture_output, text):
                return SimpleNamespace(returncode=0, stdout=self.ready_device_stdout, stderr="")
        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", return_value=self.commit):
                with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
                    with patch.object(module.secrets, "token_hex", return_value=self.identity_key):
                        return module.check_execution_readiness(
                            api_base_url=self.handoff["api_base_url"], serial=serial, runner=runner
                        )

    def test_reports_ready_without_running_qualification_or_build(self):
        calls = []
        def runner(argv, *, check, capture_output, text):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0, stdout=self.ready_device_stdout, stderr="")

        result = self._ready(serial="device-123", runner=runner)
        self.assertTrue(result["ready"])
        self.assertEqual(result["source_commit"], self.commit)
        datetime.fromisoformat(str(result["checked_at_utc"]).replace("Z", "+00:00"))
        self.assertEqual(
            calls[0],
            [sys.executable, module.DEVICE_PREFLIGHT_SCRIPT, "--identity-key", self.identity_key, "--serial", "device-123"],
        )
        argv = result["next_command_argv"]
        self.assertIn("--device-identity-key", argv)
        self.assertIn(self.identity_key, argv)
        self.assertIn("--expected-device-identity", argv)
        self.assertIn(self.device_identity, argv)
        self.assertIn("--serial", argv)
        self.assertIn("device-123", argv)
        self.assertEqual(result["output_sensitivity"], "private")
        public_summary = result["public_summary"]
        self.assertTrue(public_summary["ready"])
        self.assertEqual(public_summary["source_commit"], self.commit)
        self.assertNotIn("api_base_url", public_summary)
        self.assertNotIn("selected_device", public_summary)
        self.assertNotIn("next_command_argv", public_summary)
        self.assertNotIn(self.identity_key, str(public_summary))
        self.assertNotIn(self.device_identity, str(public_summary))
        self.assertNotIn("device-123", str(public_summary))
        self.assertIn("Keep this full readiness payload private", result["next_action"])
        self.assertIn("Share only public_summary publicly", result["next_action"])

    def test_source_failure_stops_before_device_and_endpoint_preflight(self):
        runner_calls = []
        def runner(*args, **kwargs):
            runner_calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout=self.ready_device_stdout, stderr="")
        with patch.object(module, "validate_source_readiness", side_effect=module.ExecutionReadinessError("source", "source_preflight blocked")):
            with patch.object(module, "read_source_commit") as commit_mock:
                with patch.object(module, "prepare_build_handoff") as prepare_mock:
                    with self.assertRaises(module.ExecutionReadinessError):
                        module.check_execution_readiness(runner=runner)
        self.assertEqual(runner_calls, [])
        commit_mock.assert_not_called()
        prepare_mock.assert_not_called()

    def test_invalid_source_commit_stops_before_device_and_endpoint_preflight(self):
        runner_calls = []
        def runner(*args, **kwargs):
            runner_calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout=self.ready_device_stdout, stderr="")
        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", side_effect=module.ExecutionReadinessError("source", "source_preflight blocked: could not determine exact Git commit")):
                with patch.object(module, "prepare_build_handoff") as prepare_mock:
                    with self.assertRaisesRegex(module.ExecutionReadinessError, "could not determine exact Git commit"):
                        module.check_execution_readiness(runner=runner)
        self.assertEqual(runner_calls, [])
        prepare_mock.assert_not_called()

    def test_device_failure_stops_before_endpoint_preflight_and_is_classified(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=4, stdout='{"status":"block","error":"multiple authorized Android devices are connected; rerun with --serial"}\n', stderr="")
        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", return_value=self.commit):
                with patch.object(module, "prepare_build_handoff") as prepare_mock:
                    with self.assertRaisesRegex(module.ExecutionReadinessError, "multiple authorized Android devices") as raised:
                        module.check_execution_readiness(runner=runner)
        self.assertEqual(raised.exception.blocker_scope, "device")
        prepare_mock.assert_not_called()

    def test_device_success_requires_complete_ready_payload_before_endpoint_preflight(self):
        cases = [
            ("not-json\n", "invalid JSON"),
            ('{"status":"block"}\n', "did not confirm ready status"),
            ('{"status":"ready"}\n', "valid authorized-device count"),
            ('{"status":"ready","authorized_device_count":1}\n', "selected-device metadata"),
            ('{"status":"ready","authorized_device_count":1,"selected_device":{"model":"Pixel","android_version":"16","sdk_level":""}}\n', "missing sdk_level"),
            ('{"status":"ready","authorized_device_count":1,"selected_device":{"model":"Pixel","android_version":"16","sdk_level":"36"}}\n', "privacy-safe device identity"),
        ]
        for stdout, expected_error in cases:
            with self.subTest(stdout=stdout):
                def runner(argv, *, check, capture_output, text):
                    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")
                with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
                    with patch.object(module, "read_source_commit", return_value=self.commit):
                        with patch.object(module, "prepare_build_handoff") as prepare_mock:
                            with patch.object(module.secrets, "token_hex", return_value=self.identity_key):
                                with self.assertRaisesRegex(module.ExecutionReadinessError, expected_error):
                                    module.check_execution_readiness(runner=runner)
                prepare_mock.assert_not_called()

    def test_endpoint_failure_is_classified_after_device_preflight(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout=self.ready_device_stdout, stderr="")
        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", return_value=self.commit):
                with patch.object(module.secrets, "token_hex", return_value=self.identity_key):
                    with patch.object(module, "prepare_build_handoff", side_effect=RuntimeError("backend did not respond")):
                        with self.assertRaisesRegex(module.ExecutionReadinessError, "endpoint_preflight blocked: backend did not respond") as raised:
                            module.check_execution_readiness(runner=runner)
        self.assertEqual(raised.exception.blocker_scope, "endpoint")

    def test_source_change_during_checks_blocks_ready_result(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout=self.ready_device_stdout, stderr="")
        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", side_effect=[self.commit, "b" * 40]):
                with patch.object(module.secrets, "token_hex", return_value=self.identity_key):
                    with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
                        with self.assertRaisesRegex(module.ExecutionReadinessError, "source changed during readiness checks"):
                            module.check_execution_readiness(api_base_url=self.handoff["api_base_url"], runner=runner)


if __name__ == "__main__":
    unittest.main()
