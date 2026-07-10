"""Small JSON API exposing persisted NHL GM game state to the mobile client."""

import argparse
import json
import math
import os
import re
import sqlite3
import sys
import traceback
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    from .game_service import get_game_state, reset_game, select_user_team
    from .nhl_gm_core import connect_database, init_database
    from .league_orchestrator import (
        advance_day,
        get_schedule,
        get_standings,
        initialize_league,
    )
    from .trade_service import (
        evaluate_trade,
        execute_trade,
        get_trade_history,
        get_trade_market,
    )
except ImportError:  # Support direct execution: python src/nhl_gm_api.py
    from game_service import get_game_state, reset_game, select_user_team
    from nhl_gm_core import connect_database, init_database
    from league_orchestrator import (
        advance_day,
        get_schedule,
        get_standings,
        initialize_league,
    )
    from trade_service import (
        evaluate_trade,
        execute_trade,
        get_trade_history,
        get_trade_market,
    )


def _rating(values):
    return round(sum(values) / len(values)) if values else 0


def _player_overall(player):
    if player["position"] == "G":
        values = [player["positioning"], player["reflexes"], player["speed"]]
    elif player["position"] == "D":
        values = [
            player["shooting"],
            player["passing"],
            player["positioning"],
            player["speed"],
            player["checking"],
        ]
    else:
        values = [
            player["shooting"],
            player["passing"],
            player["positioning"],
            player["speed"],
            player["checking"],
        ]
    return _rating(values)


def _get_team(cursor, team_id):
    cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
    team = cursor.fetchone()
    if team is None:
        raise LookupError(f"Team {team_id} does not exist")
    return dict(team)


def list_teams():
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, name, city, tier, franchise_mandate FROM teams ORDER BY id"
        ).fetchall()
    return {"teams": [dict(row) for row in rows]}


def get_dashboard(team_id):
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        team = _get_team(cursor, team_id)
        calendar = dict(
            cursor.execute("SELECT * FROM league_calendar WHERE id = 1").fetchone()
        )
        players = [
            dict(row)
            for row in cursor.execute(
                "SELECT position, shooting, passing, positioning, reflexes, speed, checking, aav "
                "FROM players WHERE team_id = ?",
                (team_id,),
            ).fetchall()
        ]
        standing_row = cursor.execute(
            "SELECT * FROM standings WHERE team_id = ?", (team_id,)
        ).fetchone()
        next_game_row = cursor.execute(
            """
            SELECT s.day, s.home_team_id, s.away_team_id,
                   home.name AS home_team, away.name AS away_team
            FROM schedule s
            JOIN teams home ON home.id = s.home_team_id
            JOIN teams away ON away.id = s.away_team_id
            WHERE s.day > ?
              AND (s.home_team_id = ? OR s.away_team_id = ?)
              AND s.status = 'scheduled'
            ORDER BY s.day, s.id
            LIMIT 1
            """,
            (calendar["current_day"], team_id, team_id),
        ).fetchone()

    cap_hit = sum(player["aav"] for player in players)
    days_remaining = max(1, calendar["max_days"] - calendar["current_day"])
    buying_power = calendar["accrued_margin"] * (
        calendar["max_days"] / days_remaining
    )
    forwards = [player for player in players if player["position"] == "F"]
    defensemen = [player for player in players if player["position"] == "D"]
    goalies = [player for player in players if player["position"] == "G"]
    offense = _rating(
        [
            (player["shooting"] + player["passing"] + player["speed"]) / 3
            for player in forwards
        ]
    )
    defense = _rating(
        [
            (player["positioning"] + player["checking"] + player["passing"]) / 3
            for player in defensemen
        ]
    )
    goalie_rating = _rating(
        [(player["positioning"] + player["reflexes"]) / 2 for player in goalies]
    )
    standing = dict(standing_row) if standing_row else None
    next_game = None
    if next_game_row:
        next_game_data = dict(next_game_row)
        is_home = next_game_data["home_team_id"] == team_id
        next_game = {
            "day": next_game_data["day"],
            "venue": "home" if is_home else "away",
            "opponent_id": (
                next_game_data["away_team_id"]
                if is_home
                else next_game_data["home_team_id"]
            ),
            "opponent": (
                next_game_data["away_team"]
                if is_home
                else next_game_data["home_team"]
            ),
        }

    return {
        "team": {
            "id": team["id"],
            "name": team["name"],
            "city": team["city"],
            "tier": team["tier"],
            "gm_trust_score": team["gm_trust_score"],
            "franchise_mandate": team["franchise_mandate"],
        },
        "calendar": {
            "current_day": calendar["current_day"],
            "max_days": calendar["max_days"],
        },
        "finances": {
            "cash_balance": team["cash_balance"],
            "cap_hit": cap_hit,
            "cap_ceiling": calendar["salary_cap_ceiling"],
            "cap_space": calendar["salary_cap_ceiling"] - cap_hit,
            "accrued_deadline_buying_power": buying_power,
        },
        "ratings": {
            "overall": _rating(
                [value for value in [offense, defense, goalie_rating] if value]
            ),
            "offense": offense,
            "defense": defense,
            "goalies": goalie_rating,
        },
        "roster": {
            "total": len(players),
            "forwards": len(forwards),
            "defensemen": len(defensemen),
            "goalies": len(goalies),
        },
        "standing": standing,
        "next_game": next_game,
    }


def get_roster(team_id):
    with closing(connect_database()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        team = _get_team(cursor, team_id)
        rows = cursor.execute(
            """
            SELECT id, name, age, position, archetype, shooting, passing,
                   positioning, reflexes, speed, checking, aav, contract_years,
                   fatigue, scout_observations
            FROM players
            WHERE team_id = ?
            ORDER BY CASE position WHEN 'F' THEN 1 WHEN 'D' THEN 2 ELSE 3 END, id
            """,
            (team_id,),
        ).fetchall()

    players = []
    for row in rows:
        player = dict(row)
        player["overall"] = _player_overall(player)
        player["scouting_uncertainty"] = round(
            20.0 * math.exp(-0.35 * player["scout_observations"]), 2
        )
        players.append(player)

    return {
        "team": {"id": team["id"], "name": team["name"], "city": team["city"]},
        "count": len(players),
        "players": players,
    }


class ApiHandler(BaseHTTPRequestHandler):
    team_route = re.compile(r"^/api/v1/teams/(\d+)/(dashboard|roster)$")

    def _send_json(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_internal_error(self, error):
        print(f"Unhandled NHL GM API error: {error}", file=sys.stderr)
        traceback.print_exc()
        self._send_json(500, {"error": "Internal server error"})

    def do_OPTIONS(self):
        self._send_json(200, {})

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length header") from error
        if length <= 0:
            raise ValueError("A JSON request body is required")
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Request body must be valid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object")
        return payload

    @staticmethod
    def _trade_arguments(payload):
        required = (
            "user_team_id",
            "offered_player_id",
            "target_team_id",
            "target_player_id",
        )
        missing = [name for name in required if name not in payload]
        if missing:
            raise ValueError("Missing trade fields: " + ", ".join(missing))
        try:
            return {name: int(payload[name]) for name in required}
        except (TypeError, ValueError) as error:
            raise ValueError("Trade identifiers must be integers") from error

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        try:
            if path == "/api/v1/health":
                self._send_json(200, {"status": "ok", "version": "0.2.0-alpha"})
                return
            if path == "/api/v1/game":
                self._send_json(200, get_game_state())
                return
            if path == "/api/v1/debug-report":
                game = get_game_state()
                user_team_id = game["user_team_id"]
                team_schedule = get_schedule(team_id=user_team_id, limit=200)["games"]
                self._send_json(
                    200,
                    {
                        "version": "0.2.0-alpha",
                        "game": game,
                        "standings": get_standings()["standings"],
                        "recent_games": [
                            item for item in team_schedule if item["status"] == "completed"
                        ][-10:],
                        "trade_history": get_trade_history(user_team_id, limit=10)[
                            "trades"
                        ],
                    },
                )
                return
            if path == "/api/v1/teams":
                self._send_json(200, list_teams())
                return
            if path == "/api/v1/standings":
                self._send_json(200, get_standings())
                return
            if path == "/api/v1/schedule":
                day = int(query["day"][0]) if "day" in query else None
                team_id = int(query["team_id"][0]) if "team_id" in query else None
                limit = int(query.get("limit", [20])[0])
                self._send_json(
                    200, get_schedule(day=day, team_id=team_id, limit=limit)
                )
                return
            if path == "/api/v1/trade-market":
                user_team_id = int(query.get("user_team_id", [1])[0])
                target_team_id = (
                    int(query["target_team_id"][0])
                    if "target_team_id" in query
                    else None
                )
                self._send_json(
                    200,
                    get_trade_market(
                        user_team_id=user_team_id, target_team_id=target_team_id
                    ),
                )
                return
            if path == "/api/v1/trades/history":
                user_team_id = int(query.get("user_team_id", [1])[0])
                limit = int(query.get("limit", [20])[0])
                self._send_json(200, get_trade_history(user_team_id, limit=limit))
                return
            match = self.team_route.match(path)
            if match:
                team_id = int(match.group(1))
                payload = (
                    get_dashboard(team_id)
                    if match.group(2) == "dashboard"
                    else get_roster(team_id)
                )
                self._send_json(200, payload)
                return
            self._send_json(404, {"error": "Route not found"})
        except LookupError as error:
            self._send_json(404, {"error": str(error)})
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
        except Exception as error:
            self._send_internal_error(error)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if path == "/api/v1/advance-day":
                self._send_json(200, advance_day())
                return
            if path == "/api/v1/game/select-team":
                payload = self._read_json()
                if "team_id" not in payload:
                    raise ValueError("Missing field: team_id")
                self._send_json(200, select_user_team(int(payload["team_id"])))
                return
            if path == "/api/v1/game/reset":
                payload = self._read_json()
                if payload.get("confirm") != "RESET":
                    raise ValueError("Reset requires confirm='RESET'")
                self._send_json(
                    200,
                    reset_game(
                        seed=payload.get("seed", 7),
                        save_name=payload.get("save_name", "Alpha Franchise"),
                    ),
                )
                return
            if path in ("/api/v1/trades/evaluate", "/api/v1/trades/execute"):
                arguments = self._trade_arguments(self._read_json())
                if path.endswith("/evaluate"):
                    self._send_json(200, evaluate_trade(**arguments))
                    return
                result = execute_trade(**arguments)
                self._send_json(200 if result["executed"] else 409, result)
                return
            self._send_json(404, {"error": "Route not found"})
        except LookupError as error:
            self._send_json(404, {"error": str(error)})
        except ValueError as error:
            status = 409 if path == "/api/v1/advance-day" else 400
            self._send_json(status, {"error": str(error)})
        except Exception as error:
            self._send_internal_error(error)

    def log_message(self, format, *args):
        return


def create_server(host="127.0.0.1", port=8000):
    return ThreadingHTTPServer((host, port), ApiHandler)


def main():
    parser = argparse.ArgumentParser(description="Serve NHL GM game state as JSON")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--db",
        help="SQLite database path (defaults to NHL_GM_DB_PATH or nhl_gm_core.db)",
    )
    args = parser.parse_args()

    if args.db:
        os.environ["NHL_GM_DB_PATH"] = args.db
    init_database()
    initialize_league()
    server = create_server(args.host, args.port)
    print(f"NHL GM API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
