import unittest

from src.roster_promotion import validate_promotion_readiness


class RosterPromotionTests(unittest.TestCase):
    def test_partial_catalog_is_not_ready_for_new_game_promotion(self):
        snapshot = {
            "schema_version": 1,
            "season_id": "2025-2026",
            "created_at": "2026-07-13T00:00:00+00:00",
            "sources": [{"league": "NHL", "name": "reviewed test source"}],
            "teams": [
                {
                    "league": "NHL",
                    "abbreviation": "BUF",
                    "players": [
                        {
                            "source_player_id": "1",
                            "name": "Test Center",
                            "position": "C",
                        }
                    ],
                },
                {"league": "AHL", "abbreviation": "ROC", "players": []},
            ],
        }

        result = validate_promotion_readiness(
            snapshot,
            expected_team_counts={"NHL": 1, "AHL": 1},
        )

        self.assertFalse(result["ready"])
        self.assertEqual(result["empty_teams"], ["AHL ROC"])
        self.assertIn("Every promoted team requires at least one player.", result["blockers"])
        self.assertTrue(result["source_provenance_present"])

    def test_complete_catalog_without_provenance_is_blocked(self):
        player = {
            "source_player_id": "1",
            "name": "Test Player",
            "position": "C",
        }
        snapshot = {
            "schema_version": 1,
            "season_id": "2025-2026",
            "created_at": "2026-07-13T00:00:00+00:00",
            "sources": [],
            "teams": [
                {"league": "NHL", "abbreviation": "BUF", "players": [player]},
                {"league": "AHL", "abbreviation": "ROC", "players": [player]},
            ],
        }

        result = validate_promotion_readiness(
            snapshot,
            expected_team_counts={"NHL": 1, "AHL": 1},
        )

        self.assertFalse(result["ready"])
        self.assertFalse(result["source_provenance_present"])
        self.assertEqual(result["empty_teams"], [])
        self.assertEqual(result["count_mismatches"], {})
        self.assertEqual(
            result["blockers"],
            ["Roster pack requires source provenance before promotion."],
        )

    def test_complete_32_nhl_32_ahl_catalog_is_ready(self):
        teams = []
        for league in ("NHL", "AHL"):
            for index in range(32):
                teams.append(
                    {
                        "league": league,
                        "abbreviation": f"{league[0]}{index:02d}",
                        "players": [
                            {
                                "source_player_id": f"{league.lower()}-{index}",
                                "name": f"{league} Test Player {index}",
                                "position": "C",
                            }
                        ],
                    }
                )

        snapshot = {
            "schema_version": 1,
            "season_id": "2025-2026",
            "created_at": "2026-07-14T00:00:00+00:00",
            "sources": [
                {"league": "NHL", "name": "reviewed NHL test source"},
                {"league": "AHL", "name": "reviewed AHL test source"},
            ],
            "teams": teams,
        }

        result = validate_promotion_readiness(snapshot)

        self.assertTrue(result["ready"])
        self.assertEqual(result["team_counts"], {"NHL": 32, "AHL": 32})
        self.assertEqual(result["empty_teams"], [])
        self.assertEqual(result["count_mismatches"], {})
        self.assertTrue(result["source_provenance_present"])
        self.assertEqual(result["blockers"], [])


if __name__ == "__main__":
    unittest.main()
