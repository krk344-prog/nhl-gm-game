import unittest

from src.season_context_service import get_requested_season_context


class SeasonContextServiceTest(unittest.TestCase):
    def test_absent_season_preserves_legacy_path(self):
        self.assertIsNone(get_requested_season_context({}))

    def test_explicit_season_returns_json_compatible_context(self):
        payload = get_requested_season_context({"season_id": ["2026-27"]})

        context = payload["season_context"]
        self.assertEqual(context["season_id"], "2026-27")
        self.assertEqual(context["regular_season_games"], 84)
        self.assertEqual(context["upper_limit"], 104_000_000)
        self.assertEqual(context["lower_limit"], 76_900_000)
        self.assertEqual(context["minimum_nhl_salary"], 850_000)
        self.assertIsInstance(context["source_ids"], list)
        self.assertTrue(context["source_ids"])

    def test_blank_or_repeated_season_is_rejected(self):
        for query in (
            {"season_id": [""]},
            {"season_id": ["2025-26", "2026-27"]},
        ):
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "exactly one non-empty"):
                    get_requested_season_context(query)

    def test_unknown_season_is_not_silently_replaced(self):
        with self.assertRaises((LookupError, ValueError)):
            get_requested_season_context({"season_id": ["2099-00"]})


if __name__ == "__main__":
    unittest.main()
