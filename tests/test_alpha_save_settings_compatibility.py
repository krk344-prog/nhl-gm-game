import sqlite3

from src.nhl_gm_core import get_season_context, init_database


def test_alpha_game_settings_survive_rules_migration(tmp_path):
    """Rules migration must preserve the playable Alpha's selected franchise and save identity."""
    db = tmp_path / "alpha-game-settings.db"
    settings = (
        1,
        4,
        "Harbors Rebuild",
        314159,
        2,
        "2026-07-10 14:30:00",
        "2026-07-20 09:15:00",
    )

    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE league_calendar (
                id INTEGER PRIMARY KEY,
                current_day INTEGER,
                max_days INTEGER,
                salary_cap_ceiling REAL,
                accrued_margin REAL
            )
            """
        )
        conn.execute(
            "INSERT INTO league_calendar VALUES (1, 117, 186, 92000000, 640000)"
        )
        conn.execute(
            """
            CREATE TABLE teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                city TEXT,
                tier TEXT,
                cash_balance REAL DEFAULT 25000000.0,
                gm_trust_score REAL DEFAULT 70.0,
                franchise_mandate TEXT DEFAULT 'Moneyball Auditor',
                relationship_score REAL DEFAULT 50.0
            )
            """
        )
        conn.execute(
            "INSERT INTO teams (id, name, city, tier) VALUES (4, 'Harbors', 'Boston', 'NHL')"
        )
        conn.execute(
            """
            CREATE TABLE game_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                user_team_id INTEGER NOT NULL,
                save_name TEXT NOT NULL DEFAULT 'Alpha Franchise',
                seed INTEGER NOT NULL,
                schema_version INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_team_id) REFERENCES teams(id)
            )
            """
        )
        conn.execute(
            "INSERT INTO game_settings VALUES (?, ?, ?, ?, ?, ?, ?)",
            settings,
        )

    init_database(db, season_id="2025-26")

    with sqlite3.connect(db) as conn:
        saved = conn.execute(
            """
            SELECT id, user_team_id, save_name, seed, schema_version,
                   created_at, updated_at
            FROM game_settings
            WHERE id = 1
            """
        ).fetchone()

    assert saved == settings
    assert get_season_context(db)["current_day"] == 117
