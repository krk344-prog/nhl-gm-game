import json
from datetime import date
from pathlib import Path
import tempfile
import unittest

from src.rules_registry import RulesRegistry, UnknownSeasonError


RULES_DIR = Path(__file__).resolve().parents[1] / "config" / "rules"


class AlphaRulesRegistryTests(unittest.TestCase):
    def test_registry_resolves_alpha_and_next_season_boundaries(self):
        registry = RulesRegistry(RULES_DIR)

        self.assertEqual(registry.available_seasons(), ("2025-26", "2026-27"))
        self.assertEqual(registry.for_date(date(2026, 6, 30)).season_id, "2025-26")
        self.assertEqual(registry.for_date(date(2026, 7, 1)).season_id, "2026-27")
        self.assertEqual(registry.load("2025-26").competition["regular_season_games"], 82)
        self.assertEqual(registry.load("2026-27").competition["regular_season_games"], 84)

    def test_registry_rejects_uncovered_date(self):
        registry = RulesRegistry(RULES_DIR)

        with self.assertRaisesRegex(UnknownSeasonError, "found 0"):
            registry.for_date(date(2025, 6, 30))

    def test_registry_rejects_overlapping_effective_ranges(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            alpha = json.loads((RULES_DIR / "2025-26.json").read_text(encoding="utf-8"))
            next_season = json.loads(
                (RULES_DIR / "2026-27.json").read_text(encoding="utf-8")
            )
            next_season["effective_from"] = "2026-06-30"

            (temp_path / "2025-26.json").write_text(
                json.dumps(alpha), encoding="utf-8"
            )
            (temp_path / "2026-27.json").write_text(
                json.dumps(next_season), encoding="utf-8"
            )

            with self.assertRaisesRegex(UnknownSeasonError, "found 2"):
                RulesRegistry(temp_path).for_date(date(2026, 6, 30))


if __name__ == "__main__":
    unittest.main()
