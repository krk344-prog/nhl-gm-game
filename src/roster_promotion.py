"""Guardrails for promoting a reviewed roster catalog into a new game.

This module does not mutate active saves. It only verifies that a normalized,
versioned snapshot is complete enough to be offered as a new-game seed.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from src.roster_import import validate_snapshot

EXPECTED_TEAM_COUNTS = {"NHL": 32, "AHL": 32}


def validate_promotion_readiness(
    snapshot: dict[str, Any],
    expected_team_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Validate a roster pack for new-game selection without changing a save.

    Catalog imports may be partial for review and testing. Promotion is stricter:
    every expected club must be present, every club must have at least one player,
    and the pack must retain source provenance for auditability.
    """
    validate_snapshot(snapshot)
    expected = expected_team_counts or EXPECTED_TEAM_COUNTS
    counts = Counter(str(team["league"]).upper() for team in snapshot["teams"])

    missing_sources = not snapshot.get("sources")
    empty_teams = [
        f"{str(team['league']).upper()} {str(team['abbreviation']).upper()}"
        for team in snapshot["teams"]
        if not team.get("players")
    ]
    count_mismatches = {
        league: {"expected": required, "actual": counts.get(league, 0)}
        for league, required in expected.items()
        if counts.get(league, 0) != required
    }

    blockers: list[str] = []
    if missing_sources:
        blockers.append("Roster pack requires source provenance before promotion.")
    if empty_teams:
        blockers.append("Every promoted team requires at least one player.")
    for league, mismatch in count_mismatches.items():
        blockers.append(
            f"{league} team count must be {mismatch['expected']}; found {mismatch['actual']}."
        )

    return {
        "ready": not blockers,
        "season_id": snapshot["season_id"],
        "team_counts": dict(counts),
        "empty_teams": empty_teams,
        "count_mismatches": count_mismatches,
        "source_provenance_present": not missing_sources,
        "blockers": blockers,
    }
