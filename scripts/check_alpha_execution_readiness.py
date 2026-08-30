#!/usr/bin/env python3
"""Check whether the facilitator can start the guarded Technical Alpha release handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Callable

from build_alpha_apk_local import PR_BRANCH, ROOT, validate_repository_state
from prepare_alpha_build import prepare_build_handoff

DEVICE_PREFLIGHT_SCRIPT = "scripts/check_alpha_android_device.py"
RELEASE_HANDOFF_SCRIPT = "scripts/run_alpha_release_handoff.py"


class ExecutionReadinessError(RuntimeError):
    """A privacy-safe blocker with an explicit execution stage for automation triage."""

    def __init__(self, blocker_scope: str, message: str) -> None:
        super().__init__(message)
        self.blocker_scope = blocker_scope


def validate_source_readiness() -> str:
    """Fail early unless the facilitator checkout can produce an identity-safe PR #13 build."""
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip()
        porcelain_status = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=ROOT, text=True
        )
        return validate_repository_state(branch, porcelain_status)
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        raise ExecutionReadinessError("source", f"source_preflight blocked: {exc}") from exc


def read_source_commit() -> str:
    """Return the exact clean PR #13 commit being certified by the readiness check."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ExecutionReadinessError("source", f"source_preflight blocked: {exc}") from exc
    if len(commit) != 40 or any(character not in "0123456789abcdefABCDEF" for character in commit):
        raise ExecutionReadinessError("source", "source_preflight blocked: could not determine exact Git commit")
    return commit.lower()


def check_execution_readiness(
    *,
    api_base_url: str | None = None,
    season_id: str = "2026-27",
    timeout: float = 5.0,
    serial: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict[str, object]:
    """Validate source + device + endpoint prerequisites without qualifying, building, installing, or launching."""

    validate_source_readiness()
    source_commit = read_source_commit()

    device_argv = [sys.executable, DEVICE_PREFLIGHT_SCRIPT]
    if serial:
        device_argv.extend(["--serial", serial])

    device_result = runner(
        device_argv,
        check=False,
        capture_output=True,
        text=True,
    )
    if device_result.returncode != 0:
        detail = (device_result.stdout or device_result.stderr or "").strip()
        try:
            payload = json.loads(detail) if detail else {}
        except json.JSONDecodeError:
            payload = {}
        reason = payload.get("error") if isinstance(payload, dict) else None
        if reason:
            raise ExecutionReadinessError("device", f"device_preflight blocked: {reason}")
        raise ExecutionReadinessError(
            "device", f"device_preflight failed with exit code {device_result.returncode}"
        )

    try:
        handoff = prepare_build_handoff(
            api_base_url=api_base_url,
            season_id=season_id,
            timeout=timeout,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        raise ExecutionReadinessError("endpoint", f"endpoint_preflight blocked: {exc}") from exc

    release_argv = [
        sys.executable,
        RELEASE_HANDOFF_SCRIPT,
        "--api-base-url",
        str(handoff["api_base_url"]),
        "--season-id",
        str(handoff["season_id"]),
        "--timeout",
        str(timeout),
    ]
    if serial:
        release_argv.extend(["--serial", serial])

    return {
        "ready": True,
        "source_ready": True,
        "source_branch": PR_BRANCH,
        "source_commit": source_commit,
        "device_ready": True,
        "endpoint_ready": True,
        "api_base_url": handoff["api_base_url"],
        "season_id": handoff["season_id"],
        "endpoint_source": handoff["endpoint_source"],
        "next_command_argv": release_argv,
        "next_action": "Run next_command_argv from this same clean source commit to execute qualification, exact release build, verified install, launch, backend recheck, and evidence prefill on this same device; rerun readiness if the source commit changes.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base-url")
    parser.add_argument("--season-id", default="2026-27")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--serial", help="adb serial to select when multiple authorized Android devices are connected")
    args = parser.parse_args(argv)

    try:
        payload = check_execution_readiness(
            api_base_url=args.api_base_url,
            season_id=args.season_id,
            timeout=args.timeout,
            serial=args.serial,
        )
    except ExecutionReadinessError as exc:
        print(
            json.dumps(
                {
                    "ready": False,
                    "blocker_scope": exc.blocker_scope,
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ready": False, "blocker_scope": "unknown", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
