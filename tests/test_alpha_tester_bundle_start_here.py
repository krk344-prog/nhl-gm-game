import unittest

from scripts.create_alpha_tester_bundle import _start_here


class AlphaTesterBundleStartHereTests(unittest.TestCase):
    def test_start_here_matches_release_smoke_and_privacy_contract(self):
        text = _start_here("e4ebe0ac69075f1c1298587f1f4c2131d969e59f")

        ordered_steps = [
            "Start a new game.",
            "Select a franchise.",
            "Advance the day.",
            "Open the roster.",
            "Open the standings.",
            "Attempt one trade.",
            "Open Trade History and confirm the trade result is recorded.",
            "Save the game.",
            "Close and reopen the game.",
            "Reload the saved game and confirm your franchise, day, results, standings, and Trade History persist.",
            "Generate the debug report and provide only the privacy-reviewed output to the organizer.",
            "Reset the game and confirm it returns to Day 1.",
        ]
        positions = [text.index(step) for step in ordered_steps]
        self.assertEqual(positions, sorted(positions))

        self.assertIn("eight fictional franchises and an 82-game test schedule", text)
        self.assertIn("not an official NHL roster or schedule product", text)
        self.assertIn("Do not share this package, network details, screenshots, or save files publicly.", text)
        self.assertIn("Do not include your name, device serial number, network address, save file, or password.", text)
        self.assertIn("STATUS: UI REVIEW PENDING", text)


if __name__ == "__main__":
    unittest.main()
