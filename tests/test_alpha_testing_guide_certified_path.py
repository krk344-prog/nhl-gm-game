from pathlib import Path
import unittest


class AlphaTestingGuideCertifiedPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = Path("docs/alpha_testing_guide.md").read_text(encoding="utf-8")

    def test_bug_reporting_does_not_send_testers_to_localhost(self) -> None:
        bug_report = self.guide.split("## Bug report format", 1)[1]
        self.assertNotIn("http://localhost", bug_report)
        self.assertIn("facilitator-provided privacy-safe debug report", bug_report)
        self.assertIn("should not switch to a localhost/development endpoint", bug_report)
        self.assertIn("certified backend/session", bug_report)

    def test_certified_smoke_stops_when_readiness_is_lost(self) -> None:
        start = self.guide.split("## Start the game", 1)[1].split("## Core test pass", 1)[0]
        self.assertIn("device or backend as Not Ready", start)
        self.assertIn("stop the certified smoke pass", start)
        self.assertIn("Do not retry against another endpoint", start)
        self.assertIn("re-establishes the certified Ready state", start)


if __name__ == "__main__":
    unittest.main()
