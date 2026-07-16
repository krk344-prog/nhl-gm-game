from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "mobile" / "components" / "TeamMark.js"


class TeamMarkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = COMPONENT.read_text(encoding="utf-8")

    def test_missing_artwork_has_initials_fallback(self):
        self.assertIn("safeInitials", self.source)
        self.assertIn("logoSource ? (", self.source)
        self.assertIn("{initials}", self.source)

    def test_mark_has_accessible_image_semantics(self):
        self.assertIn('accessibilityRole="image"', self.source)
        self.assertIn("accessibilityLabel={label}", self.source)
        self.assertIn("`${name || 'Team'} crest`", self.source)

    def test_small_size_remains_legible_and_bounded(self):
        self.assertRegex(
            self.source,
            re.compile(r"Math\.max\(24,\s*Math\.min\(size,\s*72\)\)"),
        )
        self.assertIn("numberOfLines={1}", self.source)
        self.assertIn("maxFontSizeMultiplier={1.25}", self.source)

    def test_team_color_is_restrained_to_mark_surface(self):
        self.assertIn("backgroundColor: primaryColor || FALLBACK_BG", self.source)
        self.assertNotIn("position: 'absolute'", self.source)
        self.assertNotIn("resizeMode=\"cover\"", self.source)

    def test_component_does_not_embed_third_party_assets(self):
        self.assertNotRegex(self.source, re.compile(r"https?://"))
        self.assertIn("approved/local artwork", self.source)


if __name__ == "__main__":
    unittest.main()
