from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from src.rules_registry import (
    RulesRegistry,
    RulesValidationError,
    UnknownSeasonError,
)


class RulesRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = RulesRegistry()

    def test_available_seasons_are_versioned(self):
        self.assertEqual(self.registry.available_seasons(), ("2025-26", "2026-27"))

    def test_loads_current_rules_without_magic_constants(self):
        rules = self.registry.load("2026-27")
        self.assertEqual(rules.salary_system["upper_limit"], 104_000_000)
        self.assertEqual(rules.salary_system["lower_limit"], 76_900_000)
        self.assertEqual(rules.competition["regular_season_games"], 84)
        self.assertTrue(rules.salary_system["playoff_salary_cap_applies"])

    def test_resolves_rules_by_date(self):
        rules = self.registry.for_date(date(2026, 7, 11))
        self.assertEqual(rules.season_id, "2026-27")

    def test_daily_charge_requires_schedule_derived_days(self):
        rules = self.registry.load("2026-27")
        with self.assertRaises(RulesValidationError):
            rules.daily_cap_charge(10_400_000)
        self.assertEqual(rules.daily_cap_charge(10_400_000, accrual_days=200), 52_000)

    def test_rule_provenance_is_queryable(self):
        rules = self.registry.load("2026-27")
        sources = rules.source_for("salary_system.upper_limit")
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].verification_status, "verified")
        rules.require_verified(["salary_system.upper_limit"])

    def test_summary_only_rules_do_not_pass_strict_verification(self):
        rules = self.registry.load("2026-27")
        with self.assertRaises(RulesValidationError):
            rules.require_verified(["salary_system.playoff_salary_cap_applies"])

    def test_unknown_season_is_explicit(self):
        with self.assertRaises(UnknownSeasonError):
            self.registry.load("2032-33")

    def test_projected_rules_are_opt_in(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = json.loads(
                (Path("config/rules/2026-27.json")).read_text(encoding="utf-8")
            )
            payload["season_id"] = "2030-31"
            payload["effective_from"] = "2030-07-01"
            payload["effective_through"] = "2031-06-30"
            payload["ruleset_status"] = "projected"
            Path(temp_dir, "2030-31.json").write_text(json.dumps(payload), encoding="utf-8")
            registry = RulesRegistry(temp_dir)
            with self.assertRaises(RulesValidationError):
                registry.load("2030-31")
            self.assertEqual(
                registry.load("2030-31", allow_projected=True).season_id,
                "2030-31",
            )


if __name__ == "__main__":
    unittest.main()
