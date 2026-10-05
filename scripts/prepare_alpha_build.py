#!/usr/bin/env python3
"""Prepare one verified local build command for a Technical Alpha APK."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Callable, Iterable

from check_alpha_backend import PreflightResult, run_preflight
from select_alpha_api_endpoint import discover_private_ipv4_addresses, select_endpoint

PR_BRANCH = "agent/alpha-rules-integration-v1"
BUILD_SCRIPT = "scripts/build_alpha_apk_local.py"
QUALIFICATION_SCRIPT = "scripts/qualify_alpha_endpoint.py"
QUALIFICATION_RECORD = "artifacts/alpha-endpoint-qualification.json"
QUALIFICATION_MINIMUM_SECONDS = 300
QUALIFICATION_BUILD_WINDOW_SECONDS = 1800


def prepare_build_handoff(
    *,
    api_base_url: str | None = None,
    season_id: str = "2026-27",
    timeout: float = 5.0,
    addresses: Iterable[str] | None = None,
    preflight: Callable[..., PreflightResult] = run_preflight,
) -> dict[str, object]:
    """Select and preflight one endpoint, then return locked qualification/build commands."""

    source = "explicit"
    if api_base_url is None:
        source = "discovered"
        candidates = discover_private_ipv4_addresses() if addresses is None else tuple(addresses)
        api_base_url = select_endpoint(candidates).recommended_api_base_url

    selected_api_base_url = api_base_url.rstrip("/")
    result = preflight(
        selected_api_base_url,
        season_id=season_id,
        timeout=timeout,
        allow_loopback=False,
    )
    if not result.ready:
        raise RuntimeError("Backend preflight did not mark the endpoint ready")
    if result.api_base_url.rstrip("/") != selected_api_base_url:
        raise RuntimeError(
            "Backend preflight returned a different endpoint; refusing to package an unqualified API target"
        )

    qualification_command = [
        sys.executable,
        QUALIFICATION_SCRIPT,
        selected_api_base_url,
        "--season-id",
        season_id,
        "--duration-seconds",
        str(QUALIFICATION_MINIMUM_SECONDS),
        "--output",
        QUALIFICATION_RECORD,
    ]
    build_command = [
        sys.executable,
        BUILD_SCRIPT,
        "--api-base-url",
        selected_api_base_url,
        "--qualification-record",
        QUALIFICATION_RECORD,
        "--execute",
    ]
    return {
        "ready": True,
        "endpoint_source": source,
        "api_base_url": selected_api_base_url,
        "season_id": result.season_id,
        "regular_season_games": result.regular_season_games,
        "ref": PR_BRANCH,
        "qualification_script": QUALIFICATION_SCRIPT,
        "qualification_record": QUALIFICATION_RECORD,
        "qualification_minimum_seconds": QUALIFICATION_MINIMUM_SECONDS,
        "qualification_build_window_seconds": QUALIFICATION_BUILD_WINDOW_SECONDS,
        "qualification_argv": qualification_command,
        "qualification_command": shlex.join(qualification_command),
        "build_script": BUILD_SCRIPT,
        "build_argv": build_command,
        "build_command": shlex.join(build_command),
        "endpoint_lock": (
            "Qualification and build must use the same api_base_url. If the endpoint changes, discard the prior "
            "qualification record and rerun qualification for the new endpoint before building."
        ),
        "expired_qualification_recovery": (
            "If the 30-minute build window expires, rerun qualification_command and use the newly generated "
            "qualification_record before starting build_command."
        ),
        "next_action": (
            "Run qualification_command first and allow the required five-minute continuity soak to complete. "
            "Confirm qualification_record exists and ready=true, then start build_command within 30 minutes "
            "of qualification so the evidence is still fresh. Keep the exact same api_base_url for qualification "
            "and build; if the endpoint changes, discard the prior record and requalify the new endpoint. If the "
            "30-minute window expires, rerun qualification_command before building; do not reuse stale evidence."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url")
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args(argv)

    try:
        payload = prepare_build_handoff(
            api_base_url=args.api_base_url,
            season_id=args.season_id,
            timeout=args.timeout,
        )
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
