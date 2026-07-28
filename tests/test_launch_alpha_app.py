from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import launch_alpha_app


class LaunchAlphaAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.device_summary = {
            "selected_device": {
                "model": "Pixel Test",
                "android_version": "16",
                "sdk_level": "36",
            }
        }

    def _check_output(self, command, *, text):
        if command[-2:] == ["devices", "-l"]:
            return "List of devices attached\nSERIAL device model:Pixel_Test\n"
        if command[-3:] == ["pm", "path", launch_alpha_app.ANDROID_PACKAGE]:
            return "package:/data/app/base.apk\n"
        if command[-2:] == ["pidof", launch_alpha_app.ANDROID_PACKAGE]:
            return "12345\n"
        raise AssertionError(f"unexpected command: {command}")

    @patch("launch_alpha_app.inspect_device")
    def test_launches_installed_package_and_confirms_process(self, inspect):
        inspect.return_value = self.device_summary

        def run(command, **kwargs):
            if "force-stop" in command:
                return subprocess.CompletedProcess(command, 0)
            if "monkey" in command:
                return subprocess.CompletedProcess(
                    command, 0, stdout="Events injected: 1\n", stderr=""
                )
            raise AssertionError(f"unexpected command: {command}")

        result = launch_alpha_app.launch_installed_app(
            check_output=self._check_output,
            run=run,
            sleep=lambda _: None,
        )

        self.assertEqual("pass", result["status"])
        self.assertTrue(result["launch_confirmed"])
        self.assertNotIn("SERIAL", str(result))

    @patch("launch_alpha_app.inspect_device")
    def test_blocks_when_launcher_command_fails(self, inspect):
        inspect.return_value = self.device_summary
        launch_run = Mock(
            side_effect=[
                subprocess.CompletedProcess([], 0),
                subprocess.CompletedProcess([], 1, stdout="", stderr="monkey failed"),
            ]
        )

        with self.assertRaisesRegex(RuntimeError, "app launch failed"):
            launch_alpha_app.launch_installed_app(
                check_output=self._check_output,
                run=launch_run,
                sleep=lambda _: None,
            )

    @patch("launch_alpha_app.inspect_device")
    def test_blocks_when_process_cannot_be_confirmed(self, inspect):
        inspect.return_value = self.device_summary

        def check_output(command, *, text):
            if command[-2:] == ["devices", "-l"]:
                return "List of devices attached\nSERIAL device model:Pixel_Test\n"
            if command[-3:] == ["pm", "path", launch_alpha_app.ANDROID_PACKAGE]:
                return "package:/data/app/base.apk\n"
            if command[-2:] == ["pidof", launch_alpha_app.ANDROID_PACKAGE]:
                return ""
            raise AssertionError(f"unexpected command: {command}")

        def run(command, **kwargs):
            if "force-stop" in command:
                return subprocess.CompletedProcess(command, 0)
            return subprocess.CompletedProcess(
                command, 0, stdout="Events injected: 1\n", stderr=""
            )

        with self.assertRaisesRegex(RuntimeError, "process"):
            launch_alpha_app.launch_installed_app(
                check_output=check_output,
                run=run,
                sleep=lambda _: None,
            )


if __name__ == "__main__":
    unittest.main()
