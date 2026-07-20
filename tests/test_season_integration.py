import sqlite3

import pytest

from src.nhl_gm_core import (
    ComplianceGate,
    DynamicFinancialPool,
    get_season_context,
    init_database,
)
from src.rules_registry import RulesValidationError


def test_new_save_binds_rules_and_schedule_denominator(tmp_path):
    db = tmp_path / "save.db"
    init_database(db, season_id="2025-26", accrual_days=192)

    context = get_season_context(db)
    assert context["season_id"] == "2025-26"
    assert context["rules_schema_version"] == 1
    assert context["salary_cap_ceiling"] == 95_500_000
    assert context["salary_cap_floor"] == 70_600_000
    assert context["active_roster_maximum"] == 23
    assert context["accrual_days"] == 192


def test_new_save_refuses_magic_accrual_denominator(tmp_path):
    with pytest.raises(RulesValidationError, match="accrual-day denominator"):
        init_database(tmp_path / "save.db", season_id="2025-26")


def test_legacy_save_migrates_existing_max_days(tmp_path):
    db = tmp_path / "legacy.db"
    with sqlite3.connect(db) as conn:
        conn.execute("""
            CREATE TABLE league_calendar (
                id INTEGER PRIMARY KEY,
                current_day INTEGER,
                max_days INTEGER,
                salary_cap_ceiling REAL,
                accrued_margin REAL
            )
        """)
        conn.execute(
            "INSERT INTO league_calendar VALUES (1, 30, 186, 92000000, 125000)"
        )

    init_database(db, season_id="2025-26")
    context = get_season_context(db)
    assert context["current_day"] == 30
    assert context["accrual_days"] == 186
    assert context["salary_cap_ceiling"] == 95_500_000
    assert context["season_id"] == "2025-26"


def test_alpha_save_metadata_survives_rules_migration(tmp_path):
    """PR #2 must enrich an Alpha save without erasing its save identity."""
    db = tmp_path / "alpha.db"
    with sqlite3.connect(db) as conn:
        conn.execute("""
            CREATE TABLE league_calendar (
                id INTEGER PRIMARY KEY,
                current_day INTEGER,
                max_days INTEGER,
                salary_cap_ceiling REAL,
                accrued_margin REAL
            )
        """)
        conn.execute(
            "INSERT INTO league_calendar VALUES (1, 47, 186, 92000000, 250000)"
        )
        conn.execute("""
            CREATE TABLE game_settings (
                id INTEGER PRIMARY KEY,
                user_team_id INTEGER NOT NULL,
                save_name TEXT NOT NULL,
                seed INTEGER NOT NULL,
                schema_version INTEGER NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO game_settings VALUES (1, 4, 'Kyle Closed Alpha', 7, 2)"
        )

    init_database(db, season_id="2025-26")

    with sqlite3.connect(db) as conn:
        saved = conn.execute(
            "SELECT user_team_id, save_name, seed, schema_version FROM game_settings WHERE id = 1"
        ).fetchone()
        current_day = conn.execute(
            "SELECT current_day FROM league_calendar WHERE id = 1"
        ).fetchone()[0]

    assert saved == (4, "Kyle Closed Alpha", 7, 2)
    assert current_day == 47
    assert get_season_context(db)["season_id"] == "2025-26"


def test_alpha_trade_history_survives_rules_migration(tmp_path):
    """Rules migration must not erase a completed Alpha transaction ledger."""
    db = tmp_path / "alpha-trade.db"
    with sqlite3.connect(db) as conn:
        conn.execute("""
            CREATE TABLE league_calendar (
                id INTEGER PRIMARY KEY,
                current_day INTEGER,
                max_days INTEGER,
                salary_cap_ceiling REAL,
                accrued_margin REAL
            )
        """)
        conn.execute(
            "INSERT INTO league_calendar VALUES (1, 61, 186, 92000000, 500000)"
        )
        conn.execute("""
            CREATE TABLE trade_history (
                id INTEGER PRIMARY KEY,
                day INTEGER NOT NULL,
                user_team_id INTEGER NOT NULL,
                target_team_id INTEGER NOT NULL,
                offered_player_id INTEGER NOT NULL,
                target_player_id INTEGER NOT NULL,
                offered_value REAL NOT NULL,
                target_value REAL NOT NULL,
                required_value REAL NOT NULL,
                relationship_score REAL NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            """
            INSERT INTO trade_history VALUES (
                1, 44, 1, 3, 11, 72, 83.5, 81.0, 80.0, 55.0,
                'approved', 'Accepted after value and relationship review',
                '2026-07-12 12:00:00'
            )
            """
        )

    init_database(db, season_id="2025-26")

    with sqlite3.connect(db) as conn:
        trade = conn.execute(
            """
            SELECT day, user_team_id, target_team_id, offered_player_id,
                   target_player_id, status, reason, created_at
              FROM trade_history
             WHERE id = 1
            """
        ).fetchone()

    assert trade == (
        44,
        1,
        3,
        11,
        72,
        "approved",
        "Accepted after value and relationship review",
        "2026-07-12 12:00:00",
    )
    assert get_season_context(db)["current_day"] == 61


def test_alpha_completed_schedule_survives_rules_migration(tmp_path):
    """Rules migration must preserve a completed Alpha game and its result log."""
    db = tmp_path / "alpha-schedule.db"
    with sqlite3.connect(db) as conn:
        conn.execute("""
            CREATE TABLE league_calendar (
                id INTEGER PRIMARY KEY,
                current_day INTEGER,
                max_days INTEGER,
                salary_cap_ceiling REAL,
                accrued_margin REAL
            )
        """)
        conn.execute(
            "INSERT INTO league_calendar VALUES (1, 62, 186, 92000000, 500000)"
        )
        conn.execute("""
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
        """)
        conn.executemany(
            "INSERT INTO teams (id, name, city, tier) VALUES (?, ?, ?, 'NHL')",
            ((1, "Blizzards", "Buffalo"), (2, "Titans", "New York")),
        )
        conn.execute("""
            CREATE TABLE schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                home_team_id INTEGER NOT NULL,
                away_team_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled'
                    CHECK(status IN ('scheduled', 'in_progress', 'completed')),
                home_score INTEGER,
                away_score INTEGER,
                overtime INTEGER NOT NULL DEFAULT 0,
                result_log TEXT,
                UNIQUE(day, home_team_id, away_team_id),
                CHECK(home_team_id != away_team_id),
                FOREIGN KEY(home_team_id) REFERENCES teams(id),
                FOREIGN KEY(away_team_id) REFERENCES teams(id)
            )
        """)
        conn.execute(
            """
            INSERT INTO schedule VALUES (
                9, 60, 1, 2, 'completed', 4, 3, 1,
                'Buffalo won 4-3 in overtime'
            )
            """
        )

    init_database(db, season_id="2025-26")

    with sqlite3.connect(db) as conn:
        game = conn.execute(
            """
            SELECT day, home_team_id, away_team_id, status,
                   home_score, away_score, overtime, result_log
              FROM schedule
             WHERE id = 9
            """
        ).fetchone()

    assert game == (
        60,
        1,
        2,
        "completed",
        4,
        3,
        1,
        "Buffalo won 4-3 in overtime",
    )
    assert get_season_context(db)["current_day"] == 62


def test_save_cannot_silently_change_seasons(tmp_path):
    db = tmp_path / "save.db"
    init_database(db, season_id="2025-26", accrual_days=192)
    with pytest.raises(RulesValidationError, match="Save belongs to 2025-26"):
        init_database(
            db,
            season_id="2026-27",
            accrual_days=200,
            allow_projected=True,
        )


def test_daily_accrual_uses_saved_schedule_denominator(tmp_path):
    db = tmp_path / "save.db"
    init_database(db, season_id="2025-26", accrual_days=200)
    with sqlite3.connect(db) as conn:
        before = conn.execute(
            "SELECT cash_balance FROM teams WHERE id = 1"
        ).fetchone()[0]
        roster_aav = conn.execute(
            "SELECT SUM(aav) FROM players WHERE team_id = 1"
        ).fetchone()[0]

    DynamicFinancialPool.process_daily_cap_accrual(db)

    with sqlite3.connect(db) as conn:
        after = conn.execute(
            "SELECT cash_balance FROM teams WHERE id = 1"
        ).fetchone()[0]
    assert after == pytest.approx(before - roster_aav / 200)


def test_compliance_gate_uses_registry_roster_limit(tmp_path):
    db = tmp_path / "save.db"
    init_database(db, season_id="2025-26", accrual_days=192)
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE players SET aav = 1000000 WHERE team_id = 1")
    legal, errors = ComplianceGate.verify_roster_legality(1, db)
    assert legal is True
    assert errors == []
