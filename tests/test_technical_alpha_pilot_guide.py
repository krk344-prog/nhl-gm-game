from pathlib import Path
import unittest


class TechnicalAlphaPilotGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guide = Path("docs/technical_alpha_pilot_guide.md").read_text(encoding="utf-8")
        cls.workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        cls.builder = Path("scripts/build_alpha_apk_local.py").read_text(encoding="utf-8")
        cls.verifier = Path("scripts/verify_alpha_artifact.py").read_text(encoding="utf-8")

    def test_required_pilot_sections_are_present(self) -> None:
        for section in (
            "## Required disclosure", "## Tester launch handoff card",
            "## Facilitator readiness check", "## Configured APK release procedure",
            "## Guided test route", "## Stop conditions", "## Bug report format",
            "## Pilot exit criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, self.guide)

    def test_guide_discloses_fictional_alpha_scope(self) -> None:
        self.assertIn("eight original fictional franchises", self.guide)
        self.assertIn("82-game test schedule", self.guide)
        self.assertIn("official 2026–27 NHL schedule uses 32 teams and 84 games", self.guide)

    def test_launch_handoff_card_contains_pilot_critical_information(self) -> None:
        for term in (
            "exact build commit", "backend status", "Start Test",
            "franchise selection", "advance day", "roster", "standings",
            "trade", "save", "reload", "debug report", "reset",
            "private bug-report destination", "360-pixel mobile viewport",
            "UI Review Pending",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.guide)

    def test_core_smoke_route_and_privacy_controls_are_documented(self) -> None:
        lowered = self.guide.lower()
        for term in ("franchise selection", "advance day", "roster", "standings", "trade", "save", "reload", "debug report", "reset"):
            with self.subTest(term=term):
                self.assertIn(term, lowered)
        self.assertIn("Do not post the SQLite database", self.guide)

    def test_configured_apk_procedure_uses_verified_local_build_handoff(self) -> None:
        for term in (
            "python scripts/prepare_alpha_build.py --season-id 2026-27",
            "python scripts/prepare_alpha_build.py --api-base-url <URL> --season-id 2026-27",
            '"ready": true', '"ready": false',
            '"ref": "agent/alpha-rules-integration-v1"',
            "qualification_command", "qualification_record",
            "artifacts/alpha-endpoint-qualification.json",
            "Run the returned `qualification_command` exactly as emitted",
            "do not build; rerun `prepare_alpha_build.py` and qualification from the beginning",
            "build_command", "scripts/build_alpha_apk_local.py",
            "Run the returned `build_command` exactly as emitted",
            "qualification record is still fresh",
            "fails closed when the record is stale or belongs to another endpoint",
            "Do not edit the endpoint or branch",
            "do not guess an address or manually assemble a build command",
            "dist/technical-alpha", "exact-package smoke test passes",
            "127.0.0.1", "localhost",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.guide)
        self.assertNotIn("dispatch_command", self.guide)
        self.assertNotIn("gh workflow run", self.guide)

    def test_release_procedure_requires_exact_standalone_artifact_verifier(self) -> None:
        for term in (
            "python scripts/verify_alpha_artifact.py dist/technical-alpha --expected-commit <COMMIT_SHA> --expected-api-base-url <URL>",
            '"status": "pass"', "both portable checksum files",
            "expected `standalone-release-apk` build type",
            "assets/index.android.bundle", "verification",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.guide)

    def test_release_artifact_names_match_builder_and_workflow(self) -> None:
        for name in (
            "nhl-gm-technical-alpha.apk", "nhl-gm-technical-alpha.apk.sha256",
            "nhl-gm-android-export.tar.gz", "nhl-gm-android-export.sha256",
            "technical-alpha-build.txt",
        ):
            with self.subTest(name=name):
                self.assertIn(name, self.workflow)
                self.assertIn(name, self.builder)
                self.assertIn(name, self.guide)

    def test_workflow_manifest_records_the_packaged_pr_head(self) -> None:
        self.assertIn(
            "TECHNICAL_ALPHA_SOURCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
            self.workflow,
        )
        self.assertIn('"$TECHNICAL_ALPHA_SOURCE_SHA" "$TECHNICAL_ALPHA_API_URL"', self.workflow)
        self.assertNotIn('"$GITHUB_SHA" "$TECHNICAL_ALPHA_API_URL"', self.workflow)

    def test_release_procedure_requires_private_validation_and_redacted_summary(self) -> None:
        for term in (
            "python scripts/validate_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>",
            "python scripts/summarize_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>",
            "Post only this redacted summary", "Do not commit a completed device record",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.guide)

    def test_packaged_build_requires_authoritative_api_path_and_embedded_bundle(self) -> None:
        for term in ("/api/v1", "non-loopback endpoint", "EXPO_PUBLIC_API_URL", "assembleRelease"):
            with self.subTest(term=term):
                self.assertIn(term, self.builder)
        self.assertNotIn("assembleDebug", self.builder)
        self.assertIn("assets/index.android.bundle", self.workflow)
        self.assertIn("assets/index.android.bundle", self.verifier)
        self.assertIn("standalone-release-apk", self.workflow)
        self.assertIn("standalone-release-apk", self.verifier)


if __name__ == "__main__":
    unittest.main()
