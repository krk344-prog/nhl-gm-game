#!/usr/bin/env python3
"""Run the guarded Technical Alpha device, endpoint, build, install, and launch handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

from prepare_alpha_build import prepare_build_handoff

DEVICE_PREFLIGHT_SCRIPT = "scripts/check_alpha_android_device.py"
INSTALL_SCRIPT = "scripts/install_alpha_apk.py"
LAUNCH_SCRIPT = "scripts/launch_alpha_app.py"
ARTIFACT_DIRECTORY = "dist/technical-alpha"


def run_release_handoff(
    *,
    api_base_url: str | None = None,
    season_id: str = "2026-27",
    timeout: float = 5.0,
    serial: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    record_exists: Callable[[str], bool] = lambda path: Path(path).is_file(),
    artifact_exists: Callable[[str], bool] = lambda path: Path(path).is_dir(),
    check_output: Callable[..., str] = subprocess.check_output,
) -> dict[str, object]:
    """Preflight one device, qualify the endpoint, build, install, and launch one release candidate."""

    handoff = prepare_build_handoff(
        api_base_url=api_base_url,
        season_id=season_id,
        timeout=timeout,
    )
    commit = check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if not commit:
        raise RuntimeError("could not determine the exact PR #13 commit for release handoff")

    device_argv = [sys.executable, DEVICE_PREFLIGHT_SCRIPT]
    if serial:
        device_argv.extend(["--serial", serial])

    install_argv = [
        sys.executable,
        INSTALL_SCRIPT,
        ARTIFACT_DIRECTORY,
        "--expected-commit",
        commit,
        "--expected-api-base-url",
        str(handoff["api_base_url"]),
    ]
    launch_argv = [sys.executable, LAUNCH_SCRIPT]
    if serial:
        install_argv.extend(["--serial", serial])
        launch_argv.extend(["--serial", serial])

    phases: Sequence[tuple[str, Sequence[str]]] = (
        ("device_preflight", device_argv),
        ("qualification", handoff["qualification_argv"]),
        ("build", handoff["build_argv"]),
        ("install", install_argv),
        ("launch", launch_argv),
    )
    completed: list[str] = []

    for phase, phase_argv in phases:
        if phase == "build" and not record_exists(str(handoff["qualification_record"])):
            raise RuntimeError("Endpoint qualification completed without producing the required qualification record")
        if phase == "install" and not artifact_exists(ARTIFACT_DIRECTORY):
            raise RuntimeError("Release build completed without producing the required Technical Alpha artifact directory")

        result = runner(phase_argv, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"{phase} failed with exit code {result.returncode}")
        completed.append(phase)

    return {
        "ready": True,
        "api_base_url": handoff["api_base_url"],
        "season_id": handoff["season_id"],
        "commit": commit,
        "qualification_record": handoff["qualification_record"],
        "artifact_directory": ARTIFACT_DIRECTORY,
        "completed_phases": completed,
        "next_action": "Complete the guided Technical Alpha gameplay, save/reload, debug, and reset smoke route on this same device, then capture Stage 3 evidence.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url")
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--serial", help="adb serial to select when multiple authorized Android devices are connected")
    args = parser.parse_args(argv)

    try:
        payload = run_release_handoff(
            api_base_url=args.api_base_url,
            season_id=args.season_id,
            timeout=args.timeout,
            serial=args.serial,
        )
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
