"""Structured trade-market evaluation and transactional player swaps."""

import sqlite3
from contextlib import closing

try:
    from .nhl_gm_core import ContractAdjustedSurplusValueDesk, connect_database
except ImportError:  # Support direct imports from scripts in src/.
    from nhl_gm_core import ContractAdjustedSurplusValueDesk, connect_database


def _get_team(cursor, team_id):
    row = cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    if row is None:
        raise LookupError(f"Team {team_id} does not exist")
    return dict(row)


def _get_player(cursor, player_id):
    row = cursor.execute(
        "SELECT * FROM players WHERE id = ?", (player_id,)
    ).fetchone()
    if row is None:
        raise LookupError(f"Player {player_id} does not exist")
    return dict(row)


def _player_overall(player):
    if player["position"] == "G":
        values = [player["positioning"], player["reflexes"], player["speed"]]
    else:
        values = [
            player["shooting"],
            player["passing"],
            player["positioning"],
            player["speed"],
            player["checking"],
        ]
    return round(sum(values) / len(values))


def _summarize_player(player, value=None):
    summary = {
        "id": player["id"],
        "team_id": player["team_id"],
        "name": player["name"],
        "age": player["age"],
        "position": player["position"],
        "archetype": player["archetype"],
        "overall": _player_overall(player),
        "aav": player["aav"],
        "contract_years": player["contract_years"],
    }
    if value is not None:
        summary["casv"] = round(value, 2)
    return summary


def _validate_trade_parties(
    cursor, user_team_id, offered_player_id, target_team_id, target_player_id
):
    if user_team_id == target_team_id:
        raise ValueError("A trade requires two different teams")

    user_team = _get_team(cursor, user_team_id)
    target_team = _get_team(cursor, target_team_id)
    if user_team["tier"] != "NHL" or target_team["tier"] != "NHL":
        raise ValueError("Trades are currently limited to NHL teams")

    offered_player = _get_player(cursor, offered_player_id)
    target_player = _get_player(cursor, target_player_id)
    if offered_player["team_id"] != user_team_id:
        raise ValueError(
            f"Player {offered_player_id} is not on team {user_team_id}"
        )
    if target_player["team_id"] != target_team_id:
        raise ValueError(
            f"Player {target_player_id} is not on team {target_team_id}"
        )
    return user_team, offered_player, target_team, target_player


def _evaluate_with_cursor(
    cursor, user_team_id, offered_player_id, target_team_id, target_player_id
):
    user_team, offered_player, target_team, target_player = _validate_trade_parties(
        cursor,
        user_team_id,
        offered_player_id,
        target_team_id,
        target_player_id,
    )
    mandate = target_team["franchise_mandate"]
    offered_value = ContractAdjustedSurplusValueDesk.evaluate_casv_index(
        offered_player, mandate
    )
    target_value = ContractAdjustedSurplusValueDesk.evaluate_casv_index(
        target_player, mandate
    )
    relationship_score = target_team["relationship_score"]
    premium_multiplier = 1.0 + ((100.0 - relationship_score) / 200.0)
    required_value = target_value * premium_multiplier
    accepted = offered_value >= required_value
    user_value_delta = target_value - offered_value

    if premium_multiplier <= 1.10:
        difficulty = "LOW"
    elif premium_multiplier <= 1.20:
        difficulty = "MEDIUM"
    elif premium_multiplier <= 1.30:
        difficulty = "MEDIUM-HIGH"
    else:
        difficulty = "HIGH"

    return {
        "status": "evaluated",
        "accepted": accepted,
        "decision": "LIKELY ACCEPT" if accepted else "LIKELY REJECT",
        "user_team": {
            "id": user_team["id"],
            "name": user_team["name"],
            "city": user_team["city"],
        },
        "target_team": {
            "id": target_team["id"],
            "name": target_team["name"],
            "city": target_team["city"],
            "franchise_mandate": mandate,
        },
        "offered": _summarize_player(offered_player, offered_value),
        "target": _summarize_player(target_player, target_value),
        "relationship_score": round(relationship_score, 1),
        "premium_multiplier": round(premium_multiplier, 3),
        "required_value": round(required_value, 2),
        "value_gap_to_acceptance": round(offered_value - required_value, 2),
        "user_value_delta": round(user_value_delta, 2),
        "difficulty": difficulty,
    }


def evaluate_trade(
    user_team_id, offered_player_id, target_team_id, target_player_id
):
    """Return a structured, non-mutating CASV evaluation for a one-for-one trade."""
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        return _evaluate_with_cursor(
            conn.cursor(),
            user_team_id,
            offered_player_id,
            target_team_id,
            target_player_id,
        )


def get_trade_market(user_team_id, target_team_id=None):
    """Return selectable NHL players and the current rival relationship context."""
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        user_team = _get_team(cursor, user_team_id)
        if user_team["tier"] != "NHL":
            raise ValueError("The user-controlled trade team must be an NHL team")

        rival_rows = cursor.execute(
            "SELECT * FROM teams WHERE tier = 'NHL' AND id != ? ORDER BY id",
            (user_team_id,),
        ).fetchall()
        if not rival_rows:
            raise ValueError("No NHL trade partners are available")
        rivals = [dict(row) for row in rival_rows]
        if target_team_id is None:
            target_team = rivals[0]
        else:
            target_team = next(
                (team for team in rivals if team["id"] == target_team_id), None
            )
            if target_team is None:
                raise ValueError(f"Team {target_team_id} is not an available trade partner")

        def roster(team_id):
            rows = cursor.execute(
                """
                SELECT * FROM players
                WHERE team_id = ?
                ORDER BY CASE position WHEN 'F' THEN 1 WHEN 'D' THEN 2 ELSE 3 END,
                         id
                """,
                (team_id,),
            ).fetchall()
            return [_summarize_player(dict(row)) for row in rows]

        return {
            "user_team": {
                "id": user_team["id"],
                "name": user_team["name"],
                "city": user_team["city"],
            },
            "rivals": [
                {
                    "id": team["id"],
                    "name": team["name"],
                    "city": team["city"],
                    "franchise_mandate": team["franchise_mandate"],
                    "relationship_score": team["relationship_score"],
                }
                for team in rivals
            ],
            "target_team": {
                "id": target_team["id"],
                "name": target_team["name"],
                "city": target_team["city"],
                "franchise_mandate": target_team["franchise_mandate"],
                "relationship_score": target_team["relationship_score"],
            },
            "offered_players": roster(user_team_id),
            "target_players": roster(target_team["id"]),
        }


def _roster_issues(cursor, team_id):
    count, total_aav = cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(aav), 0) FROM players WHERE team_id = ?",
        (team_id,),
    ).fetchone()
    cap_ceiling = cursor.execute(
        "SELECT salary_cap_ceiling FROM league_calendar WHERE id = 1"
    ).fetchone()[0]
    issues = []
    if count > 23:
        issues.append(f"Roster size exceeds 23 players ({count}/23)")
    if total_aav > cap_ceiling:
        issues.append(
            f"Cap ceiling exceeded (${total_aav:,.0f} / ${cap_ceiling:,.0f})"
        )
    return issues


def _record_history(cursor, evaluation, status, reason):
    day = cursor.execute(
        "SELECT current_day FROM league_calendar WHERE id = 1"
    ).fetchone()[0]
    cursor.execute(
        """
        INSERT INTO trade_history (
            day, user_team_id, target_team_id, offered_player_id,
            target_player_id, offered_value, target_value, required_value,
            relationship_score, status, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            day,
            evaluation["user_team"]["id"],
            evaluation["target_team"]["id"],
            evaluation["offered"]["id"],
            evaluation["target"]["id"],
            evaluation["offered"]["casv"],
            evaluation["target"]["casv"],
            evaluation["required_value"],
            evaluation["relationship_score"],
            status,
            reason,
        ),
    )
    return cursor.lastrowid


def execute_trade(user_team_id, offered_player_id, target_team_id, target_player_id):
    """Evaluate and, when accepted and cap legal, atomically execute a player swap."""
    conn = connect_database()
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        evaluation = _evaluate_with_cursor(
            cursor,
            user_team_id,
            offered_player_id,
            target_team_id,
            target_player_id,
        )
        if not evaluation["accepted"]:
            reason = (
                "Rival rejected the offer: CASV value does not clear the "
                "relationship premium."
            )
            history_id = _record_history(cursor, evaluation, "rejected", reason)
            conn.commit()
            return {
                **evaluation,
                "status": "rejected",
                "executed": False,
                "history_id": history_id,
                "error": reason,
            }

        cursor.execute(
            "UPDATE players SET team_id = ? WHERE id = ?",
            (target_team_id, offered_player_id),
        )
        cursor.execute(
            "UPDATE players SET team_id = ? WHERE id = ?",
            (user_team_id, target_player_id),
        )
        issues = _roster_issues(cursor, user_team_id) + _roster_issues(
            cursor, target_team_id
        )
        if issues:
            conn.rollback()
            reason = "Trade blocked by CBA compliance: " + "; ".join(issues)
            with closing(connect_database()) as history_conn:
                history_conn.row_factory = sqlite3.Row
                history_id = _record_history(
                    history_conn.cursor(), evaluation, "blocked", reason
                )
                history_conn.commit()
            return {
                **evaluation,
                "status": "blocked",
                "executed": False,
                "history_id": history_id,
                "error": reason,
            }

        reason = "Rival accepted the offer and both post-trade rosters are cap legal."
        history_id = _record_history(cursor, evaluation, "approved", reason)
        conn.commit()
        return {
            **evaluation,
            "status": "approved",
            "executed": True,
            "history_id": history_id,
            "message": reason,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_trade_history(user_team_id, limit=20):
    """Return the latest trade proposals involving the user-controlled team."""
    if limit < 1 or limit > 100:
        raise ValueError("Trade history limit must be between 1 and 100")
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        _get_team(conn.cursor(), user_team_id)
        rows = conn.execute(
            """
            SELECT h.*, offered.name AS offered_player,
                   target.name AS target_player, rival.name AS target_team
            FROM trade_history h
            JOIN players offered ON offered.id = h.offered_player_id
            JOIN players target ON target.id = h.target_player_id
            JOIN teams rival ON rival.id = h.target_team_id
            WHERE h.user_team_id = ?
            ORDER BY h.id DESC
            LIMIT ?
            """,
            (user_team_id, limit),
        ).fetchall()
    return {"trades": [dict(row) for row in rows]}
