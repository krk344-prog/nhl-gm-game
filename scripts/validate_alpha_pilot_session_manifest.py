#!/usr/bin/env python3
"""Fail-closed validation for the Technical Alpha pilot session manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_ROUTE = (
    "new_game",
    "franchise_selection",
    "advance_day",
    "roster",
    "standings",
    "trade",
    "save",
    "reload",
    "reset",
)
REQUIRED_EVIDENCE = (
    "endpoint_qualification",
    "physical_or_equivalent_device_smoke",
    "save_reload_reconciliation",
    "stage3_capture_validation",
    "privacy_review",
)
MIN_ENDPOINT_QUALIFICATION_MINUTES = 15
BLOCKED_ENDPOINT_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _is_tester_accessible_api_url(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and parsed.hostname.lower() not in BLOCKED_ENDPOINT_HOSTS
    )


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return validation errors. An empty list means ready for Kyle approval."""
    errors: list[str] = []

    _require(manifest.get("schema_version") == 4, "schema_version must be 4", errors)
    _require(manifest.get("status") == "ready_for_kyle_approval", "status must be ready_for_kyle_approval", errors)

    authorization = manifest.get("pilot_authorization", {})
    _require(authorization.get("kyle_approval_recorded") is False, "pilot approval must remain false before Kyle approves", errors)
    _require(authorization.get("merge_authorized") is False, "merge authorization must remain false", errors)

    source = manifest.get("source_validation", {})
    head_sha = str(source.get("head_commit_sha", ""))
    _require(source.get("pr_number") == 13, "source PR must be #13", errors)
    _require(bool(COMMIT_RE.fullmatch(head_sha)), "head_commit_sha must be a 40-character lowercase hex SHA", errors)
    _require(bool(str(source.get("alpha_validation_run_id", "")).strip()), "alpha_validation_run_id is required", errors)
    _require(source.get("alpha_validation_conclusion") == "success", "Alpha validation conclusion must be success", errors)
    _require(source.get("working_tree_clean_at_build") is True, "build must come from a clean working tree", errors)

    build = manifest.get("build_identity", {})
    build_sha = str(build.get("commit_sha", ""))
    _require(build_sha == head_sha and bool(COMMIT_RE.fullmatch(build_sha)), "built commit must match the validated PR head", errors)
    _require(bool(SHA256_RE.fullmatch(str(build.get("apk_sha256", "")))), "apk_sha256 must be a 64-character lowercase hex digest", errors)
    _require(build.get("android_package") == "com.krk344.nhlgmgame", "Android package identity is invalid", errors)
    _require(build.get("build_type") == "release", "build_type must be release", errors)
    _require(_is_tester_accessible_api_url(build.get("api_base_url")), "api_base_url must identify the exact tester-accessible http(s) backend", errors)
    _require(build.get("endpoint_class") in {"private-lan", "tester-accessible-hosted"}, "endpoint_class must be tester accessible", errors)
    _require(build.get("artifact_verification") == "pass", "artifact verification must pass", errors)
    _require(build.get("installed_package_reconciled") is True, "installed package must reconcile to the verified artifact", errors)
    _require(build.get("launch_confirmation") == "pass", "installed application launch must be confirmed", errors)

    scope = manifest.get("session_scope", {})
    tester_count = scope.get("tester_count")
    _require(isinstance(tester_count, int) and 3 <= tester_count <= 5, "tester_count must be between 3 and 5", errors)
    _require(scope.get("fictional_alpha_disclosure_acknowledged") is True, "fictional Alpha disclosure must be acknowledged", errors)
    _require(scope.get("known_limitations_acknowledged") is True, "known limitations must be acknowledged", errors)

    route = manifest.get("required_route", {})
    for step in REQUIRED_ROUTE:
        _require(route.get(step) == "pass", f"required route step {step} must pass", errors)

    evidence = manifest.get("evidence", {})
    for item in REQUIRED_EVIDENCE:
        _require(evidence.get(item) == "pass", f"evidence item {item} must pass", errors)
    endpoint_minutes = evidence.get("endpoint_qualification_minutes")
    _require(
        isinstance(endpoint_minutes, (int, float))
        and not isinstance(endpoint_minutes, bool)
        and endpoint_minutes >= MIN_ENDPOINT_QUALIFICATION_MINUTES,
        f"endpoint qualification must cover at least {MIN_ENDPOINT_QUALIFICATION_MINUTES} uninterrupted minutes",
        errors,
    )
    _require(bool(str(evidence.get("public_summary_reference", "")).strip()), "public_summary_reference is required", errors)

    defects = manifest.get("defects", {})
    _require(defects.get("open_blockers") == 0, "open Blocker defects must be zero", errors)
    _require(defects.get("open_majors") == 0, "open Major defects must be zero", errors)
    _require(defects.get("go_no_go") == "go-for-kyle-approval", "go/no-go must be go-for-kyle-approval", errors)

    ui = manifest.get("ui_review", {})
    _require(ui.get("stage2_direction_preserved") is True, "approved Stage 2 direction must remain preserved", errors)
    _require(ui.get("implemented_screens_status") == "UI Review Pending", "implemented screens must remain UI Review Pending", errors)
    _require(ui.get("kyle_stage3_or_stage4_approval_recorded") is False, "UI approval must remain false until Kyle explicitly approves", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"manifest_error: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("manifest_error: root value must be an object", file=sys.stderr)
        return 2

    errors = validate_manifest(payload)
    if errors:
        for error in errors:
            print(f"BLOCK: {error}", file=sys.stderr)
        return 1

    print("READY_FOR_KYLE_APPROVAL: exact-package pilot session evidence is complete; pilot and merge remain unauthorized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
