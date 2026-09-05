import unittest

from src.rules_registry import UnknownSeasonError
from src.season_context import resolve_season_context


class SeasonContextTests(unittest.TestCase):
    def test_adapter_is_inactive_without_explicit_season(self):
        self.assertIsNone(resolve_season_context(None))

    def test_adapter_returns_stable_context_for_explicit_season(self):
        context = resolve_season_context("2026-27")

        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.season_id, "2026-27")
        self.assertEqual(context.regular_season_games, 84)
        self.assertEqual(context.upper_limit, 104_000_000)
        self.assertEqual(context.lower_limit, 76_900_000)
        self.assertEqual(context.minimum_nhl_salary, 850_000)
        self.assertGreaterEqual(context.active_roster_maximum, 18)
        self.assertTrue(context.source_ids)
        self.assertEqual(context.as_dict()["source_ids"], list(context.source_ids))

    def test_adapter_rejects_unknown_season_instead_of_falling_back(self):
        with self.assertRaises(UnknownSeasonError):
            resolve_season_context("2099-00")


if __name__ == "__main__":
    unittest.main()
