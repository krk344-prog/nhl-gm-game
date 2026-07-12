"""Season-aware NHL general manager simulation core.

The engine loads its legal environment from ``config/rules/<season>.json``.
Existing prototype databases are migrated in place; new saves require an
explicit cap-accrual denominator until the official schedule supplies one.
"""

from __future__ import annotations

import math
import os
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any

try:
    from rules_registry import RulesRegistry, RulesValidationError, SeasonRules
except ImportError:
    from src.rules_registry import RulesRegistry, RulesValidationError, SeasonRules

DEFAULT_DB_PATH = Path(os.environ.get("NHL_GM_DB_PATH", "nhl_gm_core.db"))
DEFAULT_SEASON_ID = os.environ.get("NHL_GM_SEASON_ID", "2025-26")


def _connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    if column not in _column_names(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _load_rules(season_id: str, *, registry: RulesRegistry | None = None, allow_projected: bool = False) -> SeasonRules:
    registry = registry or RulesRegistry()
    rules = registry.load(season_id, allow_projected=allow_projected)
    rules.require_verified((
        "salary_system.upper_limit",
        "salary_system.lower_limit",
        "salary_system.active_roster_maximum",
    ))
    return rules


def _resolve_accrual_days(conn: sqlite3.Connection, rules: SeasonRules, requested: int | None) -> int:
    candidates: list[Any] = [requested, rules.competition.get("accrual_days")]
    table_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='league_calendar'"
    ).fetchone()
    if table_exists:
        columns = _column_names(conn, "league_calendar")
        if "accrual_days" in columns:
            row = conn.execute("SELECT accrual_days FROM league_calendar WHERE id = 1").fetchone()
            candidates.append(row["accrual_days"] if row else None)
        if "max_days" in columns:
            row = conn.execute("SELECT max_days FROM league_calendar WHERE id = 1").fetchone()
            candidates.append(row["max_days"] if row else None)
    for value in candidates:
        if isinstance(value, int) and value > 0:
            return value
    raise RulesValidationError(
        f"{rules.season_id} needs an accrual-day denominator. "
        "Pass accrual_days from the generated official schedule."
    )


def init_database(
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    season_id: str = DEFAULT_SEASON_ID,
    accrual_days: int | None = None,
    registry: RulesRegistry | None = None,
    allow_projected: bool = False,
) -> SeasonRules:
    """Create or migrate a save and bind it to one immutable season ruleset."""
    rules = _load_rules(season_id, registry=registry, allow_projected=allow_projected)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS league_calendar (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_day INTEGER NOT NULL DEFAULT 1,
                max_days INTEGER,
                salary_cap_ceiling REAL,
                accrued_margin REAL NOT NULL DEFAULT 0.0
            )
        """)
        if conn.execute("SELECT COUNT(*) AS n FROM league_calendar").fetchone()["n"] == 0:
            conn.execute(
                "INSERT INTO league_calendar (id, current_day, max_days, salary_cap_ceiling, accrued_margin) VALUES (1, 1, NULL, ?, 0.0)",
                (float(rules.salary_system["upper_limit"]),),
            )

        for name, definition in (
            ("season_id", "TEXT"),
            ("rules_schema_version", "INTEGER"),
            ("accrual_days", "INTEGER"),
            ("salary_cap_floor", "REAL"),
            ("active_roster_maximum", "INTEGER"),
            ("ruleset_status", "TEXT"),
        ):
            _add_column_if_missing(conn, "league_calendar", name, definition)

        current = conn.execute("SELECT * FROM league_calendar WHERE id = 1").fetchone()
        saved_season = current["season_id"]
        if saved_season and saved_season != season_id:
            raise RulesValidationError(
                f"Save belongs to {saved_season}; refusing to reopen it as {season_id}. "
                "Use a new database or an explicit offseason rollover migration."
            )

        resolved_days = _resolve_accrual_days(conn, rules, accrual_days)
        conn.execute("""
            UPDATE league_calendar
               SET season_id = ?, rules_schema_version = ?, accrual_days = ?, max_days = ?,
                   salary_cap_ceiling = ?, salary_cap_floor = ?, active_roster_maximum = ?,
                   ruleset_status = ?
             WHERE id = 1
        """, (
            rules.season_id,
            rules.schema_version,
            resolved_days,
            resolved_days,
            float(rules.salary_system["upper_limit"]),
            float(rules.salary_system["lower_limit"]),
            int(rules.salary_system["active_roster_maximum"]),
            rules.ruleset_status,
        ))

        conn.execute("""
            CREATE TABLE IF NOT EXISTS teams (
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                name TEXT,
                age INTEGER,
                position TEXT,
                archetype TEXT,
                shooting INTEGER CHECK(shooting BETWEEN 30 AND 99),
                passing INTEGER CHECK(passing BETWEEN 30 AND 99),
                positioning INTEGER CHECK(positioning BETWEEN 30 AND 99),
                reflexes INTEGER CHECK(reflexes BETWEEN 30 AND 99),
                speed INTEGER CHECK(speed BETWEEN 30 AND 99),
                checking INTEGER CHECK(checking BETWEEN 30 AND 99),
                aav REAL,
                contract_years INTEGER,
                fatigue REAL DEFAULT 0.0,
                back_to_back_started INTEGER DEFAULT 0,
                scout_observations INTEGER DEFAULT 0,
                FOREIGN KEY(team_id) REFERENCES teams(id)
            )
        """)
        _seed_prototype_league(conn, rules)
        conn.commit()
        return rules
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _seed_prototype_league(conn: sqlite3.Connection, rules: SeasonRules) -> None:
    if conn.execute("SELECT COUNT(*) AS n FROM teams").fetchone()["n"]:
        return
    conn.executemany(
        "INSERT INTO teams (name, city, tier, franchise_mandate, relationship_score) VALUES (?, ?, ?, ?, ?)",
        (
            ("Titans", "New York", "NHL", "Win-Now Titan", 75.0),
            ("Auditors", "Detroit", "NHL", "Moneyball Auditor", 45.0),
            ("Farmhorns", "Grand Rapids", "AHL", "Moneyball Auditor", 100.0),
        ),
    )
    first_names = ["Connor", "Auston", "Nikita", "Nathan", "Leon", "Cale", "Igor"]
    last_names = ["McHockey", "Matthews", "Kucherov", "MacKinnon", "Makar", "Hughes"]

    def add_player(team_id: int, position: str, archetype: str, aav: int) -> None:
        values = {
            "shooting": random.randint(55, 95), "passing": random.randint(55, 95),
            "positioning": random.randint(60, 95), "reflexes": random.randint(30, 50),
            "speed": random.randint(65, 95), "checking": random.randint(55, 95),
        }
        if position == "G":
            values.update(shooting=random.randint(30, 45), positioning=random.randint(85, 98), reflexes=random.randint(86, 99), checking=random.randint(30, 40))
        conn.execute("""
            INSERT INTO players (
                team_id, name, age, position, archetype, shooting, passing,
                positioning, reflexes, speed, checking, aav, contract_years
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            team_id, f"{random.choice(first_names)} {random.choice(last_names)}",
            random.randint(19, 35), position, archetype, values["shooting"], values["passing"],
            values["positioning"], values["reflexes"], values["speed"], values["checking"],
            aav, random.randint(1, 7),
        ))

    for team_id in (1, 2):
        for _ in range(13):
            add_player(team_id, "F", random.choice(["Elite Playmaker", "Volume Sniper", "Two-Way Forward"]), random.randint(1_000_000, 7_000_000))
        for _ in range(8):
            add_player(team_id, "D", random.choice(["Offensive D-Man", "Defensive D-Man"]), random.randint(1_000_000, 6_000_000))
        for _ in range(2):
            add_player(team_id, "G", random.choice(["Butterfly Goalie", "Hybrid Goalie"]), random.randint(1_000_000, 5_000_000))
    for _ in range(10):
        add_player(3, "F", "Minor Prospect", int(rules.salary_system["minimum_nhl_salary"]))


def get_season_context(db_path: Path | str = DEFAULT_DB_PATH) -> dict[str, Any]:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM league_calendar WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("league_calendar is not initialized")
        return dict(row)


class ComplianceGate:
    @staticmethod
    def verify_roster_legality(team_id: int, db_path: Path | str = DEFAULT_DB_PATH) -> tuple[bool, list[str]]:
        with _connect(db_path) as conn:
            count, total_aav = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(aav), 0) FROM players WHERE team_id = ?", (team_id,)
            ).fetchone()
            cal = conn.execute(
                "SELECT salary_cap_ceiling, active_roster_maximum FROM league_calendar WHERE id = 1"
            ).fetchone()
        errors: list[str] = []
        roster_max = int(cal["active_roster_maximum"])
        cap_ceiling = float(cal["salary_cap_ceiling"])
        if count > roster_max:
            errors.append(f"Roster limit exceeded: {count}/{roster_max} active players.")
        if total_aav > cap_ceiling:
            errors.append(f"Salary-cap ceiling breached: ${total_aav:,.2f} / ${cap_ceiling:,.2f}")
        return not errors, errors


class ScoutingFogEngine:
    @staticmethod
    def calculate_current_sigma(observations: int, efficiency: float = 1.0, base_sigma: float = 20.0, lambda_constant: float = 0.35) -> float:
        return base_sigma * math.exp(-(lambda_constant * observations * efficiency))

    @staticmethod
    def get_masked_display(base_value: int, observations: int) -> str:
        sigma = ScoutingFogEngine.calculate_current_sigma(observations)
        return f"{base_value:<3} [Verified]" if sigma <= 0.75 else f"{base_value:^3} (±{int(round(sigma)):<2})"


class DynamicFinancialPool:
    @staticmethod
    def process_daily_cap_accrual(db_path: Path | str = DEFAULT_DB_PATH) -> None:
        conn = _connect(db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            cal = conn.execute(
                "SELECT current_day, accrual_days, salary_cap_ceiling FROM league_calendar WHERE id = 1"
            ).fetchone()
            accrual_days = int(cal["accrual_days"])
            if accrual_days <= 0:
                raise RulesValidationError("accrual_days must be positive")
            for team in conn.execute("SELECT id, tier FROM teams"):
                total_aav = conn.execute(
                    "SELECT COALESCE(SUM(aav), 0) AS total FROM players WHERE team_id = ?", (team["id"],)
                ).fetchone()["total"]
                daily_charge = float(total_aav) / accrual_days
                conn.execute("UPDATE teams SET cash_balance = cash_balance - ? WHERE id = ?", (daily_charge, team["id"]))
                if team["id"] == 1:
                    daily_max = float(cal["salary_cap_ceiling"]) / accrual_days
                    conn.execute(
                        "UPDATE league_calendar SET accrued_margin = accrued_margin + ? WHERE id = 1",
                        (max(0.0, daily_max - daily_charge),),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class ContractAdjustedSurplusValueDesk:
    @staticmethod
    def calculate_player_baseline_asset_value(player: dict[str, Any]) -> float:
        value = sum(player[key] for key in ("shooting", "passing", "positioning", "reflexes", "speed", "checking")) / 6.0
        if player["age"] > 30:
            value -= (player["age"] - 30) * 2.5
        elif player["age"] < 23:
            value += (23 - player["age"]) * 1.5
        return max(10.0, value)

    @staticmethod
    def evaluate_casv_index(player: dict[str, Any], mandate: str) -> float:
        base = ContractAdjustedSurplusValueDesk.calculate_player_baseline_asset_value(player)
        cap_weight = player["aav"] / 1_000_000.0
        return base - cap_weight * 4.5 if mandate == "Moneyball Auditor" else base * 1.35 - cap_weight * 2.0


class AdvisorRiskScoringEngine:
    @staticmethod
    def generate_executive_analysis_report(db_path: Path | str = DEFAULT_DB_PATH) -> str:
        with _connect(db_path) as conn:
            roster = conn.execute("SELECT * FROM players WHERE team_id = 1").fetchall()
            rivals = conn.execute("SELECT * FROM teams WHERE id != 1").fetchall()
            cal = conn.execute("SELECT * FROM league_calendar WHERE id = 1").fetchone()
        total_aav = sum(player["aav"] for player in roster)
        cap_headroom = cal["salary_cap_ceiling"] - total_aav
        overpaid = sum(
            1 for player in roster
            if player["aav"] > 5_000_000
            and ContractAdjustedSurplusValueDesk.calculate_player_baseline_asset_value(dict(player)) < 65.0
        )
        mean_relationship = sum(team["relationship_score"] for team in rivals) / len(rivals) if rivals else 50.0
        risk = min(100.0, max(0.0, total_aav / cal["salary_cap_ceiling"] * 40.0) + overpaid * 12.0 + max(0.0, (100.0 - mean_relationship) * 0.3))
        return (
            f"Season {cal['season_id']} | Rules schema {cal['rules_schema_version']}\n"
            f"Risk score: {risk:.1f}/100\nRoster spending: ${total_aav:,.2f}\n"
            f"Cap headroom: ${cap_headroom:,.2f}\nLow skill-to-AAV assets: {overpaid}"
        )


class ExecutiveTerminalApp:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH, *, season_id: str = DEFAULT_SEASON_ID, accrual_days: int | None = None) -> None:
        self.db_path = Path(db_path)
        if accrual_days is None:
            env_value = os.environ.get("NHL_GM_ACCRUAL_DAYS")
            accrual_days = int(env_value) if env_value else None
        init_database(self.db_path, season_id=season_id, accrual_days=accrual_days)

    def render_dashboard_header(self) -> None:
        context = get_season_context(self.db_path)
        day, accrual_days = int(context["current_day"]), int(context["accrual_days"])
        days_remaining = max(1, accrual_days - day)
        buying_power = context["accrued_margin"] * (accrual_days / float(days_remaining))
        with _connect(self.db_path) as conn:
            team = conn.execute("SELECT cash_balance, gm_trust_score FROM teams WHERE id = 1").fetchone()
        print("=" * 78)
        print(f"NHL GM | Season {context['season_id']} | Day {day}/{accrual_days} | Rules v{context['rules_schema_version']}")
        print(f"Cap: ${context['salary_cap_ceiling']:,.0f} | Accrued deadline buying power: ${buying_power:,.0f}")
        print(f"Cash: ${team['cash_balance']:,.0f} | GM trust: {team['gm_trust_score']:.1f}/100")
        print("=" * 78)

    def advance_simulation_time(self) -> None:
        with _connect(self.db_path) as conn:
            context = conn.execute("SELECT current_day, accrual_days FROM league_calendar WHERE id = 1").fetchone()
            if context["current_day"] >= context["accrual_days"]:
                raise RuntimeError("The cap-accounting calendar is complete.")
            conn.execute("UPDATE league_calendar SET current_day = current_day + 1 WHERE id = 1")
            conn.execute("UPDATE players SET fatigue = MAX(0.0, fatigue - 5.0)")
            conn.execute("UPDATE players SET back_to_back_started = 0 WHERE fatigue = 0.0")
        DynamicFinancialPool.process_daily_cap_accrual(self.db_path)

    def run_main_loop(self) -> None:
        while True:
            self.render_dashboard_header()
            print("[1] Advance one day\n[2] Run advisor report\n[3] Exit")
            choice = input("Select [1-3]: ").strip()
            if choice == "1":
                self.advance_simulation_time()
            elif choice == "2":
                print(AdvisorRiskScoringEngine.generate_executive_analysis_report(self.db_path))
            elif choice == "3":
                return


if __name__ == "__main__":
    try:
        ExecutiveTerminalApp().run_main_loop()
    except RulesValidationError as exc:
        print(f"Rules initialization failed: {exc}", file=sys.stderr)
        print("Set NHL_GM_ACCRUAL_DAYS to the official schedule-derived denominator for a new save.", file=sys.stderr)
        raise SystemExit(2)
