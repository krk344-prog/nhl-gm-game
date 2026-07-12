"""Team-specific scouting intelligence, assignments, and player dossiers.

True player attributes remain in the simulation database for internal engines. Every
user-facing scouting view is derived from organization-specific knowledge records,
which retain uncertainty, report history, staleness, and scout disagreement.
"""

from __future__ import annotations

import math
import random
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass

try:
    from .nhl_gm_core import connect_database
except ImportError:  # pragma: no cover - direct src execution
    from nhl_gm_core import connect_database


REGIONS = ("North America", "Scandinavia", "Europe", "Russia")
DEPTH_CONFIG = {
    "quick": {"days": 2, "observations": 1, "cost": 5_000.0, "uncertainty": 1.25},
    "standard": {"days": 5, "observations": 3, "cost": 12_500.0, "uncertainty": 1.0},
    "deep": {"days": 10, "observations": 6, "cost": 25_000.0, "uncertainty": 0.72},
}
FOCUSES = {"overall", "potential", "health", "character", "role_fit"}


@dataclass(frozen=True)
class AccuracyCalibration:
    stronger_scout_id: int
    weaker_scout_id: int
    stronger_mean_absolute_error: float
    weaker_mean_absolute_error: float
    regional_fit_mean_absolute_error: float | None
    regional_mismatch_mean_absolute_error: float | None
    stronger_scout_wins: bool
    regional_specialist_wins: bool | None


def _clamp(value, low=30, high=99):
    return max(low, min(high, int(round(value))))


def _true_overall(player):
    if player["position"] == "G":
        values = (player["positioning"], player["reflexes"], player["speed"])
    else:
        values = (
            player["shooting"],
            player["passing"],
            player["positioning"],
            player["speed"],
            player["checking"],
        )
    return round(sum(values) / len(values))


def _confidence(observations):
    if observations <= 0:
        return "Unknown"
    if observations < 3:
        return "Low"
    if observations < 7:
        return "Moderate"
    if observations < 16:
        return "High"
    return "Verified"


def _ensure_column(conn, table, column, definition):
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _game_seed(conn):
    row = conn.execute("SELECT seed FROM game_settings WHERE id = 1").fetchone()
    return int(row[0]) if row else 7


def _current_day(conn):
    return int(conn.execute("SELECT current_day FROM league_calendar WHERE id = 1").fetchone()[0])


def _seed_error(team_id, player_id, salt, spread):
    raw = ((team_id * 97 + player_id * 53 + salt * 31) % (spread * 2 + 1)) - spread
    return raw if raw != 0 else (1 if (team_id + player_id + salt) % 2 else -1)


def initialize_scouting():
    """Create scouting schema and seed deterministic organization knowledge."""
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        _ensure_column(conn, "players", "true_potential", "INTEGER")
        _ensure_column(conn, "players", "durability", "INTEGER")
        _ensure_column(conn, "players", "character_rating", "INTEGER")
        _ensure_column(conn, "players", "scouting_region", "TEXT")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS scouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                specialty TEXT NOT NULL CHECK(specialty IN ('pro','amateur','regional','goalie','analytics')),
                region TEXT,
                accuracy INTEGER NOT NULL CHECK(accuracy BETWEEN 30 AND 99),
                projection INTEGER NOT NULL CHECK(projection BETWEEN 30 AND 99),
                efficiency INTEGER NOT NULL CHECK(efficiency BETWEEN 30 AND 99),
                communication INTEGER NOT NULL CHECK(communication BETWEEN 30 AND 99),
                bias REAL NOT NULL DEFAULT 0.0,
                workload_capacity INTEGER NOT NULL DEFAULT 3,
                salary REAL NOT NULL,
                contract_years INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );

            CREATE TABLE IF NOT EXISTS team_player_knowledge (
                team_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                observations INTEGER NOT NULL DEFAULT 0,
                current_estimate INTEGER NOT NULL,
                current_low INTEGER NOT NULL,
                current_high INTEGER NOT NULL,
                potential_estimate INTEGER NOT NULL,
                potential_low INTEGER NOT NULL,
                potential_high INTEGER NOT NULL,
                confidence TEXT NOT NULL,
                health_confidence TEXT NOT NULL DEFAULT 'Unknown',
                character_confidence TEXT NOT NULL DEFAULT 'Unknown',
                role_fit_confidence TEXT NOT NULL DEFAULT 'Unknown',
                health_risk TEXT,
                character_summary TEXT,
                role_fit_summary TEXT,
                last_scouted_day INTEGER,
                report_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(team_id, player_id),
                FOREIGN KEY(team_id) REFERENCES teams(id),
                FOREIGN KEY(player_id) REFERENCES players(id)
            );

            CREATE TABLE IF NOT EXISTS scouting_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                scout_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                focus TEXT NOT NULL CHECK(focus IN ('overall','potential','health','character','role_fit')),
                depth TEXT NOT NULL CHECK(depth IN ('quick','standard','deep')),
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','cancelled')),
                assigned_day INTEGER NOT NULL,
                due_day INTEGER NOT NULL,
                completed_day INTEGER,
                observations INTEGER NOT NULL,
                cost REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(team_id) REFERENCES teams(id),
                FOREIGN KEY(scout_id) REFERENCES scouts(id),
                FOREIGN KEY(player_id) REFERENCES players(id)
            );

            CREATE TABLE IF NOT EXISTS scouting_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                scout_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                report_day INTEGER NOT NULL,
                focus TEXT NOT NULL,
                confidence TEXT NOT NULL,
                quality_score REAL NOT NULL,
                current_estimate INTEGER NOT NULL,
                current_low INTEGER NOT NULL,
                current_high INTEGER NOT NULL,
                potential_estimate INTEGER NOT NULL,
                potential_low INTEGER NOT NULL,
                potential_high INTEGER NOT NULL,
                health_risk TEXT,
                character_summary TEXT,
                role_fit_summary TEXT,
                notes TEXT NOT NULL,
                FOREIGN KEY(assignment_id) REFERENCES scouting_assignments(id),
                FOREIGN KEY(team_id) REFERENCES teams(id),
                FOREIGN KEY(scout_id) REFERENCES scouts(id),
                FOREIGN KEY(player_id) REFERENCES players(id)
            );

            CREATE INDEX IF NOT EXISTS idx_scouting_assignments_due
                ON scouting_assignments(status, due_day);
            CREATE INDEX IF NOT EXISTS idx_scouting_reports_team_player
                ON scouting_reports(team_id, player_id, report_day DESC);
            """
        )

        seed = _game_seed(conn)
        players = [dict(row) for row in conn.execute("SELECT * FROM players ORDER BY id")]
        for player in players:
            overall = _true_overall(player)
            if player.get("true_potential") is None:
                age_upside = max(0, 25 - player["age"]) * 2
                jitter = ((player["id"] * 37 + seed * 17) % 13) - 4
                potential = _clamp(max(overall, overall + age_upside + jitter), 40, 99)
                durability = _clamp(52 + ((player["id"] * 19 + seed) % 43), 45, 96)
                character = _clamp(48 + ((player["id"] * 23 + seed * 3) % 47), 40, 97)
                region = REGIONS[(player["id"] + seed) % len(REGIONS)]
                conn.execute(
                    """
                    UPDATE players
                    SET true_potential = ?, durability = ?, character_rating = ?, scouting_region = ?
                    WHERE id = ?
                    """,
                    (potential, durability, character, region, player["id"]),
                )
                player.update(
                    true_potential=potential,
                    durability=durability,
                    character_rating=character,
                    scouting_region=region,
                )

        teams = [dict(row) for row in conn.execute("SELECT * FROM teams WHERE tier = 'NHL' ORDER BY id")]
        scout_names = (
            "Morgan Ellis", "Alex Mercer", "Jordan Price", "Casey Novak", "Taylor Lund",
            "Riley Grant", "Cameron Ward", "Parker Shaw", "Drew Nilsson", "Avery Cole",
        )
        specialties = ("pro", "amateur", "regional", "goalie", "analytics")
        for team in teams:
            existing = conn.execute("SELECT COUNT(*) FROM scouts WHERE team_id = ?", (team["id"],)).fetchone()[0]
            if existing:
                continue
            for index, specialty in enumerate(specialties):
                rating_seed = seed + team["id"] * 101 + index * 29
                accuracy = 62 + rating_seed % 27
                projection = 58 + (rating_seed * 3) % 31
                efficiency = 60 + (rating_seed * 5) % 29
                communication = 57 + (rating_seed * 7) % 33
                bias = (((rating_seed * 11) % 13) - 6) / 2.0
                capacity = 2 + (efficiency >= 72) + (efficiency >= 84)
                region = REGIONS[(team["id"] + index) % len(REGIONS)] if specialty == "regional" else None
                conn.execute(
                    """
                    INSERT INTO scouts (
                        team_id, name, specialty, region, accuracy, projection,
                        efficiency, communication, bias, workload_capacity,
                        salary, contract_years
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        team["id"],
                        scout_names[(team["id"] * 3 + index) % len(scout_names)],
                        specialty,
                        region,
                        accuracy,
                        projection,
                        efficiency,
                        communication,
                        bias,
                        capacity,
                        150_000.0 + (accuracy + projection) * 2_000.0,
                        1 + (rating_seed % 4),
                    ),
                )

        players = [dict(row) for row in conn.execute("SELECT * FROM players ORDER BY id")]
        for team in teams:
            for player in players:
                exists = conn.execute(
                    "SELECT 1 FROM team_player_knowledge WHERE team_id = ? AND player_id = ?",
                    (team["id"], player["id"]),
                ).fetchone()
                if exists:
                    continue
                own_player = player["team_id"] == team["id"]
                observations = 6 if own_player else 0
                current = _clamp(_true_overall(player) + _seed_error(team["id"], player["id"], 1, 5 if own_player else 9))
                potential = _clamp(player["true_potential"] + _seed_error(team["id"], player["id"], 2, 6 if own_player else 11), 40, 99)
                width = 4 if own_player else 11
                conn.execute(
                    """
                    INSERT INTO team_player_knowledge (
                        team_id, player_id, observations, current_estimate,
                        current_low, current_high, potential_estimate,
                        potential_low, potential_high, confidence,
                        health_confidence, character_confidence, role_fit_confidence,
                        last_scouted_day, report_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        team["id"], player["id"], observations, current,
                        _clamp(current - width), _clamp(current + width), potential,
                        _clamp(potential - width, 40, 99), _clamp(potential + width, 40, 99),
                        _confidence(observations),
                        "Low" if own_player else "Unknown",
                        "Low" if own_player else "Unknown",
                        "Moderate" if own_player else "Unknown",
                        1 if own_player else None,
                    ),
                )
        conn.commit()


def _knowledge_summary(knowledge, player, current_day):
    knowledge = dict(knowledge)
    last_day = knowledge["last_scouted_day"]
    stale = last_day is None or current_day - last_day > 30
    half_width = max(
        knowledge["current_estimate"] - knowledge["current_low"],
        knowledge["current_high"] - knowledge["current_estimate"],
    )
    return {
        "id": player["id"],
        "team_id": player["team_id"],
        "name": player["name"],
        "age": player["age"],
        "position": player["position"],
        "archetype": player["archetype"],
        "aav": player["aav"],
        "contract_years": player["contract_years"],
        "overall": knowledge["current_estimate"],
        "overall_range": {"low": knowledge["current_low"], "high": knowledge["current_high"]},
        "potential": knowledge["potential_estimate"],
        "potential_range": {"low": knowledge["potential_low"], "high": knowledge["potential_high"]},
        "confidence": knowledge["confidence"],
        "scouting_uncertainty": float(half_width),
        "observations": knowledge["observations"],
        "report_count": knowledge["report_count"],
        "last_scouted_day": last_day,
        "stale": stale,
        "health_risk": knowledge["health_risk"],
        "character_summary": knowledge["character_summary"],
        "role_fit_summary": knowledge["role_fit_summary"],
        "health_confidence": knowledge["health_confidence"],
        "character_confidence": knowledge["character_confidence"],
        "role_fit_confidence": knowledge["role_fit_confidence"],
    }


def summarize_player_for_team(cursor, viewer_team_id, player):
    """Return a user-safe player summary without true ratings."""
    if not isinstance(player, dict):
        player = dict(player)
    knowledge = cursor.execute(
        "SELECT * FROM team_player_knowledge WHERE team_id = ? AND player_id = ?",
        (viewer_team_id, player["id"]),
    ).fetchone()
    if knowledge is None:
        raise LookupError(f"No scouting knowledge for team {viewer_team_id} and player {player['id']}")
    return _knowledge_summary(knowledge, player, _current_day(cursor.connection))


def get_team_roster_view(viewer_team_id, roster_team_id=None):
    initialize_scouting()
    roster_team_id = viewer_team_id if roster_team_id is None else roster_team_id
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        viewer = conn.execute("SELECT * FROM teams WHERE id = ?", (viewer_team_id,)).fetchone()
        roster_team = conn.execute("SELECT * FROM teams WHERE id = ?", (roster_team_id,)).fetchone()
        if viewer is None or roster_team is None:
            raise LookupError("Viewer or roster team does not exist")
        rows = conn.execute(
            """
            SELECT * FROM players WHERE team_id = ?
            ORDER BY CASE position WHEN 'F' THEN 1 WHEN 'D' THEN 2 ELSE 3 END, id
            """,
            (roster_team_id,),
        ).fetchall()
        players = [summarize_player_for_team(conn.cursor(), viewer_team_id, row) for row in rows]
    return {
        "team": {"id": roster_team["id"], "name": roster_team["name"], "city": roster_team["city"]},
        "viewer_team_id": viewer_team_id,
        "count": len(players),
        "players": players,
    }


def _active_workload(conn, scout_id):
    return int(conn.execute(
        "SELECT COUNT(*) FROM scouting_assignments WHERE scout_id = ? AND status = 'active'",
        (scout_id,),
    ).fetchone()[0])


def list_scouts(team_id):
    initialize_scouting()
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM scouts WHERE team_id = ? AND active = 1 ORDER BY specialty, id", (team_id,)).fetchall()
        scouts = []
        for row in rows:
            scout = dict(row)
            scout["active_assignments"] = _active_workload(conn, scout["id"])
            scout["available_capacity"] = scout["workload_capacity"] - scout["active_assignments"]
            scouts.append(scout)
    return scouts


def list_assignments(team_id, status=None, limit=100):
    initialize_scouting()
    if limit < 1 or limit > 250:
        raise ValueError("Assignment limit must be between 1 and 250")
    clauses = ["a.team_id = ?"]
    params: list[object] = [team_id]
    if status:
        if status not in {"active", "completed", "cancelled"}:
            raise ValueError("Invalid assignment status")
        clauses.append("a.status = ?")
        params.append(status)
    params.append(limit)
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT a.*, s.name AS scout_name, s.specialty, p.name AS player_name,
                   p.position, p.team_id AS player_team_id
            FROM scouting_assignments a
            JOIN scouts s ON s.id = a.scout_id
            JOIN players p ON p.id = a.player_id
            WHERE {' AND '.join(clauses)}
            ORDER BY CASE a.status WHEN 'active' THEN 1 ELSE 2 END, a.due_day, a.id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def list_reports(team_id, player_id=None, limit=50):
    initialize_scouting()
    if limit < 1 or limit > 250:
        raise ValueError("Report limit must be between 1 and 250")
    clauses = ["r.team_id = ?"]
    params: list[object] = [team_id]
    if player_id is not None:
        clauses.append("r.player_id = ?")
        params.append(player_id)
    params.append(limit)
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT r.*, s.name AS scout_name, s.specialty, p.name AS player_name,
                   p.position, p.team_id AS player_team_id
            FROM scouting_reports r
            JOIN scouts s ON s.id = r.scout_id
            JOIN players p ON p.id = r.player_id
            WHERE {' AND '.join(clauses)}
            ORDER BY r.report_day DESC, r.id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def create_assignment(team_id, scout_id, player_id, focus="overall", depth="standard"):
    initialize_scouting()
    if focus not in FOCUSES:
        raise ValueError("Focus must be overall, potential, health, character, or role_fit")
    if depth not in DEPTH_CONFIG:
        raise ValueError("Depth must be quick, standard, or deep")
    config = DEPTH_CONFIG[depth]
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        scout = conn.execute("SELECT * FROM scouts WHERE id = ? AND active = 1", (scout_id,)).fetchone()
        if scout is None:
            raise LookupError(f"Scout {scout_id} does not exist")
        if scout["team_id"] != team_id:
            raise ValueError("Scout does not belong to the assigning team")
        player = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
        if player is None:
            raise LookupError(f"Player {player_id} does not exist")
        duplicate = conn.execute(
            "SELECT 1 FROM scouting_assignments WHERE team_id = ? AND player_id = ? AND focus = ? AND status = 'active'",
            (team_id, player_id, focus),
        ).fetchone()
        if duplicate:
            raise ValueError("An active assignment already covers that player and focus")
        workload = _active_workload(conn, scout_id)
        if workload >= scout["workload_capacity"]:
            raise ValueError("Scout workload capacity is full")
        day = _current_day(conn)
        due_day = day + config["days"]
        cash = conn.execute("SELECT cash_balance FROM teams WHERE id = ?", (team_id,)).fetchone()
        if cash is None:
            raise LookupError(f"Team {team_id} does not exist")
        if cash[0] < config["cost"]:
            raise ValueError("Insufficient hockey-operations cash for assignment")
        conn.execute("UPDATE teams SET cash_balance = cash_balance - ? WHERE id = ?", (config["cost"], team_id))
        cursor = conn.execute(
            """
            INSERT INTO scouting_assignments (
                team_id, scout_id, player_id, focus, depth, assigned_day,
                due_day, observations, cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (team_id, scout_id, player_id, focus, depth, day, due_day, config["observations"], config["cost"]),
        )
        assignment_id = cursor.lastrowid
        conn.commit()
    return next(item for item in list_assignments(team_id) if item["id"] == assignment_id)


def _quality_score(conn, scout, player, assignment):
    active_count = _active_workload(conn, scout["id"])
    primary = scout["projection"] if assignment["focus"] == "potential" else scout["accuracy"]
    quality = primary * 0.62 + scout["communication"] * 0.15 + scout["efficiency"] * 0.13
    specialty_bonus = 0.0
    if scout["specialty"] == "goalie" and player["position"] == "G":
        specialty_bonus += 10.0
    if scout["specialty"] == "regional" and scout["region"] == player["scouting_region"]:
        specialty_bonus += 12.0
    if scout["specialty"] == "amateur" and player["age"] <= 22:
        specialty_bonus += 8.0
    if scout["specialty"] == "pro" and player["age"] >= 23:
        specialty_bonus += 7.0
    if scout["specialty"] == "analytics" and assignment["focus"] in {"overall", "role_fit"}:
        specialty_bonus += 7.0
    workload_penalty = max(0, active_count - 1) * 4.0
    return max(0.28, min(0.96, (quality + specialty_bonus - workload_penalty) / 100.0))


def _descriptors(player, rng):
    durability = player["durability"] + rng.randint(-5, 5)
    if durability >= 82:
        health = "Low projected availability risk"
    elif durability >= 66:
        health = "Average projected availability risk"
    else:
        health = "Elevated projected availability risk"
    character = player["character_rating"] + rng.randint(-7, 7)
    if character >= 82:
        character_text = "Strong preparation, accountability, and leadership indicators"
    elif character >= 64:
        character_text = "Generally reliable habits with limited leadership evidence"
    else:
        character_text = "Inconsistent preparation or adaptability indicators"
    return health, character_text


def _role_fit(player, mandate):
    archetype = player["archetype"]
    if mandate == "Win-Now Titan":
        fit = "Strong" if player["age"] >= 24 or "Elite" in archetype else "Developmental"
    else:
        fit = "Strong" if player["age"] <= 25 or player["aav"] <= 2_000_000 else "Conditional"
    return f"{fit} fit for {mandate}: {archetype}"


def _observation_estimate(true_value, scout, player, assignment, rng):
    quality = _quality_score(assignment["_conn"], scout, player, assignment)
    depth_factor = DEPTH_CONFIG[assignment["depth"]]["uncertainty"]
    deviation = max(1.2, (1.0 - quality) * 13.0 * depth_factor)
    estimate = _clamp(true_value + rng.gauss(scout["bias"] * 0.35, deviation), 30, 99)
    width = max(1, round((1.0 - quality) * 11.0 * depth_factor + 1.0))
    return estimate, width, quality


def _complete_assignment(conn, assignment, day):
    scout = dict(conn.execute("SELECT * FROM scouts WHERE id = ?", (assignment["scout_id"],)).fetchone())
    player = dict(conn.execute("SELECT * FROM players WHERE id = ?", (assignment["player_id"],)).fetchone())
    knowledge = dict(conn.execute(
        "SELECT * FROM team_player_knowledge WHERE team_id = ? AND player_id = ?",
        (assignment["team_id"], assignment["player_id"]),
    ).fetchone())
    mandate = conn.execute("SELECT franchise_mandate FROM teams WHERE id = ?", (assignment["team_id"],)).fetchone()[0]
    seed = _game_seed(conn) + assignment["id"] * 7_919 + day * 104_729
    rng = random.Random(seed)
    assignment_with_conn = dict(assignment)
    assignment_with_conn["_conn"] = conn
    current_estimate, current_width, quality = _observation_estimate(
        _true_overall(player), scout, player, assignment_with_conn, rng
    )
    potential_estimate, potential_width, _ = _observation_estimate(
        player["true_potential"], scout, player, assignment_with_conn, rng
    )
    health, character = _descriptors(player, rng)
    role_fit = _role_fit(player, mandate)
    new_observations = knowledge["observations"] + assignment["observations"]
    weight_old = knowledge["observations"]
    weight_new = assignment["observations"]
    denominator = max(1, weight_old + weight_new)
    combined_current = _clamp((knowledge["current_estimate"] * weight_old + current_estimate * weight_new) / denominator)
    combined_potential = _clamp((knowledge["potential_estimate"] * weight_old + potential_estimate * weight_new) / denominator, 40, 99)
    learned_width = max(1, round(12.0 * math.exp(-0.13 * new_observations) + (1.0 - quality) * 3.0))
    current_width = max(1, min(current_width, learned_width))
    potential_width = max(1, min(potential_width, learned_width + 1))
    confidence = _confidence(new_observations)
    focus_confidence = confidence if assignment["focus"] in {"health", "character", "role_fit"} else None
    health_confidence = focus_confidence if assignment["focus"] == "health" else knowledge["health_confidence"]
    character_confidence = focus_confidence if assignment["focus"] == "character" else knowledge["character_confidence"]
    role_fit_confidence = focus_confidence if assignment["focus"] == "role_fit" else knowledge["role_fit_confidence"]
    notes = (
        f"{scout['name']} completed a {assignment['depth']} {assignment['focus']} review. "
        f"Report quality {quality:.2f}; estimates retain a non-zero uncertainty range."
    )
    report_cursor = conn.execute(
        """
        INSERT INTO scouting_reports (
            assignment_id, team_id, scout_id, player_id, report_day, focus,
            confidence, quality_score, current_estimate, current_low,
            current_high, potential_estimate, potential_low, potential_high,
            health_risk, character_summary, role_fit_summary, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            assignment["id"], assignment["team_id"], assignment["scout_id"], assignment["player_id"], day,
            assignment["focus"], confidence, quality, current_estimate,
            _clamp(current_estimate - current_width), _clamp(current_estimate + current_width),
            potential_estimate, _clamp(potential_estimate - potential_width, 40, 99),
            _clamp(potential_estimate + potential_width, 40, 99), health, character, role_fit, notes,
        ),
    )
    conn.execute(
        """
        UPDATE team_player_knowledge
        SET observations = ?, current_estimate = ?, current_low = ?, current_high = ?,
            potential_estimate = ?, potential_low = ?, potential_high = ?,
            confidence = ?, health_confidence = ?, character_confidence = ?,
            role_fit_confidence = ?, health_risk = ?, character_summary = ?,
            role_fit_summary = ?, last_scouted_day = ?, report_count = report_count + 1
        WHERE team_id = ? AND player_id = ?
        """,
        (
            new_observations, combined_current, _clamp(combined_current - learned_width),
            _clamp(combined_current + learned_width), combined_potential,
            _clamp(combined_potential - learned_width - 1, 40, 99),
            _clamp(combined_potential + learned_width + 1, 40, 99), confidence,
            health_confidence, character_confidence, role_fit_confidence,
            health if assignment["focus"] == "health" or knowledge["health_risk"] is None else knowledge["health_risk"],
            character if assignment["focus"] == "character" or knowledge["character_summary"] is None else knowledge["character_summary"],
            role_fit if assignment["focus"] == "role_fit" or knowledge["role_fit_summary"] is None else knowledge["role_fit_summary"],
            day, assignment["team_id"], assignment["player_id"],
        ),
    )
    conn.execute(
        "UPDATE scouting_assignments SET status = 'completed', completed_day = ? WHERE id = ?",
        (day, assignment["id"]),
    )
    return report_cursor.lastrowid


def process_scouting_day(day):
    initialize_scouting()
    completed_ids = []
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        assignments = conn.execute(
            "SELECT * FROM scouting_assignments WHERE status = 'active' AND due_day <= ? ORDER BY due_day, id",
            (day,),
        ).fetchall()
        for row in assignments:
            completed_ids.append(_complete_assignment(conn, dict(row), day))
        conn.commit()
    return {"completed_report_ids": completed_ids, "completed_count": len(completed_ids)}


def get_player_dossier(team_id, player_id):
    initialize_scouting()
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        player = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
        if player is None:
            raise LookupError(f"Player {player_id} does not exist")
        summary = summarize_player_for_team(conn.cursor(), team_id, player)
        active = conn.execute(
            """
            SELECT a.*, s.name AS scout_name FROM scouting_assignments a
            JOIN scouts s ON s.id = a.scout_id
            WHERE a.team_id = ? AND a.player_id = ? AND a.status = 'active'
            ORDER BY a.due_day
            """,
            (team_id, player_id),
        ).fetchall()
    return {"player": summary, "active_assignments": [dict(row) for row in active], "reports": list_reports(team_id, player_id=player_id, limit=20)}


def get_scouting_center(team_id):
    initialize_scouting()
    scouts = list_scouts(team_id)
    assignments = list_assignments(team_id, limit=100)
    reports = list_reports(team_id, limit=20)
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        team = conn.execute("SELECT id, city, name, cash_balance FROM teams WHERE id = ?", (team_id,)).fetchone()
        if team is None:
            raise LookupError(f"Team {team_id} does not exist")
        rows = conn.execute(
            """
            SELECT p.*, k.confidence, k.current_estimate, k.current_low, k.current_high,
                   k.potential_estimate, k.potential_low, k.potential_high,
                   k.observations, k.last_scouted_day, k.report_count,
                   k.health_risk, k.character_summary, k.role_fit_summary,
                   k.health_confidence, k.character_confidence, k.role_fit_confidence
            FROM team_player_knowledge k
            JOIN players p ON p.id = k.player_id
            WHERE k.team_id = ? AND p.team_id != ?
            ORDER BY k.observations ASC, k.potential_estimate DESC, p.age ASC
            LIMIT 30
            """,
            (team_id, team_id),
        ).fetchall()
        board = [_knowledge_summary(row, row, _current_day(conn)) for row in rows]
    return {
        "team": dict(team),
        "department": {
            "scout_count": len(scouts),
            "active_assignments": sum(item["status"] == "active" for item in assignments),
            "completed_assignments": sum(item["status"] == "completed" for item in assignments),
            "available_capacity": sum(max(0, scout["available_capacity"]) for scout in scouts),
        },
        "scouts": scouts,
        "assignments": assignments,
        "recent_reports": reports,
        "priority_board": board,
        "assignment_options": {"focuses": sorted(FOCUSES), "depths": DEPTH_CONFIG},
    }


def _simulate_error(scout, player, specialty_fit, salt):
    rng = random.Random(scout["id"] * 100_003 + player["id"] * 7_919 + salt)
    quality = (scout["accuracy"] * 0.70 + scout["communication"] * 0.15 + scout["efficiency"] * 0.15) / 100.0
    if specialty_fit:
        quality = min(0.96, quality + 0.10)
    deviation = max(1.2, (1.0 - quality) * 13.0)
    estimate = _clamp(_true_overall(player) + rng.gauss(scout["bias"] * 0.35, deviation))
    return abs(estimate - _true_overall(player))


def run_accuracy_calibration(team_id, samples=5):
    """Compare scout accuracy and regional fit over deterministic observations."""
    initialize_scouting()
    if samples < 1 or samples > 100:
        raise ValueError("Samples must be between 1 and 100")
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        scouts = [dict(row) for row in conn.execute("SELECT * FROM scouts WHERE team_id = ?", (team_id,))]
        players = [dict(row) for row in conn.execute("SELECT * FROM players WHERE team_id != ? ORDER BY id", (team_id,))]
    if len(scouts) < 2 or not players:
        raise ValueError("Calibration requires at least two scouts and an external player pool")
    ranked = sorted(scouts, key=lambda s: (s["accuracy"], s["communication"], s["efficiency"]), reverse=True)
    strong, weak = ranked[0], ranked[-1]
    strong_errors = []
    weak_errors = []
    for salt in range(samples):
        for player in players:
            strong_errors.append(_simulate_error(strong, player, False, salt))
            weak_errors.append(_simulate_error(weak, player, False, salt))
    regional = next((scout for scout in scouts if scout["specialty"] == "regional"), None)
    fit_error = mismatch_error = None
    if regional:
        fit_players = [player for player in players if player["scouting_region"] == regional["region"]]
        mismatch_players = [player for player in players if player["scouting_region"] != regional["region"]]
        fit_values = [_simulate_error(regional, player, True, salt) for salt in range(samples) for player in fit_players]
        mismatch_values = [_simulate_error(regional, player, False, salt) for salt in range(samples) for player in mismatch_players]
        fit_error = round(sum(fit_values) / len(fit_values), 3) if fit_values else None
        mismatch_error = round(sum(mismatch_values) / len(mismatch_values), 3) if mismatch_values else None
    result = AccuracyCalibration(
        stronger_scout_id=strong["id"],
        weaker_scout_id=weak["id"],
        stronger_mean_absolute_error=round(sum(strong_errors) / len(strong_errors), 3),
        weaker_mean_absolute_error=round(sum(weak_errors) / len(weak_errors), 3),
        regional_fit_mean_absolute_error=fit_error,
        regional_mismatch_mean_absolute_error=mismatch_error,
        stronger_scout_wins=(sum(strong_errors) / len(strong_errors)) < (sum(weak_errors) / len(weak_errors)),
        regional_specialist_wins=(fit_error < mismatch_error) if fit_error is not None and mismatch_error is not None else None,
    )
    return asdict(result)
