import threading
import unittest

from scripts.qualify_alpha_endpoint import qualify_endpoint
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

        result = qualify_endpoint(
            self.base_url,
            duration_seconds=60,
            interval_seconds=30,
            allow_loopback=True,
            clock=fake_time.monotonic,
            sleeper=fake_time.sleep,
        )

        self.assertTrue(result.ready)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(result.passed_attempts, 3)
        self.assertEqual(result.duration_seconds, 60)
        self.assertEqual(result.season_id, "2026-27")

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


if __name__ == "__main__":
    unittest.main()
