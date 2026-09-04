#!/usr/bin/env python3
"""Emit only privacy-safe Technical Alpha execution-readiness status.

The authoritative readiness checker intentionally emits a private payload because it can
contain a local API endpoint, a device selector, and an ephemeral device-identity key.
This wrapper is the shareable companion: it runs that checker unchanged, retains its
full output only in memory, and prints a deliberately small public summary.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Callable

PRIVATE_READINESS_SCRIPT = "scripts/check_alpha_execution_readiness.py"
PUBLIC_NEXT_ACTIONS = {
    "source": "Resolve the source checkout blocker and rerun readiness.",
    "device": "Resolve the Android device preflight blocker and rerun readiness.",
    "endpoint": "Resolve the tester endpoint preflight blocker and rerun readiness.",
    "unknown": "Resolve the facilitator preflight blocker and rerun readiness.",
}


def public_readiness_status(
    *,
    api_base_url: str | None = None,
    season_id: str = "2026-27",
    timeout: float = 5.0,
    serial: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> tuple[int, dict[str, object]]:
    """Run private readiness and return a shareable status without private diagnostics."""
    argv = [
        sys.executable,
        PRIVATE_READINESS_SCRIPT,
        "--season-id",
        season_id,
        "--timeout",
        str(timeout),
    ]
    if api_base_url:
        argv.extend(["--api-base-url", api_base_url])
    if serial:
        argv.extend(["--serial", serial])

    process_timeout = max(timeout + 15.0, 20.0)
    try:
        result = runner(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=process_timeout,
        )
    except subprocess.TimeoutExpired:
        return 1, {
            "ready": False,
            "blocker_scope": "unknown",
            "next_action": PUBLIC_NEXT_ACTIONS["unknown"],
        }

    detail = (result.stdout or result.stderr or "").strip()
    try:
        payload = json.loads(detail) if detail else {}
    except json.JSONDecodeError:
        payload = {}

    if result.returncode == 0 and isinstance(payload, dict):
        summary = payload.get("public_summary")
        if isinstance(summary, dict) and summary.get("ready") is True:
            return 0, dict(summary)

    blocker_scope = payload.get("blocker_scope") if isinstance(payload, dict) else None
    if blocker_scope not in PUBLIC_NEXT_ACTIONS:
        blocker_scope = "unknown"
    return 1, {
        "ready": False,
        "blocker_scope": blocker_scope,
        "next_action": PUBLIC_NEXT_ACTIONS[blocker_scope],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url")
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--serial")
    args = parser.parse_args(argv)

    returncode, payload = public_readiness_status(
        api_base_url=args.api_base_url,
        season_id=args.season_id,
        timeout=args.timeout,
        serial=args.serial,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return returncode


if __name__ == "__main__":
    sys.exit(main())
