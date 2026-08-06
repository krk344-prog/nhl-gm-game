#!/usr/bin/env python3
"""Create one verified, privacy-safe ZIP for an Android Technical Alpha tester."""

from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile

from scripts.verify_alpha_artifact import VerificationError, verify_artifact

APK_NAME = "nhl-gm-technical-alpha.apk"
APK_CHECKSUM_NAME = "nhl-gm-technical-alpha.apk.sha256"
BUILD_MANIFEST_NAME = "technical-alpha-build.txt"
BUNDLE_ROOT = "NHL-GM-First-Playable"


class BundleError(ValueError):
    """Raised when a tester handoff bundle cannot be created safely."""


def _read_manifest(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "=" not in line:
            raise BundleError(f"invalid build manifest line: {line!r}")
        key, value = line.split("=", 1)
        if key in values:
            raise BundleError(f"duplicate build manifest key: {key}")
        values[key] = value
    required = {"commit", "api_base_url", "build_type"}
    if set(values) != required:
        raise BundleError("build manifest is incomplete or contains unexpected fields")
    return values


def _endpoint_class(api_base_url: str) -> str:
    parsed = urlparse(api_base_url)
    hostname = parsed.hostname or ""
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and address.is_private:
        return "private-lan"
    if parsed.scheme == "https":
        return "https-hosted"
    return "network-host"


def _start_here(commit: str) -> str:
    return f"""NHL GM — FIRST PLAYABLE TEST

BUILD: {commit[:12]}
STATUS: UI REVIEW PENDING

WHAT THIS IS
This is an early test version with eight fictional franchises and an 82-game test schedule. It is not an official NHL roster or schedule product.

BEFORE YOU START
1. Stay on the network provided by the test organizer.
2. Install nhl-gm-technical-alpha.apk. Android may ask you to allow installation from this source.
3. Open NHL GM and tell the organizer if the game shows an offline message.
4. Do not share this package, network details, screenshots, or save files publicly.

TEST ROUTE
1. Start a new game.
2. Select a franchise.
3. Advance the day.
4. Open the roster.
5. Open the standings.
6. Attempt one trade.
7. Close and reopen the game to confirm your progress remains.
8. Reset the game and confirm it returns to Day 1.

REPORTING A PROBLEM
Use BUG-REPORT.txt. Record what you were doing, what you expected, what happened, and whether it happens again. Do not include your name, device serial number, network address, save file, or password.
"""


def _bug_report(commit: str) -> str:
    return f"""NHL GM FIRST PLAYABLE — BUG REPORT

Anonymous tester code:
Build: {commit[:12]}
Phone model and Android version:
Screen or step:
What I was trying to do:
What I expected:
What happened instead:
Can I repeat it? Yes / No / Unsure
Did the game close or freeze?
Did progress disappear after reopening?
Screenshot available? Yes / No
Extra notes (do not include private network or device information):
"""


def _build_info(commit: str, build_type: str, endpoint_class: str) -> str:
    return (
        f"commit={commit}\n"
        f"build_type={build_type}\n"
        f"endpoint_class={endpoint_class}\n"
        "ui_status=UI Review Pending\n"
        "package=com.krk344.nhlgmgame\n"
    )


def create_tester_bundle(
    artifact_directory: Path,
    output_zip: Path,
    *,
    expected_commit: str | None = None,
    expected_api_base_url: str | None = None,
) -> dict[str, object]:
    artifact_directory = artifact_directory.resolve()
    manifest_path = artifact_directory / BUILD_MANIFEST_NAME
    if not manifest_path.is_file():
        raise BundleError(f"missing build manifest: {BUILD_MANIFEST_NAME}")

    manifest = _read_manifest(manifest_path)
    commit = expected_commit or manifest["commit"]
    api_base_url = expected_api_base_url or manifest["api_base_url"]
    verification = verify_artifact(artifact_directory, commit, api_base_url)

    output_zip = output_zip.resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.is_dir():
        raise BundleError(f"output path is a directory: {output_zip}")

    required_files = (APK_NAME, APK_CHECKSUM_NAME)
    for name in required_files:
        if not (artifact_directory / name).is_file():
            raise BundleError(f"missing tester bundle file: {name}")

    with NamedTemporaryFile(
        prefix=f".{output_zip.name}.", suffix=".tmp", dir=output_zip.parent, delete=False
    ) as temporary:
        temp_path = Path(temporary.name)

    endpoint_class = _endpoint_class(api_base_url)
    try:
        with ZipFile(temp_path, "w", compression=ZIP_DEFLATED) as archive:
            for name in required_files:
                archive.write(artifact_directory / name, f"{BUNDLE_ROOT}/{name}")
            archive.writestr(f"{BUNDLE_ROOT}/START-HERE.txt", _start_here(commit))
            archive.writestr(f"{BUNDLE_ROOT}/BUG-REPORT.txt", _bug_report(commit))
            archive.writestr(
                f"{BUNDLE_ROOT}/BUILD-INFO.txt",
                _build_info(commit, str(verification["build_type"]), endpoint_class),
            )
        temp_path.replace(output_zip)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    files = [
        f"{BUNDLE_ROOT}/{APK_NAME}",
        f"{BUNDLE_ROOT}/{APK_CHECKSUM_NAME}",
        f"{BUNDLE_ROOT}/START-HERE.txt",
        f"{BUNDLE_ROOT}/BUG-REPORT.txt",
        f"{BUNDLE_ROOT}/BUILD-INFO.txt",
    ]
    return {
        "status": "pass",
        "output_zip": str(output_zip),
        "commit": commit,
        "build_type": verification["build_type"],
        "endpoint_class": endpoint_class,
        "apk_sha256": verification["checksums"][APK_NAME],
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_directory", type=Path)
    parser.add_argument("output_zip", type=Path)
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-api-base-url")
    args = parser.parse_args()

    try:
        result = create_tester_bundle(
            args.artifact_directory,
            args.output_zip,
            expected_commit=args.expected_commit,
            expected_api_base_url=args.expected_api_base_url,
        )
    except (BundleError, OSError, VerificationError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
