#!/usr/bin/env python3
"""Launch the installed Technical Alpha app and confirm its Android process starts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

from check_alpha_android_device import inspect_device, parse_adb_devices, select_device
from install_alpha_apk import ANDROID_PACKAGE


def launch_installed_app(
    requested_serial: str | None = None,
    *,
    check_output=subprocess.check_output,
    run=subprocess.run,
    sleep=time.sleep,
) -> dict[str, object]:
    """Launch the verified package on one authorized device and confirm a live process."""

    device_summary = inspect_device(requested_serial, check_output=check_output)
    devices = parse_adb_devices(check_output(["adb", "devices", "-l"], text=True))
    selected = select_device(devices, requested_serial)
    prefix = ["adb", "-s", selected.serial]

    package_path = check_output(
        prefix + ["shell", "pm", "path", ANDROID_PACKAGE],
        text=True,
    ).strip()
    if not package_path.startswith("package:"):
        raise RuntimeError(f"installed package {ANDROID_PACKAGE} could not be confirmed")

    run(prefix + ["shell", "am", "force-stop", ANDROID_PACKAGE], check=False)
    launch = run(
        prefix
        + [
            "shell",
            "monkey",
            "-p",
            ANDROID_PACKAGE,
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    combined_output = "\n".join(
        part for part in (launch.stdout, launch.stderr) if part
    ).strip()
    if launch.returncode != 0 or "events injected: 1" not in combined_output.lower():
        raise RuntimeError(f"app launch failed: {combined_output or 'no diagnostic output'}")

    sleep(1.0)
    process_id = check_output(
        prefix + ["shell", "pidof", ANDROID_PACKAGE],
        text=True,
    ).strip()
    if not process_id or not all(part.isdigit() for part in process_id.split()):
        raise RuntimeError(f"Android process for {ANDROID_PACKAGE} could not be confirmed")

    return {
        "status": "pass",
        "android_package": ANDROID_PACKAGE,
        "device": device_summary["selected_device"],
        "installation_confirmed": True,
        "launch_confirmed": True,
        "next_action": "complete the guided Technical Alpha gameplay and persistence route",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", help="adb serial when multiple authorized devices are connected")
    args = parser.parse_args(argv)

    try:
        result = launch_installed_app(args.serial)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "block", "error": str(exc)}, sort_keys=True))
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
