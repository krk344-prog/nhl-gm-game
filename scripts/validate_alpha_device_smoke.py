#!/usr/bin/env python3
"""Validate a Technical Alpha exact-package device smoke record.

The validator is dependency-free and intentionally conservative. It accepts a JSON
record created by the facilitator after installing the checksum-verified APK and
running the approved pilot route. Any missing, failed, loopback-bound, or weakly
timestamped evidence blocks the record from being treated as pilot-ready.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REQUIRED_TRUE_FIELDS = (
    "artifact_verifier_passed",
    "apk_installed",
    "launch_confirmed",
    "health_passed",
    "season_context_passed",
    "franchise_selection_passed",
    "advance_day_passed",
    "roster_passed",
    "standings_passed",
    "trade_passed",
    "save_reload_passed",
    "debug_report_passed",
    "reset_passed",
)

REQUIRED_TEXT_FIELDS = (
    "commit_sha",
    "api_base_url",
    "device_model",
    "android_version",
    "apk_sha256",
    "tested_at",
)


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return True
    normalized = host.strip().lower()
    if normalized in {"localhost", "0.0.0.0", "::1"}:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _has_timezone_aware_iso_timestamp(value: str) -> bool:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field in REQUIRED_TEXT_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"missing_or_blank:{field}")

    commit_sha = record.get("commit_sha")
    if isinstance(commit_sha, str) and commit_sha.strip():
        normalized_commit = commit_sha.strip().lower()
        if len(normalized_commit) != 40 or any(ch not in "0123456789abcdef" for ch in normalized_commit):
            errors.append("invalid:commit_sha")

    apk_sha256 = record.get("apk_sha256")
    if isinstance(apk_sha256, str) and apk_sha256.strip():
        normalized_digest = apk_sha256.strip().lower()
        if len(normalized_digest) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_digest):
            errors.append("invalid:apk_sha256")

    tested_at = record.get("tested_at")
    if isinstance(tested_at, str) and tested_at.strip() and not _has_timezone_aware_iso_timestamp(tested_at):
        errors.append("invalid:tested_at")

    api_base_url = record.get("api_base_url")
    if isinstance(api_base_url, str) and api_base_url.strip():
        parsed = urlparse(api_base_url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            errors.append("invalid:api_base_url")
        else:
            if _is_loopback_host(parsed.hostname):
                errors.append("loopback:api_base_url")
            if not parsed.path.rstrip("/").endswith("/api/v1"):
                errors.append("invalid_api_path:api_base_url")

    for field in REQUIRED_TRUE_FIELDS:
        if record.get(field) is not True:
            errors.append(f"not_passed:{field}")

    blockers = record.get("blockers")
    if blockers not in (None, [], ""):
        errors.append("blockers_present")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Path to the device-smoke JSON record")
    args = parser.parse_args()

    try:
        payload = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "block", "errors": [f"record_unreadable:{exc}"]}, indent=2))
        return 2

    if not isinstance(payload, dict):
        print(json.dumps({"status": "block", "errors": ["record_must_be_object"]}, indent=2))
        return 2

    errors = validate_record(payload)
    result = {
        "status": "pass" if not errors else "block",
        "errors": errors,
        "commit_sha": payload.get("commit_sha"),
        "api_base_url": payload.get("api_base_url"),
        "device_model": payload.get("device_model"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
