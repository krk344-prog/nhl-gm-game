"""Opt-in service adapter for exposing read-only NHL season context.

The playable Alpha does not change any existing response when no ``season_id``
is supplied. This module only prepares a separate JSON-compatible payload for a
future HTTP route; it performs no database or save writes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.season_context import resolve_season_context


def get_requested_season_context(
    query: Mapping[str, Sequence[str]],
) -> dict[str, Any] | None:
    """Return opt-in season context from parsed query parameters.

    Absence of ``season_id`` preserves the legacy Alpha path exactly. A present
    parameter must contain one non-empty value; unknown seasons are rejected by
    the underlying rules registry rather than silently falling back.
    """
    values = query.get("season_id")
    if values is None:
        return None
    if len(values) != 1 or not values[0].strip():
        raise ValueError("season_id must contain exactly one non-empty value")

    context = resolve_season_context(values[0].strip())
    if context is None:  # Defensive: explicit input must always resolve or fail.
        raise ValueError("season_id did not resolve to a season context")
    return {"season_context": context.as_dict()}
