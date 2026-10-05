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

    def test_major_failure_preserves_reproducible_state_for_facilitator(self) -> None:
        bug_report = self.guide.split("## Bug report format", 1)[1]
        self.assertIn("preserve the current app state", bug_report)
        self.assertIn("Do not clear app data", bug_report)
        self.assertIn("reset the save", bug_report)
        self.assertIn("reinstall the APK", bug_report)
        self.assertIn("failing state reproducible", bug_report)

    def test_core_smoke_requires_step_level_outcomes(self) -> None:
        core = self.guide.split("## Core test pass", 1)[1].split("## Longer simulation pass", 1)[0]
        self.assertIn("pass, fail, or blocked", core)
        self.assertIn("failing step number", core)
        self.assertIn("privacy-safe session reference", core)
        self.assertIn("later dependent steps", core)
        self.assertIn("facilitator explicitly releases", core)


if __name__ == "__main__":
    unittest.main()
