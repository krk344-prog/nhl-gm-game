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
    "run_alpha_release_handoff", SCRIPTS / "run_alpha_release_handoff.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RunAlphaReleaseHandoffTests(unittest.TestCase):
    def setUp(self):
        self.handoff = {
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "season_id": "2026-27",
            "qualification_record": "artifacts/alpha-endpoint-qualification.json",
            "qualification_argv": ["python", "scripts/qualify_alpha_endpoint.py"],
            "build_argv": ["python", "scripts/build_alpha_apk_local.py", "--execute"],
        }
        self.commit = "a" * 40
        self.apk_sha256 = "b" * 64

    def _run(self, runner, **kwargs):
        return module.run_release_handoff(
            runner=runner,
            record_exists=lambda path: True,
            artifact_exists=lambda path: True,
            checksum_reader=lambda path: self.apk_sha256,
            check_output=lambda *args, **kwargs: self.commit + "\n",
            **kwargs,
        )

    def test_runs_device_qualification_build_install_launch_and_backend_recheck_on_same_device(self):
        calls = []

        def runner(argv, *, check):
            calls.append((list(argv), check))
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            result = self._run(runner, serial="device-123")

        self.assertTrue(result["ready"])
        self.assertEqual(result["commit"], self.commit)
        self.assertEqual(result["apk_sha256"], self.apk_sha256)
        self.assertEqual(
            result["completed_phases"],
            ["device_preflight", "qualification", "build", "install", "launch", "backend_recheck"],
        )
        expected_identity = {
            "commit_sha": self.commit,
            "api_base_url": self.handoff["api_base_url"],
            "application_package": module.APPLICATION_PACKAGE,
            "build_type": module.BUILD_TYPE,
            "apk_sha256": self.apk_sha256,
        }
        self.assertEqual(result["device_smoke_template"], module.DEVICE_SMOKE_TEMPLATE)
        self.assertEqual(result["device_smoke_prefill"], expected_identity)
        self.assertEqual(
            result["device_smoke_validation_command"],
            f"python {module.DEVICE_SMOKE_VALIDATOR} <PRIVATE_DEVICE_SMOKE_RECORD.json>",
        )
        self.assertEqual(
            result["device_smoke_summary_command"],
            f"python {module.DEVICE_SMOKE_SUMMARIZER} <PRIVATE_DEVICE_SMOKE_RECORD.json>",
        )
        self.assertEqual(result["stage3_capture_template"], module.STAGE3_CAPTURE_TEMPLATE)
        self.assertEqual(result["stage3_capture_prefill"], expected_identity)
        self.assertEqual(
            result["stage3_capture_validation_command"],
            f"python {module.STAGE3_CAPTURE_VALIDATOR} <PRIVATE_STAGE3_CAPTURE_RECORD.json>",
        )
        self.assertIn("prefilled private device-smoke record", result["next_action"])
        self.assertIn("same device", result["next_action"])
        self.assertIn("privacy-safe summary", result["next_action"])
        self.assertIn("prefilled Stage 3 capture record", result["next_action"])
        self.assertIn("validate it before final readiness review", result["next_action"])
        self.assertEqual(calls[0][0], [sys.executable, module.DEVICE_PREFLIGHT_SCRIPT, "--serial", "device-123"])
        self.assertEqual(calls[1][0], self.handoff["qualification_argv"])
        self.assertEqual(calls[2][0], self.handoff["build_argv"])
        self.assertEqual(
            calls[3][0],
            [
                sys.executable,
                module.INSTALL_SCRIPT,
                module.ARTIFACT_DIRECTORY,
                "--expected-commit",
                self.commit,
                "--expected-api-base-url",
                self.handoff["api_base_url"],
                "--serial",
                "device-123",
            ],
        )
        self.assertEqual(calls[4][0], [sys.executable, module.LAUNCH_SCRIPT, "--serial", "device-123"])
        self.assertEqual(
            calls[5][0],
            [
                sys.executable,
                module.BACKEND_PREFLIGHT_SCRIPT,
                self.handoff["api_base_url"],
                "--season-id",
                self.handoff["season_id"],
                "--timeout",
                "5.0",
            ],
        )

    def test_failed_device_preflight_stops_before_endpoint_preparation_or_qualification(self):
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            return SimpleNamespace(returncode=4)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff) as prepare_mock:
            with self.assertRaisesRegex(RuntimeError, "device_preflight failed with exit code 4"):
                self._run(runner)

        prepare_mock.assert_not_called()
        self.assertEqual(calls, [[sys.executable, module.DEVICE_PREFLIGHT_SCRIPT]])

    def test_missing_qualification_record_blocks_build(self):
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "required qualification record"):
                module.run_release_handoff(
                    runner=runner,
                    record_exists=lambda path: False,
                    artifact_exists=lambda path: True,
                    checksum_reader=lambda path: self.apk_sha256,
                    check_output=lambda *args, **kwargs: self.commit + "\n",
                )

        self.assertEqual(calls, [[sys.executable, module.DEVICE_PREFLIGHT_SCRIPT], self.handoff["qualification_argv"]])

    def test_missing_artifact_blocks_install_and_launch(self):
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "required Technical Alpha artifact directory"):
                module.run_release_handoff(
                    runner=runner,
                    record_exists=lambda path: True,
                    artifact_exists=lambda path: False,
                    checksum_reader=lambda path: self.apk_sha256,
                    check_output=lambda *args, **kwargs: self.commit + "\n",
                )

        self.assertEqual(
            calls,
            [
                [sys.executable, module.DEVICE_PREFLIGHT_SCRIPT],
                self.handoff["qualification_argv"],
                self.handoff["build_argv"],
            ],
        )

    def test_failed_install_stops_before_launch(self):
        returncodes = iter((0, 0, 0, 7))
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            return SimpleNamespace(returncode=next(returncodes))

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "install failed with exit code 7"):
                self._run(runner)

        self.assertEqual(len(calls), 4)

    def test_failed_launch_is_reported_after_verified_install(self):
        returncodes = iter((0, 0, 0, 0, 8))

        def runner(argv, *, check):
            return SimpleNamespace(returncode=next(returncodes))

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "launch failed with exit code 8"):
                self._run(runner)

    def test_failed_backend_recheck_blocks_gameplay_handoff(self):
        returncodes = iter((0, 0, 0, 0, 0, 9))

        def runner(argv, *, check):
            return SimpleNamespace(returncode=next(returncodes))

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "backend_recheck failed with exit code 9"):
                self._run(runner)

    def test_invalid_apk_checksum_blocks_evidence_handoff(self):
        def runner(argv, *, check):
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "checksum"):
                module.run_release_handoff(
                    runner=runner,
                    record_exists=lambda path: True,
                    artifact_exists=lambda path: True,
                    checksum_reader=lambda path: (_ for _ in ()).throw(
                        RuntimeError("Technical Alpha APK checksum manifest is invalid")
                    ),
                    check_output=lambda *args, **kwargs: self.commit + "\n",
                )


if __name__ == "__main__":
    unittest.main()
