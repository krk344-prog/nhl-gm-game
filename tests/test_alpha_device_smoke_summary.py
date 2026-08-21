from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_alpha_device_smoke.py"


def valid_record() -> dict[str, object]:
    return {
        "commit_sha": "a" * 40,
        "api_base_url": "http://192.168.1.77:8000/api/v1",
        "application_package": "com.krk344.nhlgmgame",
        "build_type": "standalone-release-apk",
        "device_model": "PRIVATE DEVICE MODEL",
        "android_version": "PRIVATE ANDROID VERSION",
        "apk_sha256": "b" * 64,
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "artifact_verifier_passed": True,
        "apk_installed": True,
        "launch_confirmed": True,
        "health_passed": True,
        "season_context_passed": True,
        "franchise_selection_passed": True,
        "advance_day_passed": True,
        "roster_passed": True,
        "standings_passed": True,
        "trade_passed": True,
        "save_reload_passed": True,
        "debug_report_passed": True,
        "reset_passed": True,
        "blockers": [],
    }


class AlphaDeviceSmokeSummaryTests(unittest.TestCase):
    def run_summary(self, record: dict[str, object]) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "private-smoke.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        return result, json.loads(result.stdout)

    def test_passing_summary_omits_private_values(self) -> None:
        record = valid_record()
        result, summary = self.run_summary(record)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["commit"], "a" * 12)
        self.assertEqual(summary["application_package"], "com.krk344.nhlgmgame")
        self.assertEqual(summary["checks_passed"], 13)
        self.assertEqual(summary["checks_required"], 13)
        self.assertEqual(summary["endpoint_class"], "private-or-controlled-http")

        serialized = json.dumps(summary)
        self.assertNotIn("192.168.1.77", serialized)
        self.assertNotIn("PRIVATE DEVICE MODEL", serialized)
        self.assertNotIn("PRIVATE ANDROID VERSION", serialized)
        self.assertNotIn("b" * 64, serialized)

    def test_failed_record_remains_blocked_without_exposing_endpoint(self) -> None:
        record = valid_record()
        record["save_reload_passed"] = False
        record["blockers"] = ["Private facilitator note"]

        result, summary = self.run_summary(record)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(summary["status"], "block")
        self.assertIn("not_passed:save_reload_passed", summary["error_codes"])
        self.assertIn("blockers_present", summary["error_codes"])
        self.assertNotIn("Private facilitator note", json.dumps(summary))
        self.assertNotIn("192.168.1.77", json.dumps(summary))


if __name__ == "__main__":
    unittest.main()
