#!/usr/bin/env python3
"""Validate privacy-safe first-session observation evidence for the Technical Alpha."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TESTER_CODE_RE = re.compile(r"^T\d{2}$")
PRIVATE_TERMS = ("serial", "imei", "password", "token", "credential", "database path", "save path")


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _tester_reachable_endpoint(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value.strip())
        hostname = parsed.hostname
        if parsed.scheme not in {"http", "https"} or not hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        lowered = hostname.lower()
        if lowered in {"localhost", "0.0.0.0", "::", "::1"}:
            return False
        try:
            if ipaddress.ip_address(hostname).is_loopback:
                return False
        except ValueError:
            pass
    except ValueError:
        return False
    return True


def validate_observation(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require(payload.get("schema_version") == 1, "schema_version must be 1", errors)

    package = payload.get("package_identity", {})
    _require(package.get("pr_number") == 13, "package must come from PR #13", errors)
    _require(bool(COMMIT_RE.fullmatch(str(package.get("commit_sha", "")))), "commit_sha must be a 40-character lowercase hex SHA", errors)
    _require(bool(SHA256_RE.fullmatch(str(package.get("apk_sha256", "")))), "apk_sha256 must be a 64-character lowercase hex digest", errors)
    _require(package.get("android_package") == "com.krk344.nhlgmgame", "Android package identity is invalid", errors)
    _require(
        _tester_reachable_endpoint(package.get("api_base_url")),
        "api_base_url must be an explicit tester-reachable http(s) endpoint without credentials",
        errors,
    )

    observation = payload.get("observation", {})
    code = str(observation.get("tester_code", ""))
    _require(bool(TESTER_CODE_RE.fullmatch(code)), "tester_code must use an anonymous T## code", errors)
    _require(observation.get("fictional_alpha_disclosure_acknowledged") is True, "fictional Alpha disclosure must be acknowledged before franchise selection", errors)
    _require(observation.get("coaching_withheld_until_first_interpretation") is True, "facilitator coaching must be withheld until first interpretation is recorded", errors)
    for field in ("first_interpretation", "first_attempted_action", "highest_friction_moment", "independent_next_step"):
        value = str(observation.get(field, "")).strip()
        _require(bool(value), f"{field} is required", errors)
        lowered = value.lower()
        _require(not any(term in lowered for term in PRIVATE_TERMS), f"{field} contains prohibited private detail", errors)
    _require(observation.get("launch_reached") is True, "tester must reach the running application", errors)
    _require(observation.get("franchise_selection_reached") is True, "tester must reach franchise selection", errors)
    _require(observation.get("advance_day_identified_without_coaching") is True, "tester must independently identify how to advance the day", errors)

    ui = payload.get("ui_review", {})
    _require(ui.get("implemented_screens_status") == "UI Review Pending", "implemented screens must remain UI Review Pending", errors)
    _require(ui.get("stage2_direction_preserved") is True, "approved Stage 2 direction must remain preserved", errors)

    authorization = payload.get("authorization", {})
    _require(authorization.get("pilot_approved_by_kyle") is False, "pilot approval must remain false until Kyle explicitly approves", errors)
    _require(authorization.get("merge_approved_by_kyle") is False, "merge approval must remain false until Kyle explicitly approves", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observation", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.observation.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"observation_error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("observation_error: root value must be an object", file=sys.stderr)
        return 2
    errors = validate_observation(payload)
    if errors:
        for error in errors:
            print(f"BLOCK: {error}", file=sys.stderr)
        return 1
    print("FIRST_SESSION_READY: exact-package, uncoached onboarding evidence is complete; pilot remains unauthorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
