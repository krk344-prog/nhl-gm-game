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
            "Open Game Center and verify the latest result, recent results, and standings agree.",
            "Filter the roster by forwards, defense, and goalies.",
            "Open Trade Center",
            "Confirm both proposals appear in Trade History.",
            "Restart the API and mobile client",
            "Use Front Office → New Game / Reset Save",
        ]

        positions = [core.index(marker) for marker in required_markers]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
