#!/usr/bin/env python3
"""Create a privacy-safe summary from a Technical Alpha device-smoke record.

Completed smoke records may contain a local-network endpoint, device model, Android
version, and APK digest. Those details are useful to the facilitator but should not
be copied into public issue or pull-request comments. This dependency-free command
validates the private record and emits only the minimum evidence needed for a pilot
approval decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from validate_alpha_device_smoke import REQUIRED_TRUE_FIELDS, validate_record


def _endpoint_class(api_base_url: Any) -> str:
    if not isinstance(api_base_url, str):
        return "unavailable"
    parsed = urlparse(api_base_url.strip())
    if parsed.scheme == "https":
        return "https"
    if parsed.scheme == "http" and parsed.hostname:
        return "private-or-controlled-http"
    return "unavailable"


def build_public_summary(record: dict[str, Any]) -> dict[str, Any]:
    errors = validate_record(record)
    commit_sha = record.get("commit_sha")
    short_commit = commit_sha.strip()[:12] if isinstance(commit_sha, str) else None
    passed_checks = sum(record.get(field) is True for field in REQUIRED_TRUE_FIELDS)
    blockers = record.get("blockers")
    blocker_count = len(blockers) if isinstance(blockers, list) else (1 if blockers else 0)

    return {
        "status": "pass" if not errors else "block",
        "commit": short_commit,
        "tested_at": record.get("tested_at"),
        "endpoint_class": _endpoint_class(record.get("api_base_url")),
        "checks_passed": passed_checks,
        "checks_required": len(REQUIRED_TRUE_FIELDS),
        "blocker_count": blocker_count,
        "error_codes": errors,
        "privacy": "Device model, Android version, endpoint host, and APK digest are intentionally omitted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Path to the private device-smoke JSON record")
    args = parser.parse_args()

    try:
        payload = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "block", "error_codes": [f"record_unreadable:{exc}"]}, indent=2))
        return 2

    if not isinstance(payload, dict):
        print(json.dumps({"status": "block", "error_codes": ["record_must_be_object"]}, indent=2))
        return 2

    summary = build_public_summary(payload)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
