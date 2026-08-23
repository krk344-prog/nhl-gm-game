#!/usr/bin/env python3
"""Run the guarded Technical Alpha device, endpoint, build, install, and launch handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

from prepare_alpha_build import prepare_build_handoff

DEVICE_PREFLIGHT_SCRIPT = "scripts/check_alpha_android_device.py"
BACKEND_PREFLIGHT_SCRIPT = "scripts/check_alpha_backend.py"
INSTALL_SCRIPT = "scripts/install_alpha_apk.py"
LAUNCH_SCRIPT = "scripts/launch_alpha_app.py"
DEVICE_SMOKE_TEMPLATE = "docs/technical_alpha_device_smoke_record.template.json"
DEVICE_SMOKE_VALIDATOR = "scripts/validate_alpha_device_smoke.py"
DEVICE_SMOKE_SUMMARIZER = "scripts/summarize_alpha_device_smoke.py"
STAGE3_CAPTURE_TEMPLATE = "docs/technical_alpha_stage3_capture_record.template.json"
STAGE3_CAPTURE_VALIDATOR = "scripts/validate_alpha_stage3_capture.py"
ARTIFACT_DIRECTORY = "dist/technical-alpha"
APK_CHECKSUM_PATH = f"{ARTIFACT_DIRECTORY}/nhl-gm-technical-alpha.apk.sha256"
PRIVATE_EVIDENCE_DIRECTORY = ".alpha-private"
DEVICE_SMOKE_PRIVATE_FILENAME = "technical-alpha-device-smoke.json"
STAGE3_CAPTURE_PRIVATE_FILENAME = "technical-alpha-stage3-capture.json"
APPLICATION_PACKAGE = "com.krk344.nhlgmgame"
BUILD_TYPE = "standalone-release-apk"


def _read_apk_checksum(path: str) -> str:
    parts = Path(path).read_text(encoding="utf-8").strip().split()
    if len(parts) != 2 or parts[1].lstrip("*") != "nhl-gm-technical-alpha.apk":
        raise RuntimeError("Technical Alpha APK checksum manifest is invalid")
    digest = parts[0].lower()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise RuntimeError("Technical Alpha APK checksum is not a valid SHA-256 digest")
    return digest


def _write_prefilled_record(template_path: str, output_path: str, identity: dict[str, object]) -> str:
    template = json.loads(Path(template_path).read_text(encoding="utf-8"))
    if not isinstance(template, dict):
        raise RuntimeError(f"Technical Alpha evidence template is not a JSON object: {template_path}")

    missing_identity_fields = sorted(key for key in identity if key not in template)
    if missing_identity_fields:
        raise RuntimeError(
            "Technical Alpha evidence template is missing required release identity fields: "
            + ", ".join(missing_identity_fields)
        )

    for key, value in identity.items():
        template[key] = value

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(destination)


def _write_private_evidence_pair(
    private_root: Path,
    identity: dict[str, object],
    evidence_writer: Callable[[str, str, dict[str, object]], str],
) -> tuple[str, str]:
    """Create both private records as one handoff; never leave one canonical record alone."""
    private_root.mkdir(parents=True, exist_ok=True)
    device_path = private_root / DEVICE_SMOKE_PRIVATE_FILENAME
    stage3_path = private_root / STAGE3_CAPTURE_PRIVATE_FILENAME
    device_tmp = private_root / f".{DEVICE_SMOKE_PRIVATE_FILENAME}.tmp"
    stage3_tmp = private_root / f".{STAGE3_CAPTURE_PRIVATE_FILENAME}.tmp"

    try:
        evidence_writer(DEVICE_SMOKE_TEMPLATE, str(device_tmp), identity)
        evidence_writer(STAGE3_CAPTURE_TEMPLATE, str(stage3_tmp), identity)
        device_tmp.replace(device_path)
        stage3_tmp.replace(stage3_path)
    except Exception:
        device_tmp.unlink(missing_ok=True)
        stage3_tmp.unlink(missing_ok=True)
        device_path.unlink(missing_ok=True)
        stage3_path.unlink(missing_ok=True)
        raise

    return str(device_path), str(stage3_path)


def run_release_handoff(
    *,
    api_base_url: str | None = None,
    season_id: str = "2026-27",
    timeout: float = 5.0,
    serial: str | None = None,
    evidence_directory: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    record_exists: Callable[[str], bool] = lambda path: Path(path).is_file(),
    artifact_exists: Callable[[str], bool] = lambda path: Path(path).is_dir(),
    checksum_reader: Callable[[str], str] = _read_apk_checksum,
    evidence_writer: Callable[[str, str, dict[str, object]], str] = _write_prefilled_record,
    check_output: Callable[..., str] = subprocess.check_output,
) -> dict[str, object]:
    """Preflight one device, then qualify, build, install, launch, and recheck the backend."""

    commit = check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if not commit:
        raise RuntimeError("could not determine the exact PR #13 commit for release handoff")

    device_argv = [sys.executable, DEVICE_PREFLIGHT_SCRIPT]
    if serial:
        device_argv.extend(["--serial", serial])

    device_result = runner(device_argv, check=False)
    if device_result.returncode != 0:
        raise RuntimeError(f"device_preflight failed with exit code {device_result.returncode}")

    handoff = prepare_build_handoff(
        api_base_url=api_base_url,
        season_id=season_id,
        timeout=timeout,
    )

    install_argv = [
        sys.executable,
        INSTALL_SCRIPT,
        ARTIFACT_DIRECTORY,
        "--expected-commit",
        commit,
        "--expected-api-base-url",
        str(handoff["api_base_url"]),
    ]
    launch_argv = [sys.executable, LAUNCH_SCRIPT]
    if serial:
        install_argv.extend(["--serial", serial])
        launch_argv.extend(["--serial", serial])

    backend_recheck_argv = [
        sys.executable,
        BACKEND_PREFLIGHT_SCRIPT,
        str(handoff["api_base_url"]),
        "--season-id",
        str(handoff["season_id"]),
        "--timeout",
        str(timeout),
    ]

    phases: Sequence[tuple[str, Sequence[str]]] = (
        ("qualification", handoff["qualification_argv"]),
        ("build", handoff["build_argv"]),
        ("install", install_argv),
        ("launch", launch_argv),
        ("backend_recheck", backend_recheck_argv),
    )
    completed: list[str] = ["device_preflight"]

    for phase, phase_argv in phases:
        if phase == "build" and not record_exists(str(handoff["qualification_record"])):
            raise RuntimeError("Endpoint qualification completed without producing the required qualification record")
        if phase == "install" and not artifact_exists(ARTIFACT_DIRECTORY):
            raise RuntimeError("Release build completed without producing the required Technical Alpha artifact directory")

        result = runner(phase_argv, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"{phase} failed with exit code {result.returncode}")
        completed.append(phase)

    apk_sha256 = checksum_reader(APK_CHECKSUM_PATH)
    candidate_identity: dict[str, object] = {
        "commit_sha": commit,
        "api_base_url": handoff["api_base_url"],
        "application_package": APPLICATION_PACKAGE,
        "build_type": BUILD_TYPE,
        "apk_sha256": apk_sha256,
    }

    device_smoke_private_record = None
    stage3_capture_private_record = None
    if evidence_directory:
        device_smoke_private_record, stage3_capture_private_record = _write_private_evidence_pair(
            Path(evidence_directory), candidate_identity, evidence_writer
        )

    return {
        "ready": True,
        "api_base_url": handoff["api_base_url"],
        "season_id": handoff["season_id"],
        "commit": commit,
        "qualification_record": handoff["qualification_record"],
        "artifact_directory": ARTIFACT_DIRECTORY,
        "apk_sha256": apk_sha256,
        "completed_phases": completed,
        "device_smoke_template": DEVICE_SMOKE_TEMPLATE,
        "device_smoke_prefill": candidate_identity,
        "device_smoke_private_record": device_smoke_private_record,
        "device_smoke_validation_command": f"python {DEVICE_SMOKE_VALIDATOR} <PRIVATE_DEVICE_SMOKE_RECORD.json>",
        "device_smoke_summary_command": f"python {DEVICE_SMOKE_SUMMARIZER} <PRIVATE_DEVICE_SMOKE_RECORD.json>",
        "stage3_capture_template": STAGE3_CAPTURE_TEMPLATE,
        "stage3_capture_prefill": candidate_identity,
        "stage3_capture_private_record": stage3_capture_private_record,
        "stage3_capture_validation_command": f"python {STAGE3_CAPTURE_VALIDATOR} <PRIVATE_STAGE3_CAPTURE_RECORD.json>",
        "next_action": "Complete the prefilled private device-smoke record on this same device, validate it, generate the privacy-safe summary, then complete the prefilled Stage 3 capture record with the remaining capture evidence and validate it before final readiness review.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url")
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--serial", help="adb serial to select when multiple authorized Android devices are connected")
    parser.add_argument(
        "--evidence-directory",
        default=PRIVATE_EVIDENCE_DIRECTORY,
        help="private local directory for prefilled device-smoke and Stage 3 evidence records",
    )
    args = parser.parse_args(argv)

    try:
        payload = run_release_handoff(
            api_base_url=args.api_base_url,
            season_id=args.season_id,
            timeout=args.timeout,
            serial=args.serial,
            evidence_directory=args.evidence_directory,
        )
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
