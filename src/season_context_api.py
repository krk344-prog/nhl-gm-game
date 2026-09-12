"""Executable Alpha API handler with the read-only season-context route.

The handler subclasses the existing Alpha ``ApiHandler`` and intercepts only the
season-context GET route. Every unrelated request is delegated to the existing
implementation so legacy API behavior remains unchanged.
"""

from __future__ import annotations

import argparse
import os
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    from .league_orchestrator import initialize_league
    from .nhl_gm_api import ApiHandler
    from .nhl_gm_core import init_database
    from .season_context_route import resolve_season_context_route
except ImportError:  # Support direct execution from the src directory.
    from league_orchestrator import initialize_league
    from nhl_gm_api import ApiHandler
    from nhl_gm_core import init_database
    from season_context_route import resolve_season_context_route


class SeasonContextApiHandler(ApiHandler):
    """Alpha handler with one additive, read-only season-context GET route."""

    def do_GET(self):
        parsed = urlparse(self.path)
        route_result = resolve_season_context_route(
            parsed.path,
            parse_qs(parsed.query, keep_blank_values=True),
        )
        if route_result is None:
            super().do_GET()
            return

        status, payload = route_result
        self._send_json(status, payload)


def create_season_context_server(host="127.0.0.1", port=0):
    """Create the integrated server without initializing or mutating save data."""

    return ThreadingHTTPServer((host, port), SeasonContextApiHandler)


def main():
    """Run the playable Alpha API with the additive season-context route."""

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
    server = create_season_context_server(args.host, args.port)
    print(f"NHL GM API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
