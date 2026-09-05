import unittest

from src.season_context_route import (
    SEASON_CONTEXT_PATH,
    resolve_season_context_route,
)


class SeasonContextRouteTest(unittest.TestCase):
    def test_unrelated_route_preserves_legacy_handler_path(self):
        self.assertIsNone(resolve_season_context_route("/api/v1/game", {}))

    def test_explicit_season_returns_read_only_context(self):
        status, payload = resolve_season_context_route(
            SEASON_CONTEXT_PATH,
            {"season_id": ["2026-27"]},
        )

        self.assertEqual(status, 200)
        context = payload["season_context"]
        self.assertEqual(context["season_id"], "2026-27")
        self.assertEqual(context["regular_season_games"], 84)
        self.assertEqual(context["upper_limit"], 104_000_000)
        self.assertIn("source_ids", context)

    def test_trailing_slash_is_supported(self):
        status, payload = resolve_season_context_route(
            f"{SEASON_CONTEXT_PATH}/",
            {"season_id": ["2025-26"]},
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["season_context"]["season_id"], "2025-26")

    def test_missing_season_is_a_stable_bad_request(self):
        status, payload = resolve_season_context_route(SEASON_CONTEXT_PATH, {})

        self.assertEqual(status, 400)
        self.assertEqual(payload["code"], "invalid_season_context_request")
        self.assertEqual(payload["error"], "season_id query parameter is required")

    def test_invalid_or_repeated_season_is_a_stable_bad_request(self):
        cases = (
            {"season_id": [""]},
            {"season_id": ["2026-27", "2025-26"]},
            {"season_id": ["2099-00"]},
        )

        for query in cases:
            with self.subTest(query=query):
                status, payload = resolve_season_context_route(
                    SEASON_CONTEXT_PATH,
                    query,
                )
                self.assertEqual(status, 400)
                self.assertEqual(
                    payload["code"],
                    "invalid_season_context_request",
                )
                self.assertTrue(payload["error"])


if __name__ == "__main__":
    unittest.main()
