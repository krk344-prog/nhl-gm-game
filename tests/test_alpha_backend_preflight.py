import threading
import unittest
from unittest.mock import patch

from scripts.check_alpha_backend import (
    PreflightResult,
    _normalized_base_url,
    run_preflight,
    run_stability_preflight,
)
from src.season_context_api import create_season_context_server


class AlphaBackendPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_season_context_server()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address
        cls.base_url = f"http://{cls.host}:{cls.port}/api/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_preflight_validates_health_and_season_context(self):
        result = run_preflight(self.base_url, allow_loopback=True)

        self.assertTrue(result.ready)
        self.assertEqual(result.health_status, "ok")
        self.assertEqual(result.api_version, "0.2.0-alpha")
        self.assertEqual(result.season_id, "2026-27")
        self.assertEqual(result.regular_season_games, 84)

    def test_stability_preflight_requires_repeated_matching_identity(self):
        result = run_stability_preflight(
            self.base_url,
            probes=3,
            probe_interval=0,
            allow_loopback=True,
        )

        self.assertTrue(result.ready)
        self.assertEqual(result.api_version, "0.2.0-alpha")

    def test_stability_preflight_rejects_identity_change(self):
        stable = PreflightResult(
            api_base_url="http://192.168.1.25:8000/api/v1",
            health_status="ok",
            api_version="0.2.0-alpha",
            season_id="2026-27",
            regular_season_games=84,
            ready=True,
        )
        changed = PreflightResult(
            api_base_url=stable.api_base_url,
            health_status="ok",
            api_version="unexpected-version",
            season_id=stable.season_id,
            regular_season_games=stable.regular_season_games,
            ready=True,
        )

        with patch("scripts.check_alpha_backend.run_preflight", side_effect=[stable, changed]):
            with self.assertRaisesRegex(RuntimeError, "identity changed"):
                run_stability_preflight(stable.api_base_url, probes=2)

    def test_stability_preflight_rejects_invalid_probe_settings(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            run_stability_preflight(self.base_url, probes=0, allow_loopback=True)
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            run_stability_preflight(
                self.base_url,
                probes=1,
                probe_interval=-1,
                allow_loopback=True,
            )

    def test_loopback_is_rejected_for_tester_builds(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            _normalized_base_url("http://127.0.0.1:8000/api/v1")

        with self.assertRaisesRegex(ValueError, "localhost"):
            _normalized_base_url("http://localhost:8000/api/v1")

    def test_non_loopback_endpoint_is_accepted(self):
        self.assertEqual(
            _normalized_base_url("http://192.168.1.25:8000/api/v1/"),
            "http://192.168.1.25:8000/api/v1",
        )


if __name__ == "__main__":
    unittest.main()
