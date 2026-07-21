"""Versioned, source-backed NHL rules registry.

The simulation must never infer a season's legal environment from hard-coded
constants.  This module loads immutable season files, validates their internal
consistency, and exposes provenance alongside every ruleset.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_RULES_DIR = Path(__file__).resolve().parents[1] / "config" / "rules"
ALLOWED_RULESET_STATUSES = {
    "official",
    "official_with_pending_operational_details",
    "projected",
    "deprecated",
}
ALLOWED_VERIFICATION_STATUSES = {
    "verified",
    "inherited",
    "verified_summary_pending_full_rule_mapping",
    "unverified",
}


class RulesRegistryError(ValueError):
    """Base error for malformed, missing, or ambiguous rules."""


class UnknownSeasonError(RulesRegistryError):
    """Raised when no ruleset exists for the requested season or date."""


class RulesValidationError(RulesRegistryError):
    """Raised when a ruleset fails structural or domain validation."""


@dataclass(frozen=True)
class RuleSource:
    id: str
    authority: str
    verification_status: str
    title: str
    url: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class SeasonRules:
    schema_version: int
    season_id: str
    effective_from: date
    effective_through: date
    ruleset_status: str
    competition: Mapping[str, Any]
    salary_system: Mapping[str, Any]
    transaction_rules: Mapping[str, Any]
    sources: tuple[RuleSource, ...]

    def daily_cap_charge(self, annual_cap_hit: float, accrual_days: int | None = None) -> float:
        """Return the daily charge using a schedule-derived denominator.

        A caller may supply ``accrual_days`` after the official league calendar
        is loaded. A ruleset may also contain an explicit verified value. The
        method intentionally refuses to fall back to a magic constant.
        """
        denominator = accrual_days or self.competition.get("accrual_days")
        if not isinstance(denominator, int) or denominator <= 0:
            raise RulesValidationError(
                f"{self.season_id} has no verified accrual-day denominator; "
                "derive it from the official schedule before calculating daily cap charges"
            )
        if annual_cap_hit < 0:
            raise RulesValidationError("annual_cap_hit cannot be negative")
        return annual_cap_hit / denominator

    def source_for(self, rule_path: str) -> tuple[RuleSource, ...]:
        """Return all sources that explicitly support a dotted rule path."""
        return tuple(
            source
            for source in self.sources
            if rule_path in source.supports
            or any(rule_path.startswith(f"{prefix}.") for prefix in source.supports)
        )

    def require_verified(self, rule_paths: Iterable[str]) -> None:
        """Reject gameplay use of rules without sufficiently strong evidence."""
        acceptable = {"verified", "inherited"}
        missing = []
        for path in rule_paths:
            supporting = self.source_for(path)
            if not supporting or not any(s.verification_status in acceptable for s in supporting):
                missing.append(path)
        if missing:
            raise RulesValidationError(
                f"Rules lack verified provenance for {self.season_id}: {', '.join(missing)}"
            )


class RulesRegistry:
    def __init__(self, rules_dir: Path | str = DEFAULT_RULES_DIR) -> None:
        self.rules_dir = Path(rules_dir)
        self._cache: dict[str, SeasonRules] = {}

    def available_seasons(self) -> tuple[str, ...]:
        return tuple(sorted(path.stem for path in self.rules_dir.glob("*.json")))

    def load(self, season_id: str, *, allow_projected: bool = False) -> SeasonRules:
        if season_id in self._cache:
            rules = self._cache[season_id]
        else:
            path = self.rules_dir / f"{season_id}.json"
            if not path.exists():
                raise UnknownSeasonError(
                    f"No NHL ruleset found for {season_id}. Available: {', '.join(self.available_seasons())}"
                )
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise RulesValidationError(f"Invalid JSON in {path}: {exc}") from exc
            rules = self._parse_and_validate(payload, path)
            self._cache[season_id] = rules

        if rules.ruleset_status == "projected" and not allow_projected:
            raise RulesValidationError(
                f"{season_id} is projected; pass allow_projected=True only for scenario planning"
            )
        if rules.ruleset_status == "deprecated":
            raise RulesValidationError(f"{season_id} ruleset is deprecated")
        return rules

    def for_date(self, on_date: date, *, allow_projected: bool = False) -> SeasonRules:
        matches = [
            self.load(season, allow_projected=allow_projected)
            for season in self.available_seasons()
            if self._date_in_file_range(season, on_date)
        ]
        if len(matches) != 1:
            raise UnknownSeasonError(
                f"Expected exactly one ruleset for {on_date.isoformat()}, found {len(matches)}"
            )
        return matches[0]

    def _date_in_file_range(self, season_id: str, on_date: date) -> bool:
        path = self.rules_dir / f"{season_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return date.fromisoformat(payload["effective_from"]) <= on_date <= date.fromisoformat(
            payload["effective_through"]
        )

    @staticmethod
    def _parse_and_validate(payload: Mapping[str, Any], path: Path) -> SeasonRules:
        required = {
            "schema_version",
            "season_id",
            "effective_from",
            "effective_through",
            "ruleset_status",
            "competition",
            "salary_system",
            "transaction_rules",
            "sources",
        }
        missing = required.difference(payload)
        if missing:
            raise RulesValidationError(f"{path} missing fields: {', '.join(sorted(missing))}")

        try:
            effective_from = date.fromisoformat(str(payload["effective_from"]))
            effective_through = date.fromisoformat(str(payload["effective_through"]))
        except ValueError as exc:
            raise RulesValidationError(f"{path} contains an invalid effective date") from exc

        status = str(payload["ruleset_status"])
        if status not in ALLOWED_RULESET_STATUSES:
            raise RulesValidationError(f"Unsupported ruleset_status: {status}")
        if effective_from > effective_through:
            raise RulesValidationError("effective_from must be on or before effective_through")
        if path.stem != payload["season_id"]:
            raise RulesValidationError("season_id must match the rules filename")

        salary = payload["salary_system"]
        required_salary = {
            "upper_limit",
            "lower_limit",
            "minimum_nhl_salary",
            "active_roster_maximum",
            "contract_limit",
            "reserve_list_limit",
            "maximum_contract_years_re_signing",
            "maximum_contract_years_new_club",
            "playoff_salary_cap_applies",
        }
        salary_missing = required_salary.difference(salary)
        if salary_missing:
            raise RulesValidationError(
                f"salary_system missing fields: {', '.join(sorted(salary_missing))}"
            )
        if salary["lower_limit"] >= salary["upper_limit"]:
            raise RulesValidationError("salary lower_limit must be below upper_limit")
        if not 18 <= salary["active_roster_maximum"] <= 30:
            raise RulesValidationError("active_roster_maximum is outside a plausible NHL range")
        if salary["maximum_contract_years_new_club"] > salary["maximum_contract_years_re_signing"]:
            raise RulesValidationError("new-club maximum term cannot exceed re-signing maximum term")

        sources = []
        seen_source_ids = set()
        for raw in payload["sources"]:
            if raw["id"] in seen_source_ids:
                raise RulesValidationError(f"duplicate source id: {raw['id']}")
            seen_source_ids.add(raw["id"])
            verification_status = raw["verification_status"]
            if verification_status not in ALLOWED_VERIFICATION_STATUSES:
                raise RulesValidationError(
                    f"unsupported verification_status: {verification_status}"
                )
            if not str(raw["url"]).startswith("https://"):
                raise RulesValidationError(f"source URL must use HTTPS: {raw['id']}")
            sources.append(
                RuleSource(
                    id=str(raw["id"]),
                    authority=str(raw["authority"]),
                    verification_status=str(verification_status),
                    title=str(raw["title"]),
                    url=str(raw["url"]),
                    supports=tuple(raw["supports"]),
                )
            )
        if not sources:
            raise RulesValidationError("every ruleset must include at least one source")

        return SeasonRules(
            schema_version=int(payload["schema_version"]),
            season_id=str(payload["season_id"]),
            effective_from=effective_from,
            effective_through=effective_through,
            ruleset_status=status,
            competition=dict(payload["competition"]),
            salary_system=dict(salary),
            transaction_rules=dict(payload["transaction_rules"]),
            sources=tuple(sources),
        )
