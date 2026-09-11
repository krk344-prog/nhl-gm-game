import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_alpha_backend import PreflightResult
from prepare_alpha_build import prepare_build_handoff


class AlphaBuildHandoffContractTests(unittest.TestCase):
    def test_handoff_exposes_required_five_minute_qualification(self):
        endpoint = "http://192.168.1.25:8000/api/v1"

        def preflight(api_base_url, **_kwargs):
            return PreflightResult(
                ready=True,
                api_base_url=api_base_url,
                season_id="2026-27",
                regular_season_games=84,
                checks={},
            )

        payload = prepare_build_handoff(api_base_url=endpoint, preflight=preflight)

        self.assertEqual(payload["qualification_minimum_seconds"], 300)
        self.assertIn("five-minute continuity soak", payload["next_action"])
        self.assertEqual(payload["api_base_url"], endpoint)


if __name__ == "__main__":
    unittest.main()
