#!/usr/bin/env python3
"""Qualify Technical Alpha backend continuity before building a tester APK."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from typing import Callable

from scripts.check_alpha_backend import run_preflight


@dataclass(frozen=True)
class EndpointQualification:
    endpoint_class: str
    duration_seconds: float
    interval_seconds: float
    attempts: int
    passed_attempts: int
    season_id: str
    ready: bool


def qualify_endpoint(
    api_base_url: str,
    *,
    duration_seconds: float = 900.0,
    interval_seconds: float = 30.0,
    timeout: float = 5.0,
    season_id: str = "2026-27",
    allow_loopback: bool = False,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> EndpointQualification:
    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    started = clock()
    attempts = 0
    passed_attempts = 0

    while True:
        run_preflight(
            api_base_url,
            season_id=season_id,
            timeout=timeout,
            allow_loopback=allow_loopback,
        )
        attempts += 1
        passed_attempts += 1

        elapsed = clock() - started
        if elapsed >= duration_seconds:
            break
        sleeper(min(interval_seconds, max(0.0, duration_seconds - elapsed)))

    return EndpointQualification(
        endpoint_class="loopback-development" if allow_loopback else "tester-reachable",
        duration_seconds=round(clock() - started, 3),
        interval_seconds=interval_seconds,
        attempts=attempts,
        passed_attempts=passed_attempts,
        season_id=season_id,
        ready=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("api_base_url")
    parser.add_argument("--duration-seconds", type=float, default=900.0)
    parser.add_argument("--interval-seconds", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument(
        "--allow-loopback",
        action="store_true",
        help="Allow localhost only for development or automated tests.",
    )
    args = parser.parse_args(argv)

    try:
        result = qualify_endpoint(
            args.api_base_url,
            duration_seconds=args.duration_seconds,
            interval_seconds=args.interval_seconds,
            timeout=args.timeout,
            season_id=args.season_id,
            allow_loopback=args.allow_loopback,
        )
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
