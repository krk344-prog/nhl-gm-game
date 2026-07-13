import sqlite3
import unittest

from src.roster_import import (
    deterministic_simulation_profile,
    import_snapshot_catalog,
    merge_snapshots,
    normalize_nhl_team_roster,
    normalize_position,
    validate_snapshot,
)


class RosterImportTests(unittest.TestCase):
    def sample_nhl(self):
        return {
            "schema_version": 1,
            "season_id": "2025-2026",
            "created_at": "2026-07-13T00:00:00+00:00",
            "sources": [{"league": "NHL", "name": "test"}],
            "teams": [
                {
                    "league": "NHL",
                    "abbreviation": "BUF",
                    "players": [
                        {
                            "source_player_id": "1",
                            "name": "Test Center",
                            "position": "C",
                            "birth_date": "2000-01-01",
                            "jersey_number": 19,
                            "roster_status": "active",
                        }
                    ],
                }
            ],
        }

    def test_normalizes_official_nhl_payload(self):
        payload = {
            "forwards": [
                {
                    "id": 10,
                    "firstName": {"default": "Alex"},
                    "lastName": {"default": "Example"},
                    "positionCode": "C",
                    "birthDate": "2001-02-03",
                    "sweaterNumber": 12,
                    "shootsCatches": "L",
                }
            ],
            "defensemen": [],
            "goalies": [],
        }
        team = normalize_nhl_team_roster("BUF", payload, "20252026")
        self.assertEqual(team["players"][0]["name"], "Alex Example")
        self.assertEqual(normalize_position(team["players"][0]["position"]), "F")

    def test_placeholder_profile_is_stable_and_labeled(self):
        player = {"source_player_id": "10", "name": "Alex Example", "position": "C"}
        first = deterministic_simulation_profile(player, "2025-2026")
        second = deterministic_simulation_profile(player, "2025-2026")
        self.assertEqual(first, second)
        self.assertEqual(first["ratings_source"], "deterministic_placeholder")
        self.assertEqual(first["contract_data_status"], "unknown_placeholder")

    def test_merges_nhl_and_ahl_snapshots(self):
        nhl = self.sample_nhl()
        ahl = {
            "schema_version": 1,
            "season_id": "2025-2026",
            "created_at": "2026-07-13T00:00:00+00:00",
            "sources": [{"league": "AHL", "name": "test"}],
            "teams": [
                {
                    "league": "AHL",
                    "abbreviation": "ROC",
                    "players": [
                        {"source_player_id": "2", "name": "Test Prospect", "position": "G"}
                    ],
                }
            ],
        }
        merged = merge_snapshots(nhl, ahl)
        self.assertEqual(len(merged["teams"]), 2)
        validate_snapshot(merged)

    def test_catalog_import_is_idempotent(self):
        conn = sqlite3.connect(":memory:")
        first = import_snapshot_catalog(conn, self.sample_nhl())
        second = import_snapshot_catalog(conn, self.sample_nhl())
        self.assertEqual(first["players_imported"], 1)
        self.assertEqual(second["players_imported"], 0)
        self.assertEqual(second["duplicate"], 1)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM roster_import_players").fetchone()[0], 1)

    def test_rejects_duplicate_team(self):
        snapshot = self.sample_nhl()
        snapshot["teams"].append(dict(snapshot["teams"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate team"):
            validate_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
