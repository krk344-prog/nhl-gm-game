import json
import os
import random
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen

from src.league_orchestrator import initialize_league
from src.nhl_gm_core import init_database
from src.season_context_api import create_season_context_server


class TechnicalAlphaReadinessSmokeTest(unittest.TestCase):
    """Exercise the minimum persisted user-test loop through the integrated API."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_db_path = os.environ.get("NHL_GM_DB_PATH")
        os.environ["NHL_GM_DB_PATH"] = os.path.join(
            self.temp_dir.name, "technical-alpha.db"
        )
        random.seed(7)
        init_database(seed=7)
        initialize_league()
        self._start_server()

    def tearDown(self):
        self._stop_server()
        if self.previous_db_path is None:
            os.environ.pop("NHL_GM_DB_PATH", None)
        else:
            os.environ["NHL_GM_DB_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def _start_server(self):
        self.server = create_season_context_server("127.0.0.1", 0)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def _stop_server(self):
        if getattr(self, "server", None) is None:
            return
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.server = None

    def _request(self, path, *, method="GET", payload=None):
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        with urlopen(request, timeout=10) as response:
            return response.status, json.load(response)

    def test_select_advance_restart_reload_and_reset(self):
        status, health = self._request("/api/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(health, {"status": "ok", "version": "0.2.0-alpha"})

        status, season = self._request(
            "/api/v1/season-context?season_id=2026-27"
        )
        self.assertEqual(status, 200)
        self.assertEqual(season["season_context"]["regular_season_games"], 84)

        status, selected = self._request(
            "/api/v1/game/select-team",
            method="POST",
            payload={"team_id": 4},
        )
        self.assertEqual(status, 200)
        self.assertEqual(selected["user_team_id"], 4)

        status, advanced = self._request("/api/v1/advance-day", method="POST")
        self.assertEqual(status, 200)
        self.assertEqual(advanced["calendar"]["current_day"], 2)
        self.assertEqual(len(advanced["games"]), 4)

        status, roster = self._request("/api/v1/teams/4/roster")
        self.assertEqual(status, 200)
        self.assertEqual(roster["count"], 23)

        status, standings = self._request("/api/v1/standings")
        self.assertEqual(status, 200)
        self.assertEqual(
            sum(team["games_played"] for team in standings["standings"]),
            8,
        )

        status, market = self._request(
            "/api/v1/trade-market?user_team_id=4&target_team_id=2"
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(market["offered_players"]), 23)
        self.assertEqual(len(market["target_players"]), 23)

        self._stop_server()
        self._start_server()

        status, reloaded = self._request("/api/v1/game")
        self.assertEqual(status, 200)
        self.assertEqual(reloaded["user_team_id"], 4)
        self.assertEqual(reloaded["save"]["current_day"], 2)

        status, debug_report = self._request("/api/v1/debug-report")
        self.assertEqual(status, 200)
        self.assertEqual(debug_report["game"]["user_team_id"], 4)
        self.assertEqual(debug_report["game"]["save"]["current_day"], 2)

        status, reset = self._request(
            "/api/v1/game/reset",
            method="POST",
            payload={"confirm": "RESET", "seed": 11, "save_name": "Pilot Reset"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(reset["save"]["name"], "Pilot Reset")
        self.assertEqual(reset["save"]["current_day"], 1)
        self.assertEqual(reset["user_team_id"], 1)


if __name__ == "__main__":
    unittest.main()
