#!/usr/bin/env python3
"""Validate that the exact Android Alpha package stayed alive and reached the foreground."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


class EmulatorLaunchError(ValueError):
    """Raised when packaged-launch evidence is not safe to treat as a pass."""


def _package_fatal_exception(logcat: str, package: str) -> bool:
    lines = logcat.splitlines()
    for index, line in enumerate(lines):
        if "FATAL EXCEPTION" not in line:
            continue
        block = "\n".join(lines[index : index + 20])
        if f"Process: {package}" in block:
            return True
    return False


def _package_anr(logcat: str, package: str) -> bool:
    lines = logcat.splitlines()
    for index, line in enumerate(lines):
        if "ANR in" not in line and "Application Not Responding" not in line:
            continue
        block = "\n".join(lines[index : index + 20])
        if package in block:
            return True
    return False


def validate_emulator_launch(
    logcat_path: Path,
    activity_dump_path: Path,
    package: str = "com.krk344.nhlgmgame",
) -> dict[str, object]:
    if not logcat_path.is_file():
        raise EmulatorLaunchError(f"missing emulator logcat: {logcat_path}")
    if not activity_dump_path.is_file():
        raise EmulatorLaunchError(f"missing activity dump: {activity_dump_path}")

    logcat = logcat_path.read_text(encoding="utf-8", errors="replace")
    activities = activity_dump_path.read_text(encoding="utf-8", errors="replace")

    if 'Invariant Violation: "main" has not been registered' in logcat:
        raise EmulatorLaunchError("Expo root component was not registered")
    if _package_fatal_exception(logcat, package):
        raise EmulatorLaunchError(f"fatal Android exception detected for {package}")
    if _package_anr(logcat, package):
        raise EmulatorLaunchError(f"Android application-not-responding event detected for {package}")
    if f"Process {package}" in logcat and "has died" in logcat:
        death_lines = [
            line
            for line in logcat.splitlines()
            if f"Process {package}" in line and "has died" in line
        ]
        if death_lines:
            raise EmulatorLaunchError(f"Android process died after launch: {death_lines[-1]}")

    foreground_lines = [
        line.strip()
        for line in activities.splitlines()
        if any(
            marker in line
            for marker in ("mResumedActivity", "topResumedActivity", "mFocusedApp")
        )
    ]
    if not any(package in line for line in foreground_lines):
        raise EmulatorLaunchError(
            f"{package} was not the resumed foreground application"
        )

    return {
        "status": "pass",
        "package": package,
        "fatal_exception_absent": True,
        "anr_absent": True,
        "process_death_absent": True,
        "root_component_registered": True,
        "foreground_confirmed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logcat", type=Path)
    parser.add_argument("activity_dump", type=Path)
    parser.add_argument("--package", default="com.krk344.nhlgmgame")
    args = parser.parse_args()

    try:
        result = validate_emulator_launch(args.logcat, args.activity_dump, args.package)
    except (OSError, EmulatorLaunchError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
