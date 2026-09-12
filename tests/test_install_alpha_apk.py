from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import install_alpha_apk


class InstallAlphaApkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.artifact_dir = Path(self.temp_dir.name)
        (self.artifact_dir / install_alpha_apk.APK_NAME).write_bytes(b"apk")
        self.verification = {
            "commit": "abc123",
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "checksums": {install_alpha_apk.APK_NAME: "a" * 64},
        }
        self.device_summary = {
            "selected_device": {
                "model": "Pixel Test",
                "android_version": "16",
                "sdk_level": "36",
            }
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _check_output(self, command, *, text):
        if command[-2:] == ["devices", "-l"]:
            return "List of devices attached\nSERIAL device model:Pixel_Test\n"
        if command[-3:] == ["pm", "path", install_alpha_apk.ANDROID_PACKAGE]:
            return "package:/data/app/base.apk\n"
        raise AssertionError(f"unexpected command: {command}")

    @patch("install_alpha_apk.inspect_device")
    @patch("install_alpha_apk.verify_artifact")
    def test_installs_verified_apk_and_confirms_expected_package(self, verify, inspect):
        verify.return_value = self.verification
        inspect.return_value = self.device_summary
        install_run = Mock(
            return_value=subprocess.CompletedProcess([], 0, stdout="Success\n", stderr="")
        )

        result = install_alpha_apk.install_verified_apk(
            self.artifact_dir,
            "abc123",
            "http://192.168.1.20:8000/api/v1",
            check_output=self._check_output,
            run=install_run,
        )

        self.assertEqual("pass", result["status"])
        self.assertTrue(result["installation_confirmed"])
        self.assertEqual(install_alpha_apk.ANDROID_PACKAGE, result["android_package"])
        self.assertNotIn("SERIAL", str(result))
        self.assertIn("install", install_run.call_args.args[0])
        self.assertIn("-r", install_run.call_args.args[0])

    @patch("install_alpha_apk.inspect_device")
    @patch("install_alpha_apk.verify_artifact")
    def test_blocks_when_adb_install_fails(self, verify, inspect):
        verify.return_value = self.verification
        inspect.return_value = self.device_summary
        install_run = Mock(
            return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="INSTALL_FAILED")
        )

        with self.assertRaisesRegex(RuntimeError, "adb install failed"):
            install_alpha_apk.install_verified_apk(
                self.artifact_dir,
                "abc123",
                "http://192.168.1.20:8000/api/v1",
                check_output=self._check_output,
                run=install_run,
            )

    @patch("install_alpha_apk.inspect_device")
    @patch("install_alpha_apk.verify_artifact")
    def test_blocks_when_expected_package_cannot_be_confirmed(self, verify, inspect):
        verify.return_value = self.verification
        inspect.return_value = self.device_summary
        install_run = Mock(
            return_value=subprocess.CompletedProcess([], 0, stdout="Success\n", stderr="")
        )

        def missing_package(command, *, text):
            if command[-2:] == ["devices", "-l"]:
                return "List of devices attached\nSERIAL device model:Pixel_Test\n"
            if command[-3:] == ["pm", "path", install_alpha_apk.ANDROID_PACKAGE]:
                return ""
            raise AssertionError(f"unexpected command: {command}")

        with self.assertRaisesRegex(RuntimeError, "could not be confirmed"):
            install_alpha_apk.install_verified_apk(
                self.artifact_dir,
                "abc123",
                "http://192.168.1.20:8000/api/v1",
                check_output=missing_package,
                run=install_run,
            )


if __name__ == "__main__":
    unittest.main()
