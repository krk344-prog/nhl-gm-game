"""Persistent regular-season schedule, standings, daily simulation, and scouting."""

import sqlite3
from contextlib import closing

try:
    from .nhl_gm_core import DynamicFinancialPool, TacticalMatchSimulator, connect_database
except ImportError:  # pragma: no cover
    from nhl_gm_core import DynamicFinancialPool, TacticalMatchSimulator, connect_database

REGULAR_SEASON_GAMES = 82


def initialize_league():
    """Create league-loop tables and seed an idempotent regular-season schedule."""
    with closing(connect_database()) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS standings (
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
            );

            CREATE TABLE IF NOT EXISTS schedule (
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
            );
            """
        )
        team_ids = [row[0] for row in conn.execute(
            "SELECT id FROM teams WHERE tier = 'NHL' ORDER BY id"
        ).fetchall()]
        conn.executemany(
            "INSERT OR IGNORE INTO standings (team_id) VALUES (?)",
            [(team_id,) for team_id in team_ids],
        )
        if conn.execute("SELECT COUNT(*) FROM schedule").fetchone()[0] == 0:
            _seed_schedule(conn, team_ids)
        conn.commit()
    try:
        from .scouting_service import initialize_scouting
    except ImportError:  # pragma: no cover
        from scouting_service import initialize_scouting
    initialize_scouting()


def _round_robin_rounds(team_ids):
    participants = list(team_ids)
    if len(participants) % 2:
        participants.append(None)
    if len(participants) < 2:
        return []
    rounds = []
    for _ in range(len(participants) - 1):
        pairings = []
        half = len(participants) // 2
        for index in range(half):
            left = participants[index]
            right = participants[-(index + 1)]
            if left is not None and right is not None:
                pairings.append((left, right))
        rounds.append(pairings)
        participants = [participants[0], participants[-1], *participants[1:-1]]
    return rounds


def _orient_balanced_home_games(games):
    """Orient an even-degree matchup graph into exact home/away balance."""
    adjacency = {}
    for edge_id, (_, first, second) in enumerate(games):
        adjacency.setdefault(first, []).append(edge_id)
        adjacency.setdefault(second, []).append(edge_id)
    unused = set(range(len(games)))
    oriented = {}
    while unused:
        first_edge = min(unused)
        start = games[first_edge][1]
        current = start
        while True:
            candidates = [edge_id for edge_id in adjacency[current] if edge_id in unused]
            if not candidates:
                raise ValueError("Schedule graph could not be decomposed into closed cycles")
            edge_id = min(candidates)
            unused.remove(edge_id)
            _, first, second = games[edge_id]
            opponent = second if first == current else first
            oriented[edge_id] = (current, opponent)
            current = opponent
            if current == start:
                break
    return oriented


def _seed_schedule(conn, team_ids):
    rounds = _round_robin_rounds(team_ids)
    if not rounds:
        return
    max_day = conn.execute(
        "SELECT max_days FROM league_calendar WHERE id = 1"
    ).fetchone()[0]
    games_scheduled = {team_id: 0 for team_id in team_ids}
    games = []
    day = 2
    round_index = 0
    while day <= max_day and min(games_scheduled.values()) < REGULAR_SEASON_GAMES:
        for first, second in rounds[round_index % len(rounds)]:
            if games_scheduled[first] >= REGULAR_SEASON_GAMES or games_scheduled[second] >= REGULAR_SEASON_GAMES:
                continue
            games.append((day, first, second))
            games_scheduled[first] += 1
            games_scheduled[second] += 1
        day += 2
        round_index += 1
    oriented = _orient_balanced_home_games(games)
    conn.executemany(
        "INSERT INTO schedule (day, home_team_id, away_team_id) VALUES (?, ?, ?)",
        [(day, *oriented[edge_id]) for edge_id, (day, _, _) in enumerate(games)],
    )


def get_standings():
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT s.*, t.name, t.city,
                   (s.goals_for - s.goals_against) AS goal_differential
            FROM standings s
            JOIN teams t ON t.id = s.team_id
            ORDER BY s.points DESC, s.wins DESC, goal_differential DESC, t.name
            """
        ).fetchall()
    return {"standings": [dict(row) for row in rows]}


def get_schedule(day=None, team_id=None, limit=20):
    clauses = []
    parameters = []
    if day is not None:
        clauses.append("s.day = ?")
        parameters.append(day)
    if team_id is not None:
        clauses.append("(s.home_team_id = ? OR s.away_team_id = ?)")
        parameters.extend([team_id, team_id])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    parameters.append(max(1, min(200, limit)))
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT s.*, home.name AS home_team, away.name AS away_team
            FROM schedule s
            JOIN teams home ON home.id = s.home_team_id
            JOIN teams away ON away.id = s.away_team_id
            {where}
            ORDER BY s.day, s.id
            LIMIT ?
            """,
            parameters,
        ).fetchall()
    return {"games": [dict(row) for row in rows]}


def _next_streak(current, outcome):
    if current.startswith(outcome):
        try:
            return f"{outcome}{int(current[len(outcome):]) + 1}"
        except ValueError:
            pass
    return f"{outcome}1"


def _record_team_result(conn, team_id, goals_for, goals_against, won, overtime_loss, day):
    current_streak = conn.execute(
        "SELECT streak FROM standings WHERE team_id = ?", (team_id,)
    ).fetchone()[0]
    outcome = "W" if won else "OTL" if overtime_loss else "L"
    conn.execute(
        """
        UPDATE standings
        SET games_played = games_played + 1,
            wins = wins + ?, losses = losses + ?,
            overtime_losses = overtime_losses + ?, points = points + ?,
            goals_for = goals_for + ?, goals_against = goals_against + ?,
            streak = ?, updated_day = ?
        WHERE team_id = ?
        """,
        (
            int(won), int(not won and not overtime_loss), int(overtime_loss),
            2 if won else 1 if overtime_loss else 0,
            goals_for, goals_against, _next_streak(current_streak, outcome), day, team_id,
        ),
    )


def _release_game_claim(game_id):
    with closing(connect_database()) as conn:
        conn.execute(
            "UPDATE schedule SET status = 'scheduled' WHERE id = ? AND status = 'in_progress'",
            (game_id,),
        )
        conn.commit()


def simulate_scheduled_day(day):
    games = get_schedule(day=day, limit=200)["games"]
    completed = []
    for game in games:
        with closing(connect_database()) as conn:
            claimed = conn.execute(
                "UPDATE schedule SET status = 'in_progress' WHERE id = ? AND status = 'scheduled'",
                (game["id"],),
            ).rowcount
            conn.commit()
        if not claimed:
            continue
        try:
            result = TacticalMatchSimulator(
                game["home_team_id"], game["away_team_id"]
            ).execute_match_simulation(structured=True, persist_fatigue=False)
            if result["status"] != "completed":
                raise RuntimeError(result["error"])
            home_won = result["home_score"] > result["away_score"]
            with closing(connect_database()) as conn:
                conn.execute(
                    """
                    UPDATE schedule
                    SET status = 'completed', home_score = ?, away_score = ?,
                        overtime = ?, result_log = ?
                    WHERE id = ?
                    """,
                    (
                        result["home_score"], result["away_score"], int(result["overtime"]),
                        result["log"], game["id"],
                    ),
                )
                conn.executemany(
                    "UPDATE players SET fatigue = fatigue + 25.0, back_to_back_started = 1 WHERE id = ?",
                    [(result["home_goalie_id"],), (result["away_goalie_id"],)],
                )
                _record_team_result(
                    conn, game["home_team_id"], result["home_score"], result["away_score"],
                    home_won, result["overtime"] and not home_won, day,
                )
                _record_team_result(
                    conn, game["away_team_id"], result["away_score"], result["home_score"],
                    not home_won, result["overtime"] and home_won, day,
                )
                conn.commit()
        except Exception:
            _release_game_claim(game["id"])
            raise
        completed.append(
            {
                "id": game["id"], "day": day,
                "home_team_id": game["home_team_id"], "home_team": game["home_team"],
                "home_score": result["home_score"],
                "away_team_id": game["away_team_id"], "away_team": game["away_team"],
                "away_score": result["away_score"], "overtime": result["overtime"],
            }
        )
    return completed


def advance_day():
    """Advance one day, settle finances, scouting, games, and standings."""
    with closing(connect_database()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        current_day, max_days = conn.execute(
            "SELECT current_day, max_days FROM league_calendar WHERE id = 1"
        ).fetchone()
        if current_day >= max_days:
            conn.rollback()
            raise ValueError("The regular-season calendar is already complete")
        new_day = current_day + 1
        conn.execute("UPDATE league_calendar SET current_day = ? WHERE id = 1", (new_day,))
        conn.execute("UPDATE players SET fatigue = MAX(0.0, fatigue - 5.0)")
        conn.execute("UPDATE players SET back_to_back_started = 0 WHERE fatigue = 0.0")
        conn.commit()
    DynamicFinancialPool.process_daily_cap_accrual()
    try:
        from .scouting_service import process_scouting_day
    except ImportError:  # pragma: no cover
        from scouting_service import process_scouting_day
    scouting = process_scouting_day(new_day)
    completed_games = simulate_scheduled_day(new_day)
    return {
        "calendar": {"current_day": new_day, "max_days": max_days},
        "games": completed_games,
        "scouting": scouting,
        **get_standings(),
    }
