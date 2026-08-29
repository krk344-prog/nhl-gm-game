#!/usr/bin/env python3
"""Fail closed on incomplete or privacy-unsafe Technical Alpha bug reports."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TESTER_CODE_RE = re.compile(r"^T\d{2}$")
ALLOWED_SEVERITIES = {"Minor", "Major", "Blocker"}
ALLOWED_ROUTES = {
    "application_launch",
    "new_game",
    "franchise_selection",
    "advance_day",
    "roster",
    "standings",
    "trade",
    "trade_history",
    "save",
    "reload",
    "debug_report",
    "reset",
}
PRIVATE_KEYS = {
    "tester_name",
    "email",
    "device_serial",
    "endpoint_url",
    "ip_address",
    "credentials",
    "raw_log",
    "database_path",
    "save_path",
}


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _contains_private_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).lower() in PRIVATE_KEYS or _contains_private_key(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_private_key(item) for item in value)
    return False


def _safe_attachment_reference(value: Any) -> bool:
    reference = str(value or "").strip()
    if not reference or "\\" in reference:
        return False
    path = PurePosixPath(reference)
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def validate_report(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _require(payload.get("schema_version") == 1, "schema_version must be 1", errors)
    _require(not _contains_private_key(payload), "report contains a prohibited private field", errors)

    package = payload.get("package_identity", {})
    _require(package.get("pr_number") == 13, "package must come from PR #13", errors)
    _require(bool(COMMIT_RE.fullmatch(str(package.get("commit_sha", "")))), "commit_sha must be a lowercase 40-character SHA", errors)
    _require(bool(SHA256_RE.fullmatch(str(package.get("apk_sha256", "")))), "apk_sha256 must be a lowercase 64-character digest", errors)
    _require(package.get("android_package") == "com.krk344.nhlgmgame", "Android package identity is invalid", errors)
    _require(package.get("build_type") == "standalone-release-apk", "build_type must be standalone-release-apk", errors)

    report = payload.get("report", {})
    _require(bool(TESTER_CODE_RE.fullmatch(str(report.get("tester_code", "")))), "tester_code must use anonymous T## format", errors)
    _require(report.get("severity") in ALLOWED_SEVERITIES, "severity must be Minor, Major, or Blocker", errors)
    _require(report.get("route") in ALLOWED_ROUTES, "route is not part of the controlled Alpha smoke path", errors)
    _require(isinstance(report.get("reproducible"), bool), "reproducible must be true or false", errors)
    _require(bool(str(report.get("expected", "")).strip()), "expected behavior is required", errors)
    _require(bool(str(report.get("actual", "")).strip()), "actual behavior is required", errors)
    steps = report.get("steps", [])
    _require(isinstance(steps, list) and 1 <= len(steps) <= 12, "provide 1-12 reproduction steps", errors)
    if isinstance(steps, list):
        _require(all(isinstance(step, str) and step.strip() for step in steps), "every reproduction step must be non-empty text", errors)
    _require(bool(str(report.get("first_interpretation", "")).strip()), "first interpretation must be recorded before coaching", errors)
    _require(bool(str(report.get("highest_friction_moment", "")).strip()), "highest-friction moment is required", errors)
    _require(report.get("fictional_alpha_limitation_acknowledged") is True, "fictional eight-franchise/82-game Alpha limitation must be acknowledged", errors)
    _require(report.get("ui_status") == "UI Review Pending", "implemented UI must remain UI Review Pending", errors)

    attachments = payload.get("attachments", [])
    _require(isinstance(attachments, list) and len(attachments) <= 5, "attachments must be a list with at most five privacy-reviewed references", errors)
    if isinstance(attachments, list):
        for index, attachment in enumerate(attachments, start=1):
            _require(isinstance(attachment, dict), f"attachment {index} must be an object", errors)
            if not isinstance(attachment, dict):
                continue
            _require(attachment.get("privacy_reviewed") is True, f"attachment {index} must be privacy reviewed", errors)
            _require(attachment.get("kind") in {"screenshot", "redacted_log", "video"}, f"attachment {index} kind is invalid", errors)
            _require(_safe_attachment_reference(attachment.get("reference")), f"attachment {index} reference must be a safe relative evidence path", errors)

    authorization = payload.get("authorization", {})
    _require(authorization.get("pilot_approved_by_kyle") is False, "pilot approval must remain false until Kyle explicitly approves", errors)
    _require(authorization.get("merge_approved_by_kyle") is False, "merge approval must remain false until Kyle explicitly approves", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"report_error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("report_error: root value must be an object", file=sys.stderr)
        return 2
    errors = validate_report(payload)
    if errors:
        for error in errors:
            print(f"BLOCK: {error}", file=sys.stderr)
        return 1
    print("BUG_REPORT_READY: actionable, exact-package, anonymous, and privacy-reviewed; pilot and merge remain unauthorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
