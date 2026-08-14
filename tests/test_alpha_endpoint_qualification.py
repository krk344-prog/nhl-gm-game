import unittest
from unittest.mock import patch

from scripts.check_alpha_backend import PreflightResult
from scripts.qualify_alpha_endpoint import qualify_endpoint


class AlphaEndpointQualificationTests(unittest.TestCase):
    def _result(self, *, api_version="0.2.0-alpha"):
        return PreflightResult(
            api_base_url="http://192.168.1.25:8000/api/v1",
            health_status="ok",
            api_version=api_version,
            season_id="2026-27",
            regular_season_games=84,
            ready=True,
        )

    def test_matching_backend_identity_passes_qualification(self):
        times = iter([0.0, 0.0, 30.0, 30.0])
        stable = self._result()

        with patch(
            "scripts.qualify_alpha_endpoint.run_preflight",
            side_effect=[stable, stable],
        ):
            result = qualify_endpoint(
                stable.api_base_url,
                duration_seconds=30.0,
                interval_seconds=30.0,
                clock=lambda: next(times),
                sleeper=lambda _: None,
            )

        self.assertTrue(result.ready)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.passed_attempts, 2)

    def test_backend_identity_change_blocks_qualification(self):
        stable = self._result()
        changed = self._result(api_version="unexpected-version")
        times = iter([0.0, 0.0, 30.0])

        with patch(
            "scripts.qualify_alpha_endpoint.run_preflight",
            side_effect=[stable, changed],
        ):
            with self.assertRaisesRegex(RuntimeError, "identity changed"):
                qualify_endpoint(
                    stable.api_base_url,
                    duration_seconds=30.0,
                    interval_seconds=30.0,
                    clock=lambda: next(times),
                    sleeper=lambda _: None,
                )


if __name__ == "__main__":
    unittest.main()
