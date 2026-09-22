from pathlib import Path
import unittest


class AlphaCoreRouteContractTests(unittest.TestCase):
    def test_core_route_keeps_required_pilot_actions_in_order(self) -> None:
        guide = Path("docs/alpha_testing_guide.md").read_text(encoding="utf-8")
        core = guide.split("## Core test pass", 1)[1].split("## Longer simulation pass", 1)[0]

        required_markers = [
            "Confirm eight franchises appear on the Dashboard.",
            "Select a different franchise and restart the mobile client; the selection should persist.",
            "Advance through at least ten calendar days.",
            "Confirm scheduled games produce final scores without ties.",
            "Open Game Center and verify the latest result, recent results, and standings agree.",
            "Filter the roster by forwards, defense, and goalies.",
            "Open Trade Center",
            "Confirm both proposals appear in Trade History.",
            "Save/reload checkpoint:",
            "Reset checkpoint:",
        ]

        positions = [core.index(marker) for marker in required_markers]
        self.assertEqual(positions, sorted(positions))

    def test_save_reload_checkpoint_requires_visible_persistence_evidence(self) -> None:
        guide = Path("docs/alpha_testing_guide.md").read_text(encoding="utf-8")
        core = guide.split("## Core test pass", 1)[1].split("## Longer simulation pass", 1)[0]

        self.assertIn("restart the API and mobile client", core)
        self.assertIn("season day, results, team selection, and trade history should persist", core)
        self.assertIn("all four persisted values are visibly restored after restart", core)

    def test_reset_checkpoint_requires_visible_clean_state_evidence(self) -> None:
        guide = Path("docs/alpha_testing_guide.md").read_text(encoding="utf-8")
        core = guide.split("## Core test pass", 1)[1].split("## Longer simulation pass", 1)[0]

        self.assertIn("season returns to Day 1", core)
        self.assertIn("prior session's trade history is no longer present", core)
        self.assertIn("both clean-state conditions are visibly confirmed", core)


if __name__ == "__main__":
    unittest.main()
