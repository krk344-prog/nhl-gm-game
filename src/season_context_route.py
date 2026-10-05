"""Read-only HTTP route contract for NHL season context.

This module deliberately does not modify the Alpha API handler. It provides a
small, dependency-free route adapter that can be mounted in ``nhl_gm_api`` once
its response and error contracts are validated.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

try:
    from .season_context_service import get_requested_season_context
except ImportError:  # Support direct execution from the src directory.
    from season_context_service import get_requested_season_context

SEASON_CONTEXT_PATH = "/api/v1/season-context"


def resolve_season_context_route(
    path: str,
    query: Mapping[str, Sequence[str]],
) -> tuple[int, dict[str, Any]] | None:
    """Resolve the dedicated read-only season-context route.

    ``None`` means the request is not owned by this route and the legacy Alpha
    handler must continue unchanged. The endpoint requires exactly one explicit
    ``season_id`` so it cannot silently infer or mutate a save's rules context.
    """
    normalized_path = path.rstrip("/") or "/"
    if normalized_path != SEASON_CONTEXT_PATH:
        return None

    try:
        payload = get_requested_season_context(query)
        if payload is None:
            raise ValueError("season_id query parameter is required")
        return 200, payload
    except (LookupError, ValueError) as error:
        return 400, {
            "error": str(error),
            "code": "invalid_season_context_request",
        }
