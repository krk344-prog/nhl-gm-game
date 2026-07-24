#!/usr/bin/env python3
"""Verify a downloaded Technical Alpha artifact before installation.

This tool is intentionally dependency-free so a facilitator can run it from a
clean Python environment after downloading and extracting the GitHub Actions
artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_ARTIFACTS = {
    "nhl-gm-technical-alpha.apk": "nhl-gm-technical-alpha.apk.sha256",
    "nhl-gm-android-export.tar.gz": "nhl-gm-android-export.sha256",
}
BUILD_MANIFEST = "technical-alpha-build.txt"


class VerificationError(ValueError):
    """Raised when an artifact cannot be approved for installation."""


def _validate_non_loopback_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise VerificationError("expected API URL must be an absolute http(s) URL")
    if not parsed.path.rstrip("/").endswith("/api/v1"):
        raise VerificationError("expected API URL must include the /api/v1 base path")

    hostname = parsed.hostname.lower()
    if hostname == "localhost":
        raise VerificationError("loopback API endpoints are not valid for tester APKs")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and (address.is_loopback or address.is_unspecified):
        raise VerificationError("loopback or unspecified API endpoints are not valid for tester APKs")
    return value.rstrip("/")


def _read_build_manifest(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "=" not in line:
            raise VerificationError(f"invalid build manifest line: {line!r}")
        key, value = line.split("=", 1)
        if key in values:
            raise VerificationError(f"duplicate build manifest key: {key}")
        values[key] = value
    required = {"commit", "api_base_url", "build_type"}
    if set(values) != required:
        raise VerificationError(
            f"build manifest keys must be exactly {sorted(required)}; found {sorted(values)}"
        )
    return values


def _verify_checksum(directory: Path, artifact_name: str, checksum_name: str) -> str:
    artifact = directory / artifact_name
    checksum_file = directory / checksum_name
    if not artifact.is_file():
        raise VerificationError(f"missing artifact: {artifact_name}")
    if not checksum_file.is_file():
        raise VerificationError(f"missing checksum file: {checksum_name}")

    parts = checksum_file.read_text(encoding="utf-8").strip().split()
    if len(parts) != 2:
        raise VerificationError(f"invalid checksum manifest: {checksum_name}")
    expected_hash, recorded_name = parts
    recorded_name = recorded_name.lstrip("*")
    if Path(recorded_name).name != recorded_name or recorded_name != artifact_name:
        raise VerificationError(
            f"checksum manifest must reference portable filename {artifact_name!r}"
        )

    actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if actual_hash.lower() != expected_hash.lower():
        raise VerificationError(f"checksum mismatch for {artifact_name}")
    return actual_hash


def verify_artifact(directory: Path, expected_commit: str, expected_api_base_url: str) -> dict[str, object]:
    directory = directory.resolve()
    if not directory.is_dir():
        raise VerificationError(f"artifact directory does not exist: {directory}")

    expected_api_base_url = _validate_non_loopback_url(expected_api_base_url)
    manifest_path = directory / BUILD_MANIFEST
    if not manifest_path.is_file():
        raise VerificationError(f"missing build manifest: {BUILD_MANIFEST}")
    manifest = _read_build_manifest(manifest_path)

    if manifest["commit"] != expected_commit:
        raise VerificationError(
            f"build commit {manifest['commit']!r} does not match expected commit {expected_commit!r}"
        )
    embedded_url = _validate_non_loopback_url(manifest["api_base_url"])
    if embedded_url != expected_api_base_url:
        raise VerificationError(
            f"build API URL {embedded_url!r} does not match expected URL {expected_api_base_url!r}"
        )
    if manifest["build_type"] != "debug-apk":
        raise VerificationError(f"unsupported build type: {manifest['build_type']!r}")

    checksums = {
        artifact: _verify_checksum(directory, artifact, checksum)
        for artifact, checksum in REQUIRED_ARTIFACTS.items()
    }
    return {
        "status": "pass",
        "commit": expected_commit,
        "api_base_url": expected_api_base_url,
        "build_type": manifest["build_type"],
        "checksums": checksums,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_directory", type=Path)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-api-base-url", required=True)
    args = parser.parse_args()

    try:
        result = verify_artifact(
            args.artifact_directory,
            args.expected_commit,
            args.expected_api_base_url,
        )
    except (OSError, VerificationError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
