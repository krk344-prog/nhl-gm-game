#!/usr/bin/env python3
"""Verify the certified Android device identity, then run the guarded Technical Alpha release handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from run_alpha_release_handoff import run_release_handoff

DEVICE_PREFLIGHT_SCRIPT = "scripts/check_alpha_android_device.py"


def _normalize(value: object) -> str:
    return str(value).strip()


def validate_certified_device(
    payload: object,
    *,
    model: str,
    android_version: str,
    sdk_level: str,
    device_identity: str,
) -> None:
    if not isinstance(payload, dict) or payload.get("status") != "ready":
        raise RuntimeError("certified device verification failed: device preflight did not confirm ready")
    selected = payload.get("selected_device")
    if not isinstance(selected, dict):
        raise RuntimeError("certified device verification failed: selected-device metadata is missing")

    expected = {
        "model": _normalize(model),
        "android_version": _normalize(android_version),
        "sdk_level": _normalize(sdk_level),
    }
    actual = {key: _normalize(selected.get(key, "")) for key in expected}
    if actual != expected:
        raise RuntimeError(
            "certified device changed after execution readiness; rerun readiness before release handoff"
        )

    actual_identity = _normalize(payload.get("device_identity", "")).lower()
    if actual_identity != _normalize(device_identity).lower():
        raise RuntimeError(
            "certified device identity changed after execution readiness; rerun readiness before release handoff"
        )


def run_certified_handoff(
    *,
    api_base_url: str | None,
    season_id: str,
    timeout: float,
    serial: str | None,
    evidence_directory: str,
    expected_source_commit: str,
    readiness_checked_at: str,
    expected_device_model: str,
    expected_android_version: str,
    expected_sdk_level: str,
    device_identity_key: str,
    expected_device_identity: str,
    runner=subprocess.run,
) -> dict[str, object]:
    device_argv = [
        sys.executable,
        DEVICE_PREFLIGHT_SCRIPT,
        "--identity-key",
        device_identity_key,
    ]
    if serial:
        device_argv.extend(["--serial", serial])
    result = runner(device_argv, check=False, capture_output=True, text=True)
    detail = (result.stdout or result.stderr or "").strip()
    try:
        payload = json.loads(detail) if detail else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError("certified device verification failed: device checker returned invalid JSON") from exc
    if result.returncode != 0:
        raise RuntimeError("certified device verification failed: device preflight blocked")

    validate_certified_device(
        payload,
        model=expected_device_model,
        android_version=expected_android_version,
        sdk_level=expected_sdk_level,
        device_identity=expected_device_identity,
    )

    return run_release_handoff(
        api_base_url=api_base_url,
        season_id=season_id,
        timeout=timeout,
        serial=serial,
        evidence_directory=evidence_directory,
        expected_source_commit=expected_source_commit,
        readiness_checked_at=readiness_checked_at,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url")
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--serial")
    parser.add_argument("--evidence-directory", default=".alpha-private")
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--readiness-checked-at", required=True)
    parser.add_argument("--expected-device-model", required=True)
    parser.add_argument("--expected-android-version", required=True)
    parser.add_argument("--expected-sdk-level", required=True)
    parser.add_argument("--device-identity-key", required=True)
    parser.add_argument("--expected-device-identity", required=True)
    args = parser.parse_args(argv)

    try:
        payload = run_certified_handoff(
            api_base_url=args.api_base_url,
            season_id=args.season_id,
            timeout=args.timeout,
            serial=args.serial,
            evidence_directory=args.evidence_directory,
            expected_source_commit=args.expected_source_commit,
            readiness_checked_at=args.readiness_checked_at,
            expected_device_model=args.expected_device_model,
            expected_android_version=args.expected_android_version,
            expected_sdk_level=args.expected_sdk_level,
            device_identity_key=args.device_identity_key,
            expected_device_identity=args.expected_device_identity,
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
