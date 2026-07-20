import sqlite3

from src.nhl_gm_core import get_season_context, init_database


def test_alpha_franchise_catalog_survives_rules_migration(tmp_path):
    """Season-rules migration must preserve NHL clubs and the Alpha AHL affiliate."""
    db = tmp_path / "alpha-franchises.db"
    franchises = (
        (1, "Blizzards", "Buffalo", "NHL"),
        (2, "Titans", "New York", "NHL"),
        (3, "Auditors", "Detroit", "NHL"),
        (4, "Harbors", "Boston", "NHL"),
        (5, "Towers", "Toronto", "NHL"),
        (6, "Voyageurs", "Montreal", "NHL"),
        (7, "Forge", "Chicago", "NHL"),
        (8, "Orcas", "Seattle", "NHL"),
        (9, "Northstars", "Rochester", "AHL"),
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
            "INSERT INTO teams (id, name, city, tier) VALUES (?, ?, ?, ?)",
            franchises,
        )

    init_database(db, season_id="2025-26")

    with sqlite3.connect(db) as conn:
        saved = conn.execute(
            "SELECT id, name, city, tier FROM teams ORDER BY id"
        ).fetchall()
        nhl_team_count = conn.execute(
            "SELECT COUNT(*) FROM teams WHERE tier = 'NHL'"
        ).fetchone()[0]
        ahl_team_count = conn.execute(
            "SELECT COUNT(*) FROM teams WHERE tier = 'AHL'"
        ).fetchone()[0]

    assert saved == list(franchises)
    assert nhl_team_count == 8
    assert ahl_team_count == 1
    assert get_season_context(db)["current_day"] == 71


def test_alpha_standings_survive_rules_migration(tmp_path):
    """Rules migration must preserve the playable Alpha's standings ledger."""
    db = tmp_path / "alpha-standings.db"
    standings = (
        (1, 45, 28, 12, 5, 61, 156, 124, "W3", 103),
        (2, 45, 24, 16, 5, 53, 142, 137, "L1", 103),
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
            "INSERT INTO league_calendar VALUES (1, 103, 186, 92000000, 925000)"
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
            ((1, "Blizzards", "Buffalo"), (2, "Titans", "New York")),
        )
        conn.execute(
            """
            CREATE TABLE standings (
                team_id INTEGER PRIMARY KEY,
                games_played INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                overtime_losses INTEGER NOT NULL DEFAULT 0,
                points INTEGER NOT NULL DEFAULT 0,
                goals_for INTEGER NOT NULL DEFAULT 0,
                goals_against INTEGER NOT NULL DEFAULT 0,
                streak TEXT NOT NULL DEFAULT '-',
                updated_day INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(team_id) REFERENCES teams(id)
            )
            """
        )
        conn.executemany(
            "INSERT INTO standings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            standings,
        )

    init_database(db, season_id="2025-26")

    with sqlite3.connect(db) as conn:
        saved = conn.execute(
            """
            SELECT team_id, games_played, wins, losses, overtime_losses,
                   points, goals_for, goals_against, streak, updated_day
            FROM standings
            ORDER BY team_id
            """
        ).fetchall()

    assert saved == list(standings)
    assert get_season_context(db)["current_day"] == 103
