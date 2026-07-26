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

    def test_configured_apk_procedure_uses_verified_build_handoff(self) -> None:
        required_terms = (
            "python scripts/prepare_alpha_build.py --season-id 2026-27",
            "python scripts/prepare_alpha_build.py --api-base-url <URL> --season-id 2026-27",
            '"ready": true',
            '"ready": false',
            '"ref": "agent/alpha-rules-integration-v1"',
            "dispatch_command",
            "Run the returned `dispatch_command` exactly as emitted",
            "Do not edit the URL, workflow, or branch",
            "do not guess an address or manually assemble a workflow command",
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

    def test_release_guide_names_match_workflow_artifacts(self) -> None:
        artifact_names = (
            "nhl-gm-technical-alpha.apk",
            "nhl-gm-technical-alpha.apk.sha256",
            "nhl-gm-android-export.tar.gz",
            "nhl-gm-android-export.sha256",
            "technical-alpha-build.txt",
        )
        for name in artifact_names:
            with self.subTest(name=name):
                self.assertIn(name, self.workflow)
                self.assertIn(name, self.guide)
        self.assertNotIn("nhl-gm-technical-alpha-android-export.zip.sha256", self.guide)

    def test_release_procedure_requires_private_validation_and_redacted_public_summary(self) -> None:
        required_terms = (
            "python scripts/validate_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>",
            "python scripts/summarize_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>",
            "Post only this redacted summary",
            "Do not commit a completed device record",
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

    def test_packaged_build_requires_authoritative_api_path(self) -> None:
        required_terms = (
            'normalized_api_url="${TECHNICAL_ALPHA_API_URL%/}"',
            "*/api/v1) ;;",
            "api_base_url must end with /api/v1",
            "api_base_url must not contain a query string or fragment",
        )
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, self.workflow)


if __name__ == "__main__":
    unittest.main()
