#!/usr/bin/env python3
"""Verify and install the exact Technical Alpha APK on one authorized Android device."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from check_alpha_android_device import inspect_device, parse_adb_devices, select_device
from verify_alpha_artifact import VerificationError, verify_artifact

APK_NAME = "nhl-gm-technical-alpha.apk"
ANDROID_PACKAGE = "com.krk344.nhlgmgame"


def install_verified_apk(
    artifact_directory: Path,
    expected_commit: str,
    expected_api_base_url: str,
    requested_serial: str | None = None,
    *,
    check_output=subprocess.check_output,
    run=subprocess.run,
) -> dict[str, object]:
    verification = verify_artifact(
        artifact_directory,
        expected_commit,
        expected_api_base_url,
    )
    device_summary = inspect_device(
        requested_serial,
        check_output=check_output,
    )

    devices = parse_adb_devices(check_output(["adb", "devices", "-l"], text=True))
    selected = select_device(devices, requested_serial)
    prefix = ["adb", "-s", selected.serial]
    apk_path = artifact_directory.resolve() / APK_NAME

    install = run(
        prefix + ["install", "-r", str(apk_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    combined_output = "\n".join(part for part in (install.stdout, install.stderr) if part).strip()
    if install.returncode != 0 or "success" not in combined_output.lower():
        raise RuntimeError(f"adb install failed: {combined_output or 'no diagnostic output'}")

    package_path = check_output(
        prefix + ["shell", "pm", "path", ANDROID_PACKAGE],
        text=True,
    ).strip()
    if not package_path.startswith("package:"):
        raise RuntimeError(f"installed package {ANDROID_PACKAGE} could not be confirmed")

    return {
        "status": "pass",
        "commit": verification["commit"],
        "api_base_url": verification["api_base_url"],
        "apk_sha256": verification["checksums"][APK_NAME],
        "android_package": ANDROID_PACKAGE,
        "device": device_summary["selected_device"],
        "installation_confirmed": True,
        "next_action": "launch the installed app and complete the guided Technical Alpha smoke route",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_directory", type=Path)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-api-base-url", required=True)
    parser.add_argument("--serial", help="adb serial when multiple authorized devices are connected")
    args = parser.parse_args(argv)

    try:
        result = install_verified_apk(
            args.artifact_directory,
            args.expected_commit,
            args.expected_api_base_url,
            args.serial,
        )
    except (OSError, RuntimeError, VerificationError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "block", "error": str(exc)}, sort_keys=True))
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
