#!/usr/bin/env python3
"""Validate approval-stage SVG UI artifacts using only the Python standard library."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"
REQUIRED_TEXT = {
    "main-dashboard-stage2-desktop.svg": (
        "Needs Your Attention",
        "MANDATORY",
        "OFFLINE MODE",
        "Advance Day",
    ),
    "main-dashboard-stage2-mobile.svg": (
        "Needs Your Attention",
        "MANDATORY",
        "OFFLINE",
        "Advance Day",
    ),
}


def validate_svg(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [f"{path}: cannot parse SVG: {exc}"]

    if root.tag != f"{SVG_NS}svg":
        errors.append(f"{path}: root element is not SVG")
    if root.get("role") != "img":
        errors.append(f"{path}: role must be 'img'")
    if root.get("aria-labelledby") != "title desc":
        errors.append(f"{path}: aria-labelledby must reference 'title desc'")
    if not root.get("viewBox"):
        errors.append(f"{path}: viewBox is required for responsive scaling")

    title = root.find(f"{SVG_NS}title")
    desc = root.find(f"{SVG_NS}desc")
    if title is None or title.get("id") != "title" or not (title.text or "").strip():
        errors.append(f"{path}: accessible title is missing or invalid")
    if desc is None or desc.get("id") != "desc" or not (desc.text or "").strip():
        errors.append(f"{path}: accessible description is missing or invalid")

    visible_text = " ".join((node.text or "").strip() for node in root.iter(f"{SVG_NS}text"))
    for marker in REQUIRED_TEXT.get(path.name, ()):
        if marker not in visible_text:
            errors.append(f"{path}: required state label missing: {marker!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("docs/ui") / name for name in REQUIRED_TEXT],
    )
    args = parser.parse_args()

    errors = [error for path in args.paths for error in validate_svg(path)]
    if errors:
        print("UI artifact validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(args.paths)} UI artifact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
