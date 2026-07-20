import sqlite3

from src.nhl_gm_core import get_season_context, init_database


def test_alpha_franchise_catalog_survives_rules_migration(tmp_path):
    """Season-rules migration must not replace the playable Alpha's franchises."""
    db = tmp_path / "alpha-franchises.db"
    franchises = (
        (1, "Blizzards", "Buffalo"),
        (2, "Titans", "New York"),
        (3, "Auditors", "Detroit"),
        (4, "Harbors", "Boston"),
        (5, "Towers", "Toronto"),
        (6, "Voyageurs", "Montreal"),
        (7, "Forge", "Chicago"),
        (8, "Orcas", "Seattle"),
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
            "INSERT INTO league_calendar VALUES (1, 71, 186, 92000000, 750000)"
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
        conn.executemany(
            "INSERT INTO teams (id, name, city, tier) VALUES (?, ?, ?, 'NHL')",
            franchises,
        )

    init_database(db, season_id="2025-26")

    with sqlite3.connect(db) as conn:
        saved = conn.execute(
            "SELECT id, name, city FROM teams WHERE tier = 'NHL' ORDER BY id"
        ).fetchall()
        all_team_count = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]

    assert saved == list(franchises)
    assert all_team_count == 8
    assert get_season_context(db)["current_day"] == 71
