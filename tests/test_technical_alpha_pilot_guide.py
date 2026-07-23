from pathlib import Path
import unittest


class TechnicalAlphaPilotGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = Path("docs/technical_alpha_pilot_guide.md").read_text(encoding="utf-8")

    def test_required_pilot_sections_are_present(self) -> None:
        required_sections = (
            "## Required disclosure",
            "## Facilitator readiness check",
            "## Guided test route",
            "## Stop conditions",
            "## Bug report format",
            "## Pilot exit criteria",
        )
        for section in required_sections:
            with self.subTest(section=section):
                self.assertIn(section, self.guide)

    def test_guide_discloses_fictional_alpha_scope(self) -> None:
        self.assertIn("eight original fictional franchises", self.guide)
        self.assertIn("82-game test schedule", self.guide)
        self.assertIn("official 2026–27 NHL schedule uses 32 teams and 84 games", self.guide)

    def test_core_smoke_route_and_privacy_controls_are_documented(self) -> None:
        required_terms = (
            "franchise selection",
            "advance day",
            "roster",
            "standings",
            "trade",
            "save",
            "reload",
            "debug report",
            "reset",
            "Do not post the SQLite database",
        )
        lowered = self.guide.lower()
        for term in required_terms[:-1]:
            with self.subTest(term=term):
                self.assertIn(term, lowered)
        self.assertIn(required_terms[-1], self.guide)


if __name__ == "__main__":
    unittest.main()
