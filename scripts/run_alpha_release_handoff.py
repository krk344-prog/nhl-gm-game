#!/usr/bin/env python3
"""Run the guarded Technical Alpha device, endpoint, and APK build handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

from prepare_alpha_build import prepare_build_handoff

DEVICE_PREFLIGHT_SCRIPT = "scripts/check_alpha_android_device.py"


def run_release_handoff(
    *,
    api_base_url: str | None = None,
    season_id: str = "2026-27",
    timeout: float = 5.0,
    serial: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    record_exists: Callable[[str], bool] = lambda path: Path(path).is_file(),
) -> dict[str, object]:
    """Preflight one Android device, qualify the endpoint, and build one exact release candidate."""

    handoff = prepare_build_handoff(
        api_base_url=api_base_url,
        season_id=season_id,
        timeout=timeout,
    )

    device_argv = [sys.executable, DEVICE_PREFLIGHT_SCRIPT]
    if serial:
        device_argv.extend(["--serial", serial])

    phases: Sequence[tuple[str, Sequence[str]]] = (
        ("device_preflight", device_argv),
        ("qualification", handoff["qualification_argv"]),
        ("build", handoff["build_argv"]),
    )
    completed: list[str] = []

    for phase, phase_argv in phases:
        if phase == "build" and not record_exists(str(handoff["qualification_record"])):
            raise RuntimeError("Endpoint qualification completed without producing the required qualification record")

        result = runner(phase_argv, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"{phase} failed with exit code {result.returncode}")
        completed.append(phase)

    return {
        "ready": True,
        "api_base_url": handoff["api_base_url"],
        "season_id": handoff["season_id"],
        "qualification_record": handoff["qualification_record"],
        "completed_phases": completed,
        "next_action": "Verify the generated artifact, then install and launch that exact APK on the same preflighted Android device.",
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
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
