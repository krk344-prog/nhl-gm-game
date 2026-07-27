#!/usr/bin/env python3
"""Build and package a configured Technical Alpha APK from PR #13 locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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


def _major_version(output: str) -> int | None:
    match = re.search(r"(?:version\s+\")?v?(\d+)(?:[.\"]|$)", output)
    return int(match.group(1)) if match else None


def _sdk_candidates(env: dict[str, str]) -> list[Path]:
    candidates: list[Path] = []
    for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if env.get(name):
            candidates.append(Path(env[name]).expanduser())
    if env.get("LOCALAPPDATA"):
        candidates.append(Path(env["LOCALAPPDATA"]) / "Android" / "Sdk")
    home = Path.home()
    candidates.extend((home / "Android" / "Sdk", home / "Library" / "Android" / "sdk"))
    return candidates


def inspect_build_environment(
    *,
    env: dict[str, str] | None = None,
    which=shutil.which,
    check_output=subprocess.check_output,
) -> dict[str, object]:
    env = dict(os.environ if env is None else env)
    tools = {name: which(name) for name in ("node", "npm", "npx", "java")}
    node_output = check_output(["node", "--version"], text=True).strip() if tools["node"] else ""
    java_output = (
        check_output(["java", "-version"], text=True, stderr=subprocess.STDOUT).strip()
        if tools["java"]
        else ""
    )
    sdk_path = next((path for path in _sdk_candidates(env) if path.is_dir()), None)
    return {
        "tools": tools,
        "node_major": _major_version(node_output),
        "java_major": _major_version(java_output),
        "android_sdk": str(sdk_path) if sdk_path else None,
    }


def validate_build_environment(report: dict[str, object]) -> dict[str, object]:
    tools = report.get("tools") or {}
    missing = [name for name in ("node", "npm", "npx", "java") if not tools.get(name)]
    errors: list[str] = []
    if missing:
        errors.append(f"missing required tools: {', '.join(missing)}")
    if report.get("node_major") != 20:
        errors.append(f"Node.js 20 is required; found {report.get('node_major') or 'unknown'}")
    if report.get("java_major") != 17:
        errors.append(f"Java 17 is required; found {report.get('java_major') or 'unknown'}")
    if not report.get("android_sdk"):
        errors.append("Android SDK was not found via ANDROID_HOME, ANDROID_SDK_ROOT, or a standard install path")
    if errors:
        raise RuntimeError("; ".join(errors))
    return report


def validate_repository_state(branch: str, porcelain_status: str) -> str:
    if branch != PR_BRANCH:
        raise RuntimeError(f"build must run from {PR_BRANCH}; current branch is {branch or 'detached'}")
    if porcelain_status.strip():
        raise RuntimeError(
            "configured APK build requires a clean working tree so the recorded commit exactly identifies the package"
        )
    return branch


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
    validate_build_environment(inspect_build_environment())
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip()
    porcelain_status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True
    )
    validate_repository_state(branch, porcelain_status)
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
    parser.add_argument("--check-environment", action="store_true")
    args = parser.parse_args(argv)
    try:
        endpoint = validate_api_base_url(args.api_base_url)
        environment = None
        if args.check_environment or args.execute:
            environment = validate_build_environment(inspect_build_environment())
        if not args.execute:
            print(json.dumps({"status": "ready", "api_base_url": endpoint, "environment": environment, "commands": command_plan(endpoint)}, indent=2))
            return 0
        print(json.dumps(build(endpoint), indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "block", "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
