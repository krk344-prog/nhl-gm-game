#!/usr/bin/env python3
"""Validate that one authorized Android device is ready for the Technical Alpha smoke test."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str
    details: dict[str, str]


def parse_adb_devices(output: str) -> list[AdbDevice]:
    devices: list[AdbDevice] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices attached") or line.startswith("*"):
            continue
        fields = line.split()
        if len(fields) < 2:
            continue
        details: dict[str, str] = {}
        for field in fields[2:]:
            if ":" in field:
                key, value = field.split(":", 1)
                details[key] = value
        devices.append(AdbDevice(serial=fields[0], state=fields[1], details=details))
    return devices


def select_device(devices: list[AdbDevice], requested_serial: str | None = None) -> AdbDevice:
    if requested_serial:
        matches = [device for device in devices if device.serial == requested_serial]
        if not matches:
            raise RuntimeError("requested Android device was not reported by adb")
        selected = matches[0]
    else:
        ready = [device for device in devices if device.state == "device"]
        if not ready:
            states = sorted({device.state for device in devices})
            detail = f"; observed states: {', '.join(states)}" if states else ""
            raise RuntimeError(f"no authorized Android device is ready{detail}")
        if len(ready) > 1:
            raise RuntimeError("multiple authorized Android devices are connected; rerun with --serial")
        selected = ready[0]

    if selected.state != "device":
        raise RuntimeError(f"selected Android device is {selected.state}, not authorized and ready")
    return selected


def inspect_device(
    requested_serial: str | None = None,
    *,
    which=shutil.which,
    check_output=subprocess.check_output,
) -> dict[str, object]:
    if not which("adb"):
        raise RuntimeError("adb was not found; install Android platform-tools and add adb to PATH")

    devices = parse_adb_devices(check_output(["adb", "devices", "-l"], text=True))
    selected = select_device(devices, requested_serial)
    prefix = ["adb", "-s", selected.serial]
    model = selected.details.get("model") or check_output(
        prefix + ["shell", "getprop", "ro.product.model"], text=True
    ).strip()
    android_version = check_output(
        prefix + ["shell", "getprop", "ro.build.version.release"], text=True
    ).strip()
    sdk_level = check_output(
        prefix + ["shell", "getprop", "ro.build.version.sdk"], text=True
    ).strip()

    if not model or not android_version or not sdk_level:
        raise RuntimeError("adb connected, but required device metadata could not be read")

    return {
        "status": "ready",
        "authorized_device_count": sum(device.state == "device" for device in devices),
        "selected_device": {
            "model": model,
            "android_version": android_version,
            "sdk_level": sdk_level,
        },
        "next_action": "install the checksum-verified APK on this exact device",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", help="adb serial to select when multiple authorized devices are connected")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect_device(args.serial), indent=2))
        return 0
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "block", "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
