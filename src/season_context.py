"""Read-only season context for the playable Alpha service layer.

This adapter deliberately does not mutate saves, database tables, HTTP payloads,
or existing Alpha constants. Callers must provide an explicit season identifier;
when none is supplied, the adapter remains inactive and returns ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.rules_registry import RulesRegistry, SeasonRules


@dataclass(frozen=True)
class SeasonContext:
    season_id: str
    schema_version: int
    ruleset_status: str
    regular_season_games: int
    upper_limit: int
    lower_limit: int
    minimum_nhl_salary: int
    active_roster_maximum: int
    source_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a stable, JSON-compatible service-layer representation."""
        return {
            "season_id": self.season_id,
            "schema_version": self.schema_version,
            "ruleset_status": self.ruleset_status,
            "regular_season_games": self.regular_season_games,
            "upper_limit": self.upper_limit,
            "lower_limit": self.lower_limit,
            "minimum_nhl_salary": self.minimum_nhl_salary,
            "active_roster_maximum": self.active_roster_maximum,
            "source_ids": list(self.source_ids),
        }


def resolve_season_context(
    season_id: str | None,
    *,
    registry: RulesRegistry | None = None,
) -> SeasonContext | None:
    """Resolve read-only context only when a season is explicitly supplied.

    ``None`` preserves the existing Alpha path exactly. An unknown, projected,
    deprecated, or malformed season is rejected by ``RulesRegistry`` rather
    than falling back to a guessed rules environment.
    """
    if season_id is None:
        return None

    rules = (registry or RulesRegistry()).load(season_id)
    return _context_from_rules(rules)


def _context_from_rules(rules: SeasonRules) -> SeasonContext:
    competition = rules.competition
    salary = rules.salary_system
    return SeasonContext(
        season_id=rules.season_id,
        schema_version=rules.schema_version,
        ruleset_status=rules.ruleset_status,
        regular_season_games=int(competition["regular_season_games"]),
        upper_limit=int(salary["upper_limit"]),
        lower_limit=int(salary["lower_limit"]),
        minimum_nhl_salary=int(salary["minimum_nhl_salary"]),
        active_roster_maximum=int(salary["active_roster_maximum"]),
        source_ids=tuple(source.id for source in rules.sources),
    )
