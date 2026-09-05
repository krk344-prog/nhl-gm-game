#!/usr/bin/env python3
"""Qualify Technical Alpha backend continuity before building a tester APK."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from scripts.check_alpha_backend import PreflightResult, run_preflight


@dataclass(frozen=True)
class EndpointQualification:
    api_base_url: str
    endpoint_class: str
    duration_seconds: float
    interval_seconds: float
    attempts: int
    passed_attempts: int
    season_id: str
    qualified_at_utc: str
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
    utc_now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> EndpointQualification:
    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    selected_api_base_url = api_base_url.rstrip("/")
    started = clock()
    attempts = 0
    passed_attempts = 0
    first_result: PreflightResult | None = None

    while True:
        result = run_preflight(
            selected_api_base_url,
            season_id=season_id,
            timeout=timeout,
            allow_loopback=allow_loopback,
        )
        attempts += 1

        if first_result is None:
            first_result = result
        elif result != first_result:
            raise RuntimeError("Backend identity changed during endpoint qualification")

        passed_attempts += 1

        elapsed = clock() - started
        if elapsed >= duration_seconds:
            break
        sleeper(min(interval_seconds, max(0.0, duration_seconds - elapsed)))

    qualified_at = utc_now()
    if qualified_at.tzinfo is None or qualified_at.utcoffset() is None:
        raise ValueError("utc_now must return a timezone-aware datetime")

    return EndpointQualification(
        api_base_url=selected_api_base_url,
        endpoint_class="loopback-development" if allow_loopback else "tester-reachable",
        duration_seconds=round(clock() - started, 3),
        interval_seconds=interval_seconds,
        attempts=attempts,
        passed_attempts=passed_attempts,
        season_id=season_id,
        qualified_at_utc=qualified_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        ready=True,
    )


def write_qualification_record(result: EndpointQualification, output: str | Path) -> Path:
    """Persist the exact qualification evidence used for the pilot build handoff."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("api_base_url")
    parser.add_argument("--duration-seconds", type=float, default=900.0)
    parser.add_argument("--interval-seconds", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument(
        "--output",
        help="Write the successful qualification record to this JSON path.",
    )
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
        if args.output:
            write_qualification_record(result, args.output)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
