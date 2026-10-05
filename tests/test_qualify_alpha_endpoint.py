import json
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.qualify_alpha_endpoint import qualify_endpoint, write_qualification_record
from src.season_context_api import create_season_context_server


class FakeTime:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class AlphaEndpointQualificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_season_context_server()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}/api/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_qualification_rechecks_backend_for_full_window(self):
        fake_time = FakeTime()
        qualified_at = datetime(2026, 8, 15, 16, 30, tzinfo=timezone.utc)

        result = qualify_endpoint(
            self.base_url + "/",
            duration_seconds=60,
            interval_seconds=30,
            allow_loopback=True,
            clock=fake_time.monotonic,
            sleeper=fake_time.sleep,
            utc_now=lambda: qualified_at,
        )

        self.assertTrue(result.ready)
        self.assertEqual(result.api_base_url, self.base_url)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(result.passed_attempts, 3)
        self.assertEqual(result.duration_seconds, 60)
        self.assertEqual(result.season_id, "2026-27")
        self.assertEqual(result.qualified_at_utc, "2026-08-15T16:30:00Z")

    def test_successful_qualification_can_be_persisted_as_exact_json_evidence(self):
        fake_time = FakeTime()
        result = qualify_endpoint(
            self.base_url,
            duration_seconds=0,
            allow_loopback=True,
            clock=fake_time.monotonic,
            sleeper=fake_time.sleep,
            utc_now=lambda: datetime(2026, 8, 15, 17, 0, tzinfo=timezone.utc),
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence" / "qualification.json"
            written = write_qualification_record(result, output)
            payload = json.loads(written.read_text(encoding="utf-8"))

        self.assertEqual(written, output)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["api_base_url"], self.base_url)
        self.assertEqual(payload["season_id"], "2026-27")
        self.assertEqual(payload["qualified_at_utc"], "2026-08-15T17:00:00Z")

    def test_invalid_timing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            qualify_endpoint(self.base_url, duration_seconds=-1, allow_loopback=True)

        with self.assertRaisesRegex(ValueError, "positive"):
            qualify_endpoint(
                self.base_url,
                duration_seconds=0,
                interval_seconds=0,
                allow_loopback=True,
            )

    def test_naive_qualification_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            qualify_endpoint(
                self.base_url,
                duration_seconds=0,
                allow_loopback=True,
                utc_now=lambda: datetime(2026, 8, 15, 16, 30),
            )


if __name__ == "__main__":
    unittest.main()
