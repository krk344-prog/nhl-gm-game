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


if __name__ == "__main__":
    unittest.main()
