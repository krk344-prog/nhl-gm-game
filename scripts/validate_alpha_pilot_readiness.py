#!/usr/bin/env python3
"""Reconcile Technical Alpha device-smoke and Stage 3 evidence before pilot approval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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


def validate(device: dict[str, Any], stage3: dict[str, Any]) -> list[str]:
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

    device_commit = _normalized(device.get("commit_sha"))
    stage3_commit = _normalized(stage3.get("commit_sha"))
    if not device_commit or not stage3_commit or device_commit != stage3_commit:
        errors.append("identity_mismatch:commit_sha")

    device_apk = _normalized(device.get("apk_sha256"))
    stage3_apk = _normalized(stage3.get("apk_sha256"))
    if not device_apk or not stage3_apk or device_apk != stage3_apk:
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
    args = parser.parse_args()

    device, device_errors = _load(args.device_record, "device_record")
    stage3, stage3_errors = _load(args.stage3_record, "stage3_record")
    errors = device_errors + stage3_errors
    if device is not None and stage3 is not None:
        errors.extend(validate(device, stage3))

    status = "ready_for_kyle_approval" if not errors else "block"
    print(json.dumps({
        "status": status,
        "errors": errors,
        "commit_sha": stage3.get("commit_sha") if stage3 else None,
        "apk_sha256": stage3.get("apk_sha256") if stage3 else None,
        "pilot_started": False,
        "merge_authorized": False,
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
