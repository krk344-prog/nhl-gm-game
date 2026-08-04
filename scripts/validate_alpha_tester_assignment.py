#!/usr/bin/env python3
"""Validate controlled Technical Alpha tester assignments before a session starts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TESTER_CODE_RE = re.compile(r"^T\d{2}$")
REQUIRED_ROUTES = {
    "application_launch",
    "new_game",
    "franchise_selection",
    "advance_day",
    "roster",
    "standings",
    "trade",
    "save",
    "reload",
    "reset",
}


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_assignment(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require(payload.get("schema_version") == 1, "schema_version must be 1", errors)

    package = payload.get("package_identity", {})
    _require(package.get("pr_number") == 13, "package must come from PR #13", errors)
    _require(bool(COMMIT_RE.fullmatch(str(package.get("commit_sha", "")))), "commit_sha must be a 40-character lowercase hex SHA", errors)
    _require(bool(SHA256_RE.fullmatch(str(package.get("apk_sha256", "")))), "apk_sha256 must be a 64-character lowercase hex digest", errors)
    _require(package.get("android_package") == "com.krk344.nhlgmgame", "Android package identity is invalid", errors)
    _require(package.get("build_type") == "release", "build_type must be release", errors)
    _require(package.get("endpoint_class") in {"private-lan", "tester-accessible-hosted"}, "endpoint_class must be tester accessible", errors)

    session = payload.get("session", {})
    tester_count = session.get("tester_count")
    testers = payload.get("testers", [])
    _require(isinstance(tester_count, int) and 3 <= tester_count <= 5, "tester_count must be between 3 and 5", errors)
    _require(isinstance(testers, list) and len(testers) == tester_count, "tester list length must equal tester_count", errors)
    _require(session.get("fictional_alpha_disclosure_acknowledged") is True, "fictional Alpha disclosure must be acknowledged", errors)
    _require(session.get("known_limitations_acknowledged") is True, "known limitations must be acknowledged", errors)
    _require(session.get("facilitator_coaching_deferred_until_first_interpretation") is True, "facilitator must defer coaching until first interpretation is recorded", errors)

    codes: list[str] = []
    primary_owners: dict[str, list[str]] = {route: [] for route in REQUIRED_ROUTES}
    backup_owners: dict[str, list[str]] = {route: [] for route in REQUIRED_ROUTES}
    for index, tester in enumerate(testers if isinstance(testers, list) else []):
        if not isinstance(tester, dict):
            errors.append(f"tester {index + 1} must be an object")
            continue
        code = str(tester.get("code", ""))
        codes.append(code)
        _require(bool(TESTER_CODE_RE.fullmatch(code)), f"tester {index + 1} code is invalid", errors)
        _require(bool(str(tester.get("device_class", "")).strip()) and "<" not in str(tester.get("device_class", "")), f"tester {code or index + 1} device_class is required", errors)
        _require(tester.get("disclosure_acknowledged") is True, f"tester {code} disclosure must be acknowledged", errors)
        _require(tester.get("first_interpretation_recorded") is True, f"tester {code} first interpretation must be recorded", errors)
        _require(tester.get("highest_friction_moment_recorded") is True, f"tester {code} highest-friction moment must be recorded", errors)
        _require(tester.get("confidence_building_moment_recorded") is True, f"tester {code} confidence-building moment must be recorded", errors)
        primary = tester.get("primary_routes", [])
        backup = tester.get("backup_routes", [])
        _require(isinstance(primary, list) and bool(primary), f"tester {code} needs at least one primary route", errors)
        _require(isinstance(backup, list) and bool(backup), f"tester {code} needs at least one backup route", errors)
        for route in primary if isinstance(primary, list) else []:
            _require(route in REQUIRED_ROUTES, f"tester {code} has unknown primary route {route}", errors)
            if route in primary_owners:
                primary_owners[route].append(code)
        for route in backup if isinstance(backup, list) else []:
            _require(route in REQUIRED_ROUTES, f"tester {code} has unknown backup route {route}", errors)
            if route in backup_owners:
                backup_owners[route].append(code)

    _require(len(codes) == len(set(codes)), "tester codes must be unique", errors)
    for route in sorted(REQUIRED_ROUTES):
        _require(len(primary_owners[route]) == 1, f"route {route} must have exactly one primary owner", errors)
        _require(bool(backup_owners[route]), f"route {route} must have at least one backup observer", errors)
        if primary_owners[route] and backup_owners[route]:
            _require(primary_owners[route][0] not in backup_owners[route], f"route {route} primary owner cannot also be its backup", errors)

    ui = payload.get("ui_review", {})
    _require(ui.get("stage2_direction_preserved") is True, "approved Stage 2 direction must remain preserved", errors)
    _require(ui.get("implemented_screens_status") == "UI Review Pending", "implemented screens must remain UI Review Pending", errors)
    _require(ui.get("required_stage3_capture_count") == 9, "nine Stage 3 captures are required", errors)

    authorization = payload.get("authorization", {})
    _require(authorization.get("pilot_approved_by_kyle") is False, "pilot approval must remain false until Kyle explicitly approves", errors)
    _require(authorization.get("merge_approved_by_kyle") is False, "merge approval must remain false until Kyle explicitly approves", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assignment", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.assignment.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"assignment_error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("assignment_error: root value must be an object", file=sys.stderr)
        return 2
    errors = validate_assignment(payload)
    if errors:
        for error in errors:
            print(f"BLOCK: {error}", file=sys.stderr)
        return 1
    print("ASSIGNMENT_READY: 3-5 anonymous testers have exact-package route ownership and backup coverage; pilot remains unauthorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
