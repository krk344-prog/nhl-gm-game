import json
import os
import random
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.nhl_gm_api import create_server, get_dashboard, get_roster
from src.league_orchestrator import (
    advance_day,
    get_schedule,
    get_standings,
    initialize_league,
)
from src.nhl_gm_core import init_database


class ApiStateTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_db_path = os.environ.get("NHL_GM_DB_PATH")
        os.environ["NHL_GM_DB_PATH"] = os.path.join(self.temp_dir.name, "test.db")
        random.seed(7)
        init_database()
        initialize_league()

    def tearDown(self):
        if self.previous_db_path is None:
            os.environ.pop("NHL_GM_DB_PATH", None)
        else:
            os.environ["NHL_GM_DB_PATH"] = self.previous_db_path
        self.temp_dir.cleanup()

    def test_dashboard_returns_live_cap_and_ratings(self):
        dashboard = get_dashboard(1)

        self.assertEqual(dashboard["team"]["name"], "Titans")
        self.assertEqual(
            dashboard["roster"],
            {
                "total": 23,
                "forwards": 13,
                "defensemen": 8,
                "goalies": 2,
            },
        )
        self.assertLessEqual(
            dashboard["finances"]["cap_hit"],
            dashboard["finances"]["cap_ceiling"],
        )
        self.assertGreater(dashboard["ratings"]["overall"], 0)
        self.assertEqual(dashboard["next_game"]["day"], 2)
        self.assertEqual(dashboard["standing"]["games_played"], 0)

    def test_roster_returns_persisted_players_with_derived_fields(self):
        roster = get_roster(1)

        self.assertEqual(roster["count"], 23)
        self.assertEqual(roster["players"][0]["position"], "F")
        self.assertIn("overall", roster["players"][0])
        self.assertEqual(roster["players"][0]["scouting_uncertainty"], 20.0)

    def test_unknown_team_raises_lookup_error(self):
        with self.assertRaisesRegex(LookupError, "Team 999 does not exist"):
            get_dashboard(999)

    def test_schedule_seeds_full_home_and_away_season(self):
        schedule = get_schedule(team_id=1, limit=200)["games"]

        self.assertEqual(len(schedule), 82)
        self.assertEqual(schedule[0]["day"], 2)
        self.assertEqual(schedule[-1]["day"], 164)
        self.assertEqual(
            sum(game["home_team_id"] == 1 for game in schedule),
            41,
        )

    def test_advance_day_simulates_slate_and_updates_standings(self):
        result = advance_day()

        self.assertEqual(result["calendar"]["current_day"], 2)
        self.assertEqual(len(result["games"]), 1)
        game = result["games"][0]
        self.assertNotEqual(game["home_score"], game["away_score"])
        standings = get_standings()["standings"]
        self.assertEqual(sum(team["games_played"] for team in standings), 2)
        self.assertIn(sum(team["points"] for team in standings), (2, 3))
        completed = get_schedule(day=2)["games"][0]
        self.assertEqual(completed["status"], "completed")

    def test_http_routes_return_json_and_cors(self):
        server = create_server("127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urlopen(f"{base_url}/api/v1/teams/1/dashboard") as response:
                payload = json.load(response)
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
                self.assertEqual(payload["roster"]["total"], 23)

            with urlopen(f"{base_url}/api/v1/schedule?day=2") as response:
                payload = json.load(response)
                self.assertEqual(len(payload["games"]), 1)

            request = Request(f"{base_url}/api/v1/advance-day", method="POST")
            with urlopen(request) as response:
                payload = json.load(response)
                self.assertEqual(payload["calendar"]["current_day"], 2)
                self.assertEqual(len(payload["games"]), 1)

            with urlopen(f"{base_url}/api/v1/standings") as response:
                payload = json.load(response)
                self.assertEqual(
                    sum(team["games_played"] for team in payload["standings"]),
                    2,
                )

            with self.assertRaises(HTTPError) as error:
                urlopen(f"{base_url}/api/v1/teams/999/roster")
            self.assertEqual(error.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
