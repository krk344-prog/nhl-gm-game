#!/usr/bin/env python3
"""Build and package a configured Technical Alpha APK from PR #13 locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.parse import urlsplit

PR_BRANCH = "agent/alpha-rules-integration-v1"
ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"
OUTPUT = ROOT / "dist" / "technical-alpha"


def validate_api_base_url(value: str) -> str:
    value = value.rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("api_base_url must be an http(s) URL")
    if parsed.query or parsed.fragment or not parsed.path.endswith("/api/v1"):
        raise ValueError("api_base_url must end with /api/v1 and contain no query or fragment")
    host = parsed.hostname.lower()
    if host == "localhost" or host == "0.0.0.0" or host == "::1" or host.startswith("127."):
        raise ValueError("tester APK requires a non-loopback endpoint")
    return value


def command_plan(api_base_url: str) -> list[list[str]]:
    gradle = "gradlew.bat" if os.name == "nt" else "./gradlew"
    return [
        ["npm", "ci"],
        ["npx", "expo", "export", "--platform", "android", "--output-dir", str(OUTPUT / "android-export")],
        ["npx", "expo", "prebuild", "--platform", "android", "--non-interactive", "--no-install"],
        [gradle, "assembleDebug", "--no-daemon"],
    ]


def _run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(api_base_url: str) -> dict[str, str]:
    api_base_url = validate_api_base_url(api_base_url)
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip()
    if branch != PR_BRANCH:
        raise RuntimeError(f"build must run from {PR_BRANCH}; current branch is {branch or 'detached'}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    env = os.environ.copy()
    env["EXPO_NO_TELEMETRY"] = "1"
    env["EXPO_PUBLIC_API_URL"] = api_base_url
    plan = command_plan(api_base_url)
    _run(plan[0], MOBILE, env)
    _run(plan[1], MOBILE, env)
    _run(plan[2], MOBILE, env)
    _run(plan[3], MOBILE / "android", env)

    source_apk = MOBILE / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    apk = OUTPUT / "nhl-gm-technical-alpha.apk"
    shutil.copy2(source_apk, apk)
    export_archive = OUTPUT / "nhl-gm-android-export.tar.gz"
    with tarfile.open(export_archive, "w:gz") as archive:
        archive.add(OUTPUT / "android-export", arcname="nhl-gm-android")

    apk_digest = _sha256(apk)
    export_digest = _sha256(export_archive)
    (OUTPUT / "nhl-gm-technical-alpha.apk.sha256").write_text(
        f"{apk_digest}  {apk.name}\n", encoding="utf-8"
    )
    (OUTPUT / "nhl-gm-android-export.sha256").write_text(
        f"{export_digest}  {export_archive.name}\n", encoding="utf-8"
    )
    (OUTPUT / "technical-alpha-build.txt").write_text(
        f"commit={commit}\napi_base_url={api_base_url}\nbuild_type=debug-apk\n",
        encoding="utf-8",
    )
    return {"status": "pass", "output_dir": str(OUTPUT), "commit": commit, "api_base_url": api_base_url}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        endpoint = validate_api_base_url(args.api_base_url)
        if not args.execute:
            print(json.dumps({"status": "ready", "api_base_url": endpoint, "commands": command_plan(endpoint)}, indent=2))
            return 0
        print(json.dumps(build(endpoint), indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "block", "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
