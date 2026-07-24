from pathlib import Path
import unittest


class TechnicalAlphaPilotGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = Path("docs/technical_alpha_pilot_guide.md").read_text(encoding="utf-8")
        cls.workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    def test_required_pilot_sections_are_present(self) -> None:
        required_sections = (
            "## Required disclosure",
            "## Facilitator readiness check",
            "## Configured APK release procedure",
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

    def test_configured_apk_procedure_binds_preflight_build_and_device_test(self) -> None:
        required_terms = (
            "python scripts/check_alpha_backend.py --api-base-url <URL> --season-id 2026-27",
            "api_base_url",
            "nhl-gm-technical-alpha.apk.sha256",
            "technical-alpha-build.txt",
            "Do not substitute a locally rebuilt or earlier APK",
            "exact-package smoke test passes",
            "127.0.0.1",
            "localhost",
        )
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.guide)

    def test_release_procedure_requires_exact_artifact_verifier(self) -> None:
        required_terms = (
            "python scripts/verify_alpha_artifact.py <ARTIFACT_DIR> --expected-commit <COMMIT_SHA> --expected-api-base-url <URL>",
            '"status": "pass"',
            "both portable checksum files",
            "expected `debug-apk` build type",
            "artifact verification",
        )
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.guide)

    def test_manual_tester_build_rejects_loopback_endpoints(self) -> None:
        required_terms = (
            'EVENT_NAME: ${{ github.event_name }}',
            'if [ "$EVENT_NAME" = "workflow_dispatch" ]',
            "localhost|127.*|0.0.0.0|::1",
            "Manual tester builds require a non-loopback API endpoint",
        )
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.workflow)


if __name__ == "__main__":
    unittest.main()
