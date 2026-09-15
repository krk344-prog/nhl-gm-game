from pathlib import Path
import unittest


class AlphaLaunchStabilityDisclosureTests(unittest.TestCase):
    def test_disclosure_matches_physical_launch_gate(self) -> None:
        disclosure = Path("docs/technical_alpha_launch_stability_disclosure.md").read_text(encoding="utf-8")
        launcher = Path("scripts/launch_alpha_app.py").read_text(encoding="utf-8")

        self.assertIn("LAUNCH_STABILITY_SECONDS = 3.0", launcher)
        self.assertIn('"launch_stability_confirmed": True', launcher)
        self.assertIn('"launch_stability_seconds": LAUNCH_STABILITY_SECONDS', launcher)
        self.assertIn("same application process", disclosure)
        self.assertIn("three-second stability window", disclosure)
        self.assertIn("restarts with a different PID", disclosure)
        self.assertIn("Do not begin gameplay smoke", disclosure)
        self.assertIn("UI Review Pending", disclosure)


if __name__ == "__main__":
    unittest.main()
