import json
from pathlib import Path
import unittest


RULES_DIR = Path(__file__).resolve().parents[1] / "config" / "rules"


class SeasonRulesPayloadTests(unittest.TestCase):
    def load_rules(self, season_id):
        path = RULES_DIR / f"{season_id}.json"
        self.assertTrue(path.exists(), f"missing rules payload: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_alpha_and_next_season_rules_are_additive_and_source_backed(self):
        alpha = self.load_rules("2025-26")
        next_season = self.load_rules("2026-27")

        self.assertEqual(alpha["competition"]["regular_season_games"], 82)
        self.assertEqual(next_season["competition"]["regular_season_games"], 84)
        self.assertEqual(alpha["salary_system"]["upper_limit"], 95_500_000)
        self.assertEqual(next_season["salary_system"]["upper_limit"], 104_000_000)
        self.assertEqual(alpha["salary_system"]["active_roster_maximum"], 23)
        self.assertEqual(next_season["salary_system"]["active_roster_maximum"], 23)

        for payload in (alpha, next_season):
            self.assertIsNone(payload["competition"]["accrual_days"])
            self.assertEqual(
                payload["competition"]["accrual_days_strategy"],
                "derive_from_official_schedule",
            )
            self.assertTrue(payload["sources"])
            for source in payload["sources"]:
                self.assertTrue(source["url"].startswith("https://"))
                self.assertTrue(source["supports"])

    def test_season_payloads_have_contiguous_effective_ranges(self):
        alpha = self.load_rules("2025-26")
        next_season = self.load_rules("2026-27")

        self.assertEqual(alpha["effective_through"], "2026-06-30")
        self.assertEqual(next_season["effective_from"], "2026-07-01")


if __name__ == "__main__":
    unittest.main()
