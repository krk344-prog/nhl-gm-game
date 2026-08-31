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

        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH) as source_mock:
            with patch.object(module, "read_source_commit", return_value=self.commit) as commit_mock:
                with patch.object(module, "prepare_build_handoff", return_value=self.handoff) as prepare_mock:
                    result = module.check_execution_readiness(
                        api_base_url=self.handoff["api_base_url"],
                        serial="device-123",
                        runner=runner,
                    )

        self.assertEqual(source_mock.call_count, 2)
        self.assertEqual(commit_mock.call_count, 2)
        self.assertTrue(result["ready"])
        self.assertTrue(result["source_ready"])
        self.assertEqual(result["source_branch"], module.PR_BRANCH)
        self.assertEqual(result["source_commit"], self.commit)
        self.assertTrue(str(result["checked_at_utc"]).endswith("Z"))
        datetime.fromisoformat(str(result["checked_at_utc"]).replace("Z", "+00:00"))
        self.assertTrue(result["device_ready"])
        self.assertTrue(result["endpoint_ready"])
        self.assertEqual(result["api_base_url"], self.handoff["api_base_url"])
        self.assertIn("pinned to this certified source commit and readiness timestamp", result["next_action"])
        self.assertIn("fail closed if the checkout changes or readiness is stale", result["next_action"])
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
                "--expected-source-commit",
                self.commit,
                "--readiness-checked-at",
                result["checked_at_utc"],
                "--serial",
                "device-123",
            ],
        )

    def test_source_failure_stops_before_commit_device_and_endpoint_preflight(self):
        runner_calls = []

        def runner(*args, **kwargs):
            runner_calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout='{"status":"ready"}\n', stderr="")

        with patch.object(
            module,
            "validate_source_readiness",
            side_effect=module.ExecutionReadinessError(
                "source",
                f"source_preflight blocked: build must run from {module.PR_BRANCH}; current branch is main",
            ),
        ):
            with patch.object(module, "read_source_commit") as commit_mock:
                with patch.object(module, "prepare_build_handoff") as prepare_mock:
                    with self.assertRaisesRegex(module.ExecutionReadinessError, "source_preflight blocked") as raised:
                        module.check_execution_readiness(runner=runner)

        self.assertEqual(raised.exception.blocker_scope, "source")
        self.assertEqual(runner_calls, [])
        commit_mock.assert_not_called()
        prepare_mock.assert_not_called()

    def test_invalid_source_commit_stops_before_device_and_endpoint_preflight(self):
        runner_calls = []

        def runner(*args, **kwargs):
            runner_calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout='{"status":"ready"}\n', stderr="")

        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(
                module,
                "read_source_commit",
                side_effect=module.ExecutionReadinessError(
                    "source", "source_preflight blocked: could not determine exact Git commit"
                ),
            ):
                with patch.object(module, "prepare_build_handoff") as prepare_mock:
                    with self.assertRaisesRegex(module.ExecutionReadinessError, "could not determine exact Git commit") as raised:
                        module.check_execution_readiness(runner=runner)

        self.assertEqual(raised.exception.blocker_scope, "source")
        self.assertEqual(runner_calls, [])
        prepare_mock.assert_not_called()

    def test_device_failure_stops_before_endpoint_preflight_and_is_classified(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(
                returncode=4,
                stdout='{"status":"block","error":"multiple authorized Android devices are connected; rerun with --serial"}\n',
                stderr="",
            )

        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", return_value=self.commit):
                with patch.object(module, "prepare_build_handoff") as prepare_mock:
                    with self.assertRaisesRegex(
                        module.ExecutionReadinessError,
                        "device_preflight blocked: multiple authorized Android devices are connected; rerun with --serial",
                    ) as raised:
                        module.check_execution_readiness(runner=runner)

        self.assertEqual(raised.exception.blocker_scope, "device")
        prepare_mock.assert_not_called()

    def test_device_success_requires_parseable_ready_payload_before_endpoint_preflight(self):
        cases = [
            ("not-json\n", "invalid JSON"),
            ('{"status":"block"}\n', "did not confirm ready status"),
            ('{"status":"unknown"}\n', "did not confirm ready status"),
        ]
        for stdout, expected_error in cases:
            with self.subTest(stdout=stdout):
                def runner(argv, *, check, capture_output, text):
                    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

                with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
                    with patch.object(module, "read_source_commit", return_value=self.commit):
                        with patch.object(module, "prepare_build_handoff") as prepare_mock:
                            with self.assertRaisesRegex(module.ExecutionReadinessError, expected_error) as raised:
                                module.check_execution_readiness(runner=runner)

                self.assertEqual(raised.exception.blocker_scope, "device")
                prepare_mock.assert_not_called()

    def test_endpoint_failure_is_classified_after_device_preflight(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout='{"status":"ready"}\n', stderr="")

        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH):
            with patch.object(module, "read_source_commit", return_value=self.commit):
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

    def test_source_change_during_device_and_endpoint_checks_blocks_ready_result(self):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout='{"status":"ready"}\n', stderr="")

        with patch.object(module, "validate_source_readiness", return_value=module.PR_BRANCH) as source_mock:
            with patch.object(module, "read_source_commit", side_effect=[self.commit, "b" * 40]) as commit_mock:
                with patch.object(module, "prepare_build_handoff", return_value=self.handoff) as prepare_mock:
                    with self.assertRaisesRegex(
                        module.ExecutionReadinessError,
                        "source changed during readiness checks; rerun readiness",
                    ) as raised:
                        module.check_execution_readiness(
                            api_base_url=self.handoff["api_base_url"],
                            runner=runner,
                        )

        self.assertEqual(raised.exception.blocker_scope, "source")
        self.assertEqual(source_mock.call_count, 2)
        self.assertEqual(commit_mock.call_count, 2)
        prepare_mock.assert_called_once_with(
            api_base_url=self.handoff["api_base_url"],
            season_id="2026-27",
            timeout=5.0,
        )


if __name__ == "__main__":
    unittest.main()
