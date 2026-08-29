import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from scripts.create_alpha_tester_bundle import BundleError, create_tester_bundle
from scripts.verify_alpha_artifact import VerificationError


class CreateAlphaTesterBundleTests(unittest.TestCase):
    def _write_artifacts(self, directory: Path) -> tuple[str, str]:
        commit = "64e1715952ebe7776605b898fdc6998e1c204e9f"
        api_url = "http://192.168.1.25:8000/api/v1"
        (directory / "nhl-gm-technical-alpha.apk").write_bytes(b"apk")
        (directory / "nhl-gm-technical-alpha.apk.sha256").write_text(
            "abc  nhl-gm-technical-alpha.apk\n", encoding="utf-8"
        )
        (directory / "technical-alpha-build.txt").write_text(
            f"commit={commit}\napi_base_url={api_url}\nbuild_type=standalone-release-apk\n",
            encoding="utf-8",
        )
        return commit, api_url

    @patch("scripts.create_alpha_tester_bundle.verify_artifact")
    def test_creates_single_plain_language_privacy_safe_tester_zip(self, verify):
        verify.return_value = {
            "build_type": "standalone-release-apk",
            "checksums": {"nhl-gm-technical-alpha.apk": "abc"},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_artifacts(directory)
            output = directory / "handoff.zip"

            result = create_tester_bundle(directory, output)

            verify.assert_called_once_with(directory.resolve(), commit, api_url)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["endpoint_class"], "private-lan")
            with ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertEqual(names, set(result["files"]))
                self.assertNotIn(
                    "NHL-GM-First-Playable/technical-alpha-build.txt", names
                )
                start_here = archive.read(
                    "NHL-GM-First-Playable/START-HERE.txt"
                ).decode("utf-8")
                bug_report = archive.read(
                    "NHL-GM-First-Playable/BUG-REPORT.txt"
                ).decode("utf-8")
                build_info = archive.read(
                    "NHL-GM-First-Playable/BUILD-INFO.txt"
                ).decode("utf-8")
                self.assertIn("eight fictional franchises", start_here)
                self.assertIn("Advance the day", start_here)
                self.assertIn("Open Trade History", start_here)
                self.assertIn("Save the game", start_here)
                self.assertIn("Reload the saved game", start_here)
                self.assertIn("Trade History persist", start_here)
                self.assertIn("Generate the debug report", start_here)
                self.assertIn("privacy-reviewed output", start_here)
                self.assertIn("returns to Day 1", start_here)
                self.assertLess(start_here.index("Open Trade History"), start_here.index("Save the game"))
                self.assertLess(start_here.index("Save the game"), start_here.index("Reload the saved game"))
                self.assertIn("Anonymous tester code (T## only; no name):", bug_report)
                self.assertNotIn("Anonymous tester code:\n", bug_report)
                self.assertIn(f"Build: {commit[:12]}", bug_report)
                self.assertIn("Build type: standalone-release-apk", bug_report)
                self.assertIn("Package: com.krk344.nhlgmgame", bug_report)
                self.assertIn("Endpoint class: private-lan", bug_report)
                self.assertIn("APK SHA-256: abc", bug_report)
                self.assertIn("endpoint_class=private-lan", build_info)
                self.assertNotIn(api_url, start_here)
                self.assertNotIn(api_url, bug_report)
                self.assertNotIn(api_url, build_info)

    def test_rejects_incomplete_manifest_before_packaging(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "technical-alpha-build.txt").write_text(
                "commit=abc\nbuild_type=standalone-release-apk\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(BundleError, "incomplete"):
                create_tester_bundle(directory, directory / "handoff.zip")

    @patch("scripts.create_alpha_tester_bundle.verify_artifact")
    def test_does_not_create_zip_when_exact_package_verification_fails(self, verify):
        verify.side_effect = VerificationError("checksum mismatch")
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            self._write_artifacts(directory)
            output = directory / "handoff.zip"

            with self.assertRaisesRegex(VerificationError, "checksum mismatch"):
                create_tester_bundle(directory, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
