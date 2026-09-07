#!/usr/bin/env python3
"""Fail closed unless a tester launch card is complete and explicitly READY."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


class LaunchCardError(ValueError):
    """Raised when a tester launch card is not safe to use."""


_FIELD_PATTERNS = {
    "backend": re.compile(r"^Backend:\s*(.+)$", re.MULTILINE),
    "verified_at": re.compile(r"^Verified at:\s*(.+)$", re.MULTILINE),
    "tester_id": re.compile(r"^Anonymous tester ID:\s*(.+)$", re.MULTILINE),
    "bug_destination": re.compile(r"^Private bug-report destination:\s*(.+)$", re.MULTILINE),
    "known_limitation": re.compile(r"^Most important known limitation:\s*(.+)$", re.MULTILINE),
}
_PLACEHOLDER_MARKERS = ("[", "]", "PRIVATE DESTINATION", "ONE SENTENCE", "DATE/TIME")
_MAX_CLOCK_SKEW = timedelta(minutes=5)
_MAX_VERIFICATION_AGE = timedelta(minutes=30)


def _field(text: str, name: str) -> str:
    matches = _FIELD_PATTERNS[name].findall(text)
    if not matches:
        raise LaunchCardError(f"missing launch-card field: {name}")
    if len(matches) != 1:
        raise LaunchCardError(f"launch-card field must appear exactly once: {name}")
    value = matches[0].strip()
    if not value or any(marker in value for marker in _PLACEHOLDER_MARKERS):
        raise LaunchCardError(f"launch-card field is incomplete: {name}")
    return value


def validate_launch_card(path: Path, *, now: datetime | None = None) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    backend = _field(text, "backend").upper()
    if backend != "READY":
        raise LaunchCardError("backend must be explicitly READY before testing starts")

    verified_at = _field(text, "verified_at")
    try:
        verified_datetime = datetime.fromisoformat(verified_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LaunchCardError("Verified at must be an ISO-8601 date/time") from exc
    if verified_datetime.tzinfo is None or verified_datetime.utcoffset() is None:
        raise LaunchCardError("Verified at must include a timezone offset or Z")

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise LaunchCardError("validation time must include a timezone offset")
    current_utc = current_time.astimezone(timezone.utc)
    verified_utc = verified_datetime.astimezone(timezone.utc)
    if verified_utc > current_utc + _MAX_CLOCK_SKEW:
        raise LaunchCardError("Verified at must not be future-dated beyond the allowed clock skew")
    if current_utc - verified_utc > _MAX_VERIFICATION_AGE:
        raise LaunchCardError("Verified at is stale; re-check the backend before testing starts")

    tester_id = _field(text, "tester_id")
    if re.fullmatch(r"T\d{2}", tester_id) is None:
        raise LaunchCardError("Anonymous tester ID must use the T## format")

    _field(text, "bug_destination")
    _field(text, "known_limitation")

    return {
        "status": "pass",
        "backend": "READY",
        "tester_id": tester_id,
        "verified_at": verified_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("launch_card", type=Path)
    args = parser.parse_args()
    try:
        result = validate_launch_card(args.launch_card)
    except (LaunchCardError, OSError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
