import os
import random
import tempfile
import unittest

from src.game_service import reset_game
from src.league_orchestrator import advance_day, initialize_league
from src.nhl_gm_api import get_dashboard, get_roster
from src.nhl_gm_core import connect_database, init_database
from src.scouting_service import (
    create_assignment,
    get_player_dossier,
    get_scouting_center,
    list_assignments,
    list_reports,
    run_accuracy_calibration,
)
from src.trade_service import get_trade_market


class ScoutingIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_db = os.environ.get("NHL_GM_DB_PATH")
        os.environ["NHL_GM_DB_PATH"] = os.path.join(self.temp_dir.name, "scouting.db")
        random.seed(7)
        init_database(seed=7)
        initialize_league()

    def tearDown(self):
        if self.previous_db is None:
            os.environ.pop("NHL_GM_DB_PATH", None)
        else:
            os.environ["NHL_GM_DB_PATH"] = self.previous_db
        self.temp_dir.cleanup()

    def test_initializes_staff_and_team_specific_knowledge(self):
        center = get_scouting_center(1)
        self.assertEqual(center["department"]["scout_count"], 5)
        self.assertEqual(len(center["priority_board"]), 30)
        with connect_database() as conn:
            team_count = conn.execute("SELECT COUNT(*) FROM teams WHERE tier = 'NHL'").fetchone()[0]
            player_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
            knowledge_count = conn.execute("SELECT COUNT(*) FROM team_player_knowledge").fetchone()[0]
        self.assertEqual(knowledge_count, team_count * player_count)

    def test_roster_and_trade_payloads_never_expose_true_attributes(self):
        hidden = {
            "shooting", "passing", "positioning", "reflexes", "speed", "checking",
            "true_potential", "durability", "character_rating", "scouting_region",
        }
        roster_player = get_roster(1)["players"][0]
        rival_player = get_trade_market(1)["target_players"][0]
        self.assertTrue(hidden.isdisjoint(roster_player))
        self.assertTrue(hidden.isdisjoint(rival_player))
        self.assertIn("overall_range", rival_player)
        self.assertIn("confidence", rival_player)
        self.assertEqual(get_dashboard(1)["ratings"]["source"], "organization scouting consensus")

    def test_deep_assignment_completes_and_reduces_uncertainty(self):
        center = get_scouting_center(1)
        scout = max(center["scouts"], key=lambda item: item["accuracy"])
        player = center["priority_board"][0]
        before_width = player["overall_range"]["high"] - player["overall_range"]["low"]
        assignment = create_assignment(1, scout["id"], player["id"], focus="overall", depth="deep")
        self.assertEqual(assignment["status"], "active")
        for _ in range(10):
            advance_day()
        completed = list_assignments(1, status="completed")
        self.assertEqual(len(completed), 1)
        reports = list_reports(1, player_id=player["id"])
        self.assertEqual(len(reports), 1)
        dossier = get_player_dossier(1, player["id"])["player"]
        after_width = dossier["overall_range"]["high"] - dossier["overall_range"]["low"]
        self.assertLess(after_width, before_width)
        self.assertGreater(dossier["observations"], player["observations"])
        self.assertLess(reports[0]["current_low"], reports[0]["current_high"])

    def test_scout_capacity_blocks_over_assignment(self):
        center = get_scouting_center(1)
        scout = min(center["scouts"], key=lambda item: item["workload_capacity"])
        players = center["priority_board"]
        for index in range(scout["workload_capacity"]):
            create_assignment(1, scout["id"], players[index]["id"], focus="overall", depth="quick")
        with self.assertRaisesRegex(ValueError, "capacity is full"):
            create_assignment(
                1, scout["id"], players[scout["workload_capacity"]]["id"],
                focus="overall", depth="quick",
            )

    def test_accuracy_calibration_rewards_scout_quality(self):
        result = run_accuracy_calibration(1, samples=12)
        self.assertTrue(result["stronger_scout_wins"])
        self.assertLess(
            result["stronger_mean_absolute_error"],
            result["weaker_mean_absolute_error"],
        )
        self.assertIsNotNone(result["regional_specialist_wins"])

    def test_reset_removes_old_assignments_and_reports(self):
        center = get_scouting_center(1)
        create_assignment(
            1, center["scouts"][0]["id"], center["priority_board"][0]["id"],
            focus="potential", depth="quick",
        )
        reset_game(seed=8, save_name="Scouting Reset")
        self.assertEqual(list_assignments(1), [])
        self.assertEqual(list_reports(1), [])
        self.assertEqual(get_scouting_center(1)["department"]["scout_count"], 5)


if __name__ == "__main__":
    unittest.main()
