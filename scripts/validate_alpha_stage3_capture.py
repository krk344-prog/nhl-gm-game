#!/usr/bin/env python3
"""Validate the machine-readable Technical Alpha Stage 3 capture record."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

REQUIRED_CAPTURES = {
    "S3-01": "launch_or_connection",
    "S3-02": "new_game_franchise_selection",
    "S3-03": "dashboard_after_advance_day",
    "S3-04": "roster",
    "S3-05": "standings",
    "S3-06": "trade",
    "S3-07": "reloaded_save",
    "S3-08": "reset_confirmation_and_result",
    "S3-09": "non_ideal_recovery",
}
REQUIRED_PRECONDITIONS = (
    "artifact_identity_passed",
    "backend_qualification_passed",
    "guided_route_passed",
    "save_reload_passed",
    "reset_to_day_one_passed",
    "device_smoke_passed",
    "privacy_review_passed",
)
REQUIRED_UI_CHECKS = (
    "primary_action_clear",
    "non_color_status",
    "text_readable_without_clipping",
    "touch_targets_distinct",
    "recovery_states_explicit",
    "franchise_and_day_context_visible",
    "dense_information_scannable",
    "fictional_alpha_disclosure_clear",
    "privacy_boundary_passed",
)
REQUIRED_SIGN_OFF = (
    "capture_owner",
    "ui_ux_reviewer",
    "testing_reviewer",
    "privacy_reviewer",
    "release_reviewer",
)
REQUIRED_TEXT = (
    "commit_sha",
    "apk_sha256",
    "application_package",
    "api_base_url",
    "build_type",
    "endpoint_class",
    "anonymous_tester_id",
    "route_result_reference",
    "captured_at",
)
MAX_EVIDENCE_AGE = timedelta(days=7)
TESTER_CODE_RE = re.compile(r"^T\d{2}$")


def _blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _safe_private_reference(value: Any) -> bool:
    if _blank(value):
        return False
    text = value.strip().replace("\\", "/")
    path = PurePosixPath(text)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.parts
        and path.parts[0] == "private"
    )


def _valid_api_base_url(value: Any) -> bool:
    if _blank(value):
        return False
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if parsed.query or parsed.fragment or parsed.path.rstrip("/") != "/api/v1":
        return False
    host = parsed.hostname.lower()
    if host == "localhost" or host == "0.0.0.0" or host == "::1" or host.startswith("127."):
        return False
    return True


def _endpoint_class_matches(value: Any, endpoint_class: Any) -> bool:
    if _blank(value) or endpoint_class not in {"private_lan", "approved_hosted_test"}:
        return False
    try:
        host = urlsplit(value.strip()).hostname
        address = ipaddress.ip_address(host) if host else None
    except ValueError:
        address = None
    is_private_lan = bool(address and address.is_private and not address.is_loopback)
    return (endpoint_class == "private_lan" and is_private_lan) or (
        endpoint_class == "approved_hosted_test" and not is_private_lan
    )


def _parse_utc_timestamp(value: Any) -> datetime | None:
    if _blank(value):
        return None
    text = value.strip()
    if not text.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def validate_record(record: dict[str, Any], *, now: datetime | None = None) -> list[str]:
    errors: list[str] = []

    if record.get("schema_version") != 1:
        errors.append("invalid:schema_version")

    for field in REQUIRED_TEXT:
        if _blank(record.get(field)):
            errors.append(f"missing_or_blank:{field}")

    commit_sha = record.get("commit_sha")
    if isinstance(commit_sha, str) and commit_sha.strip():
        normalized = commit_sha.strip().lower()
        if len(normalized) < 7 or any(ch not in "0123456789abcdef" for ch in normalized):
            errors.append("invalid:commit_sha")

    apk_sha256 = record.get("apk_sha256")
    if isinstance(apk_sha256, str) and apk_sha256.strip():
        normalized = apk_sha256.strip().lower()
        if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
            errors.append("invalid:apk_sha256")

    api_base_url = record.get("api_base_url")
    if not _blank(api_base_url) and not _valid_api_base_url(api_base_url):
        errors.append("invalid:api_base_url")

    endpoint_class = record.get("endpoint_class")
    if endpoint_class not in {"private_lan", "approved_hosted_test"}:
        errors.append("invalid:endpoint_class")
    elif not _blank(api_base_url) and _valid_api_base_url(api_base_url) and not _endpoint_class_matches(api_base_url, endpoint_class):
        errors.append("mismatch:endpoint_class")

    anonymous_tester_id = record.get("anonymous_tester_id")
    if not _blank(anonymous_tester_id) and not TESTER_CODE_RE.fullmatch(anonymous_tester_id.strip()):
        errors.append("invalid:anonymous_tester_id")

    route_result_reference = record.get("route_result_reference")
    if not _blank(route_result_reference) and not _safe_private_reference(route_result_reference):
        errors.append("invalid:route_result_reference")

    captured_at = record.get("captured_at")
    if not _blank(captured_at):
        parsed_captured_at = _parse_utc_timestamp(captured_at)
        if parsed_captured_at is None:
            errors.append("invalid:captured_at")
        else:
            now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
            if parsed_captured_at > now_utc:
                errors.append("future:captured_at")
            elif now_utc - parsed_captured_at > MAX_EVIDENCE_AGE:
                errors.append("stale:captured_at")

    if record.get("application_package") != "com.krk344.nhlgmgame":
        errors.append("invalid:application_package")
    if record.get("build_type") != "standalone-release-apk":
        errors.append("invalid:build_type")

    preconditions = record.get("preconditions")
    if not isinstance(preconditions, dict):
        errors.append("missing:preconditions")
    else:
        for field in REQUIRED_PRECONDITIONS:
            if preconditions.get(field) is not True:
                errors.append(f"not_passed:preconditions.{field}")

    captures = record.get("captures")
    if not isinstance(captures, dict):
        errors.append("missing:captures")
    else:
        for capture_id, expected_state in REQUIRED_CAPTURES.items():
            capture = captures.get(capture_id)
            if not isinstance(capture, dict):
                errors.append(f"missing:capture.{capture_id}")
                continue
            if capture.get("state") != expected_state:
                errors.append(f"invalid_state:capture.{capture_id}")
            if capture.get("result") != "PASS":
                errors.append(f"not_passed:capture.{capture_id}")
            private_reference = capture.get("private_reference")
            if _blank(private_reference):
                errors.append(f"missing_private_reference:capture.{capture_id}")
            elif not _safe_private_reference(private_reference):
                errors.append(f"invalid_private_reference:capture.{capture_id}")

    ui_checks = record.get("ui_checks")
    if not isinstance(ui_checks, dict):
        errors.append("missing:ui_checks")
    else:
        for field in REQUIRED_UI_CHECKS:
            if ui_checks.get(field) is not True:
                errors.append(f"not_passed:ui_checks.{field}")

    if record.get("blockers") not in (None, []):
        errors.append("blockers_present")
    if record.get("open_major_defects") not in (None, []):
        errors.append("major_defects_present")

    sign_off = record.get("sign_off")
    if not isinstance(sign_off, dict):
        errors.append("missing:sign_off")
    else:
        for field in REQUIRED_SIGN_OFF:
            if _blank(sign_off.get(field)):
                errors.append(f"missing_or_blank:sign_off.{field}")

    if record.get("stage3_decision") != "COMPLETE_UI_REVIEW_PENDING":
        errors.append("invalid:stage3_decision")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
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
    print(json.dumps({
        "status": "pass" if not errors else "block",
        "errors": errors,
        "commit_sha": payload.get("commit_sha"),
        "api_base_url": payload.get("api_base_url"),
        "capture_count": len(payload.get("captures", {})) if isinstance(payload.get("captures"), dict) else 0,
        "stage3_decision": payload.get("stage3_decision"),
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
