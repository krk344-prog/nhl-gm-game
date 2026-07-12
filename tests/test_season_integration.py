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
    legal, errors = ComplianceGate.verify_roster_legality(1, db)
    assert legal is True
    assert errors == []
