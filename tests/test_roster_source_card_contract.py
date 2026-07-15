from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "mobile" / "components" / "RosterSourceCard.js"


class RosterSourceCardContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CARD.read_text(encoding="utf-8")

    def test_component_preserves_approved_premium_surface_contract(self):
        self.assertIn("#0D0F13", self.source)
        self.assertIn("#171A20", self.source)
        self.assertIn("#D6A84B", self.source)
        self.assertIn("borderRadius: 22", self.source)
        self.assertIn("minHeight: 292", self.source)

    def test_visible_consequences_are_bounded_to_three(self):
        self.assertIn("consequences.slice(0, 3)", self.source)

    def test_selected_and_blocked_states_do_not_rely_on_color_alone(self):
        self.assertIn("selected: selected", self.source)
        self.assertIn("blocked ? 'Unavailable'", self.source)
        self.assertIn("accessibilityRole=\"alert\"", self.source)
        self.assertIn(">BLOCKED<", self.source)

    def test_card_exposes_keyboard_and_screen_reader_semantics(self):
        self.assertIn("accessibilityRole=\"button\"", self.source)
        self.assertIn("accessibilityLabel", self.source)
        self.assertIn("accessibilityHint", self.source)
        self.assertIn("focused && styles.cardFocused", self.source)
        self.assertRegex(self.source, re.compile(r"cardFocused:\s*\{[^}]*borderWidth:\s*2", re.DOTALL))

    def test_primary_action_meets_minimum_touch_target(self):
        self.assertRegex(self.source, re.compile(r"actionRow:\s*\{[^}]*minHeight:\s*44", re.DOTALL))

    def test_blocked_source_requires_an_explanation(self):
        self.assertIn("const blocked = Boolean(blockedReason)", self.source)
        self.assertIn("{blockedReason}", self.source)
        self.assertIn("Review blocker", self.source)


if __name__ == "__main__":
    unittest.main()
