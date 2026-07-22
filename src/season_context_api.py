"""Reversible API handler that mounts the read-only season-context route.

The existing Alpha ``ApiHandler`` remains unchanged. This subclass provides the
smallest executable integration seam for validating the new route through real
HTTP requests before the route is promoted into the default server.
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    from .nhl_gm_api import ApiHandler
    from .season_context_route import resolve_season_context_route
except ImportError:  # Support direct execution from the src directory.
    from nhl_gm_api import ApiHandler
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
    """Create an isolated server for HTTP contract validation.

    Port ``0`` lets the operating system select an available port during tests.
    No database or save initialization is performed by this factory.
    """

    return ThreadingHTTPServer((host, port), SeasonContextApiHandler)
