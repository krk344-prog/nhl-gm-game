#!/usr/bin/env python3
"""Reconcile Technical Alpha device, Stage 3, and first-session evidence before approval."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from scripts.validate_alpha_first_session_observation import validate_observation

DEVICE_PASSES = (
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

COMMIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
APK_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _load(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{label}_unreadable:{exc}"]
    if not isinstance(value, dict):
        return None, [f"{label}_must_be_object"]
    return value, []


def _normalized(value: Any) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


def validate(
    device: dict[str, Any],
    stage3: dict[str, Any],
    first_session: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    for field in DEVICE_PASSES:
        if device.get(field) is not True:
            errors.append(f"device_not_passed:{field}")

    if device.get("blockers") not in (None, []):
        errors.append("device_blockers_present")

    if stage3.get("stage3_decision") != "COMPLETE_UI_REVIEW_PENDING":
        errors.append("stage3_not_complete")
    if stage3.get("blockers") not in (None, []):
        errors.append("stage3_blockers_present")
    if stage3.get("open_major_defects") not in (None, []):
        errors.append("stage3_major_defects_present")

    errors.extend(f"first_session:{error}" for error in validate_observation(first_session))

    device_commit = _normalized(device.get("commit_sha"))
    stage3_commit = _normalized(stage3.get("commit_sha"))
    session_package = first_session.get("package_identity", {})
    session_commit = _normalized(session_package.get("commit_sha"))
    commits = (device_commit, stage3_commit, session_commit)
    if not all(COMMIT_SHA_PATTERN.fullmatch(value) for value in commits):
        errors.append("invalid_format:commit_sha")
    if not all(commits) or len(set(commits)) != 1:
        errors.append("identity_mismatch:commit_sha")

    device_apk = _normalized(device.get("apk_sha256"))
    stage3_apk = _normalized(stage3.get("apk_sha256"))
    session_apk = _normalized(session_package.get("apk_sha256"))
    apk_hashes = (device_apk, stage3_apk, session_apk)
    if not all(APK_SHA256_PATTERN.fullmatch(value) for value in apk_hashes):
        errors.append("invalid_format:apk_sha256")
    if not all(apk_hashes) or len(set(apk_hashes)) != 1:
        errors.append("identity_mismatch:apk_sha256")

    if stage3.get("application_package") != "com.krk344.nhlgmgame":
        errors.append("invalid:application_package")
    if stage3.get("build_type") != "standalone-release-apk":
        errors.append("invalid:build_type")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device_record", type=Path)
    parser.add_argument("stage3_record", type=Path)
    parser.add_argument("first_session_record", type=Path)
    args = parser.parse_args()

    device, device_errors = _load(args.device_record, "device_record")
    stage3, stage3_errors = _load(args.stage3_record, "stage3_record")
    first_session, first_session_errors = _load(
        args.first_session_record, "first_session_record"
    )
    errors = device_errors + stage3_errors + first_session_errors
    if device is not None and stage3 is not None and first_session is not None:
        errors.extend(validate(device, stage3, first_session))

    status = "ready_for_kyle_approval" if not errors else "block"
    print(json.dumps({
        "status": status,
        "errors": errors,
        "commit_sha": stage3.get("commit_sha") if stage3 else None,
        "apk_sha256": stage3.get("apk_sha256") if stage3 else None,
        "first_session_evidence_required": True,
        "pilot_started": False,
        "merge_authorized": False,
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
