import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.build_alpha_apk_local import validate_qualification_record


class AlphaBuildQualificationGuardTests(unittest.TestCase):
    ENDPOINT = "http://192.168.1.25:8000/api/v1"
    NOW = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)

    def _record(self, **overrides):
        payload = {
            "api_base_url": self.ENDPOINT,
            "endpoint_class": "tester-reachable",
            "duration_seconds": 900.0,
            "interval_seconds": 30.0,
            "attempts": 31,
            "passed_attempts": 31,
            "season_id": "2026-27",
            "qualified_at_utc": (self.NOW - timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            "ready": True,
        }
        payload.update(overrides)
        return payload

    def _write(self, directory, payload):
        path = Path(directory) / "qualification.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_fresh_matching_qualification_allows_build_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._record())
            result = validate_qualification_record(path, self.ENDPOINT, now=self.NOW)
        self.assertTrue(result["ready"])
        self.assertEqual(result["api_base_url"], self.ENDPOINT)

    def test_different_endpoint_blocks_build_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(
                directory,
                self._record(api_base_url="http://192.168.1.99:8000/api/v1"),
            )
            with self.assertRaisesRegex(RuntimeError, "does not match"):
                validate_qualification_record(path, self.ENDPOINT, now=self.NOW)

    def test_stale_qualification_blocks_build_handoff(self):
        stale = self.NOW - timedelta(minutes=31)
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(
                directory,
                self._record(qualified_at_utc=stale.isoformat().replace("+00:00", "Z")),
            )
            with self.assertRaisesRegex(RuntimeError, "stale"):
                validate_qualification_record(path, self.ENDPOINT, now=self.NOW)


if __name__ == "__main__":
    unittest.main()
