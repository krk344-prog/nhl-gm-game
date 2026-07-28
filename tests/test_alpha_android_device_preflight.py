from __future__ import annotations

import unittest

from scripts.check_alpha_android_device import inspect_device, parse_adb_devices, select_device


ADB_OUTPUT = """List of devices attached
ABC123 device product:panther model:Pixel_7 device:panther transport_id:1
"""


class AlphaAndroidDevicePreflightTests(unittest.TestCase):
    def test_parses_and_selects_one_authorized_device(self) -> None:
        devices = parse_adb_devices(ADB_OUTPUT)
        selected = select_device(devices)
        self.assertEqual("ABC123", selected.serial)
        self.assertEqual("Pixel_7", selected.details["model"])

    def test_blocks_unauthorized_device(self) -> None:
        devices = parse_adb_devices(
            "List of devices attached\nABC123 unauthorized usb:1-1 transport_id:1\n"
        )
        with self.assertRaisesRegex(RuntimeError, "no authorized Android device"):
            select_device(devices)

    def test_blocks_multiple_devices_without_serial(self) -> None:
        devices = parse_adb_devices(
            "List of devices attached\nABC123 device model:Pixel_7\nXYZ789 device model:Pixel_8\n"
        )
        with self.assertRaisesRegex(RuntimeError, "multiple authorized Android devices"):
            select_device(devices)

    def test_requested_serial_must_be_ready(self) -> None:
        devices = parse_adb_devices(
            "List of devices attached\nABC123 offline transport_id:1\n"
        )
        with self.assertRaisesRegex(RuntimeError, "offline"):
            select_device(devices, "ABC123")

    def test_inspection_returns_privacy_safe_device_metadata(self) -> None:
        def fake_check_output(command: list[str], text: bool = True) -> str:
            if command == ["adb", "devices", "-l"]:
                return ADB_OUTPUT
            if command[-1] == "ro.build.version.release":
                return "16\n"
            if command[-1] == "ro.build.version.sdk":
                return "36\n"
            raise AssertionError(command)

        report = inspect_device(which=lambda name: "/sdk/adb", check_output=fake_check_output)
        self.assertEqual("ready", report["status"])
        self.assertEqual("Pixel_7", report["selected_device"]["model"])
        self.assertEqual("16", report["selected_device"]["android_version"])
        self.assertNotIn("ABC123", str(report))

    def test_blocks_when_adb_is_missing(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "adb was not found"):
            inspect_device(which=lambda name: None)


if __name__ == "__main__":
    unittest.main()
