"""Save metadata, franchise selection, and safe alpha reset operations."""

import sqlite3
from contextlib import closing

try:
    from .league_orchestrator import initialize_league
    from .nhl_gm_core import (
        DEFAULT_GAME_SEED,
        SCHEMA_VERSION,
        connect_database,
        init_database,
    )
except ImportError:  # Support direct imports from scripts in src/.
    from league_orchestrator import initialize_league
    from nhl_gm_core import (
        DEFAULT_GAME_SEED,
        SCHEMA_VERSION,
        connect_database,
        init_database,
    )


def get_game_state():
    """Return save metadata and the selectable NHL franchise list."""
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        settings = conn.execute(
            "SELECT * FROM game_settings WHERE id = 1"
        ).fetchone()
        if settings is None:
            raise LookupError("No game save is initialized")
        teams = conn.execute(
            """
            SELECT t.id, t.city, t.name, t.franchise_mandate,
                   t.relationship_score, COUNT(p.id) AS roster_count,
                   COALESCE(SUM(p.aav), 0) AS cap_hit
            FROM teams t
            LEFT JOIN players p ON p.team_id = t.id
            WHERE t.tier = 'NHL'
            GROUP BY t.id
            ORDER BY t.id
            """
        ).fetchall()
        current_day, max_days = conn.execute(
            "SELECT current_day, max_days FROM league_calendar WHERE id = 1"
        ).fetchone()
        completed_games = conn.execute(
            "SELECT COUNT(*) FROM schedule WHERE status = 'completed'"
        ).fetchone()[0]

    setting_data = dict(settings)
    team_data = [dict(team) for team in teams]
    selected = next(
        (team for team in team_data if team["id"] == setting_data["user_team_id"]),
        None,
    )
    return {
        "save": {
            "name": setting_data["save_name"],
            "seed": setting_data["seed"],
            "schema_version": setting_data["schema_version"],
            "current_day": current_day,
            "max_days": max_days,
            "completed_games": completed_games,
            "auto_saved": True,
        },
        "user_team_id": setting_data["user_team_id"],
        "user_team": selected,
        "teams": team_data,
        "requires_reset": (
            setting_data["schema_version"] < SCHEMA_VERSION or len(team_data) < 8
        ),
    }


def select_user_team(team_id):
    """Persist the franchise controlled by the current local save."""
    with closing(connect_database()) as conn:
        team = conn.execute(
            "SELECT id FROM teams WHERE id = ? AND tier = 'NHL'", (team_id,)
        ).fetchone()
        if team is None:
            raise LookupError(f"NHL team {team_id} does not exist")
        conn.execute(
            """
            UPDATE game_settings
            SET user_team_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (team_id,),
        )
        conn.commit()
    return get_game_state()


def reset_game(seed=DEFAULT_GAME_SEED, save_name="Alpha Franchise"):
    """Replace the current local save with a deterministic fresh alpha league."""
    seed = int(seed)
    if seed < 0 or seed > 2_147_483_647:
        raise ValueError("Game seed must be between 0 and 2147483647")
    save_name = str(save_name).strip() or "Alpha Franchise"
    if len(save_name) > 60:
        raise ValueError("Save name cannot exceed 60 characters")

    with closing(connect_database()) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("BEGIN EXCLUSIVE")
        for table in (
            "schedule",
            "standings",
            "trade_history",
            "game_settings",
            "players",
            "teams",
            "league_calendar",
        ):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()

    init_database(seed=seed)
    initialize_league()
    with closing(connect_database()) as conn:
        conn.execute(
            """
            UPDATE game_settings
            SET save_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (save_name,),
        )
        conn.commit()
    return get_game_state()
