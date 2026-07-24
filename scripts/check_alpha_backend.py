#!/usr/bin/env python3
"""Verify a Technical Alpha backend before building or installing a tester APK."""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from dataclasses import dataclass, asdict
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen


@dataclass(frozen=True)
class PreflightResult:
    api_base_url: str
    health_status: str
    api_version: str
    season_id: str
    regular_season_games: int
    ready: bool


def _normalized_base_url(value: str, *, allow_loopback: bool = False) -> str:
    raw = value.strip().rstrip("/")
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("API URL must be an absolute http:// or https:// URL")

    host = parsed.hostname
    if not allow_loopback:
        if host == "localhost":
            raise ValueError("localhost cannot be reached from a separate tester device")
        try:
            if ipaddress.ip_address(host).is_loopback:
                raise ValueError("loopback addresses cannot be reached from a tester device")
        except ValueError as exc:
            if "loopback" in str(exc):
                raise
            # A DNS hostname is acceptable.

    return raw


def _get_json(url: str, timeout: float) -> tuple[int, dict[str, Any]]:
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {"error": str(exc)}
        return exc.code, payload
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Unable to reach {url}: {exc}") from exc


def run_preflight(
    api_base_url: str,
    *,
    season_id: str = "2026-27",
    timeout: float = 5.0,
    allow_loopback: bool = False,
) -> PreflightResult:
    base = _normalized_base_url(api_base_url, allow_loopback=allow_loopback)

    health_status, health = _get_json(f"{base}/health", timeout)
    if health_status != 200 or health.get("status") != "ok":
        raise RuntimeError(f"Health check failed: HTTP {health_status} {health}")

    context_status, context_payload = _get_json(
        f"{base}/season-context?season_id={season_id}", timeout
    )
    if context_status != 200:
        raise RuntimeError(
            f"Season-context check failed: HTTP {context_status} {context_payload}"
        )

    context = context_payload.get("season_context") or {}
    if context.get("season_id") != season_id:
        raise RuntimeError("Season-context response did not match the requested season")

    games = context.get("regular_season_games")
    if not isinstance(games, int) or games <= 0:
        raise RuntimeError("Season-context response did not include a valid game count")

    return PreflightResult(
        api_base_url=base,
        health_status=str(health["status"]),
        api_version=str(health.get("version", "unknown")),
        season_id=season_id,
        regular_season_games=games,
        ready=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("api_base_url")
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--allow-loopback",
        action="store_true",
        help="Allow localhost only for development or automated tests.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_preflight(
            args.api_base_url,
            season_id=args.season_id,
            timeout=args.timeout,
            allow_loopback=args.allow_loopback,
        )
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
