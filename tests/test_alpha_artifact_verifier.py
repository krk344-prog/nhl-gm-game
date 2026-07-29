import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.verify_alpha_artifact import VerificationError, verify_artifact


class AlphaArtifactVerifierTests(unittest.TestCase):
    def _write_valid_artifact(self, directory: Path) -> tuple[str, str]:
        commit = "abc123def456"
        api_url = "http://192.168.1.25:8000/api/v1"
        apk = directory / "nhl-gm-technical-alpha.apk"
        with ZipFile(apk, "w") as archive:
            archive.writestr(
                "assets/index.android.bundle",
                f"standalone-js-bundle:{api_url}".encode("utf-8"),
            )
            archive.writestr("AndroidManifest.xml", b"manifest")
            archive.writestr("classes.dex", b"dex")
        export = directory / "nhl-gm-android-export.tar.gz"
        export.write_bytes(b"export-bytes")

        files = {
            apk.name: (apk.read_bytes(), "nhl-gm-technical-alpha.apk.sha256"),
            export.name: (export.read_bytes(), "nhl-gm-android-export.sha256"),
        }
        for name, (payload, checksum_name) in files.items():
            digest = hashlib.sha256(payload).hexdigest()
            (directory / checksum_name).write_text(
                f"{digest}  {name}\n", encoding="utf-8"
            )
        (directory / "technical-alpha-build.txt").write_text(
            f"commit={commit}\napi_base_url={api_url}\nbuild_type=standalone-release-apk\n",
            encoding="utf-8",
        )
        return commit, api_url

    def _rewrite_apk_checksum(self, directory: Path) -> None:
        apk = directory / "nhl-gm-technical-alpha.apk"
        digest = hashlib.sha256(apk.read_bytes()).hexdigest()
        (directory / "nhl-gm-technical-alpha.apk.sha256").write_text(
            f"{digest}  {apk.name}\n", encoding="utf-8"
        )

    def test_valid_artifact_matches_commit_endpoint_checksums_and_embedded_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)

            result = verify_artifact(directory, commit, api_url)

            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["commit"], commit)
            self.assertEqual(result["api_base_url"], api_url)
            self.assertGreater(result["embedded_bundle_bytes"], 0)
            self.assertTrue(result["embedded_endpoint_verified"])
            self.assertTrue(result["apk_zip_integrity_verified"])
            self.assertEqual(
                set(result["apk_required_members_verified"]),
                {"AndroidManifest.xml", "classes.dex"},
            )
            self.assertEqual(
                set(result["checksums"]),
                {"nhl-gm-technical-alpha.apk", "nhl-gm-android-export.tar.gz"},
            )

    def test_rejects_build_for_different_endpoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, _ = self._write_valid_artifact(directory)

            with self.assertRaisesRegex(VerificationError, "does not match expected URL"):
                verify_artifact(directory, commit, "http://192.168.1.30:8000/api/v1")

    def test_rejects_loopback_expected_endpoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, _ = self._write_valid_artifact(directory)

            with self.assertRaisesRegex(VerificationError, "loopback"):
                verify_artifact(directory, commit, "http://127.0.0.1:8000/api/v1")

    def test_rejects_tampered_apk(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)
            (directory / "nhl-gm-technical-alpha.apk").write_bytes(b"tampered")

            with self.assertRaisesRegex(VerificationError, "checksum mismatch"):
                verify_artifact(directory, commit, api_url)

    def test_rejects_nonportable_checksum_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)
            apk = directory / "nhl-gm-technical-alpha.apk"
            digest = hashlib.sha256(apk.read_bytes()).hexdigest()
            (directory / "nhl-gm-technical-alpha.apk.sha256").write_text(
                f"{digest}  /tmp/nhl-gm-technical-alpha.apk\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(VerificationError, "portable filename"):
                verify_artifact(directory, commit, api_url)

    def test_rejects_debug_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)
            (directory / "technical-alpha-build.txt").write_text(
                f"commit={commit}\napi_base_url={api_url}\nbuild_type=debug-apk\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(VerificationError, "unsupported build type"):
                verify_artifact(directory, commit, api_url)

    def test_rejects_apk_without_embedded_javascript_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)
            apk = directory / "nhl-gm-technical-alpha.apk"
            with ZipFile(apk, "w") as archive:
                archive.writestr("AndroidManifest.xml", b"manifest")
                archive.writestr("classes.dex", b"dex")
            self._rewrite_apk_checksum(directory)

            with self.assertRaisesRegex(VerificationError, "not standalone"):
                verify_artifact(directory, commit, api_url)

    def test_rejects_apk_missing_required_android_member(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)
            apk = directory / "nhl-gm-technical-alpha.apk"
            with ZipFile(apk, "w") as archive:
                archive.writestr(
                    "assets/index.android.bundle",
                    f"standalone-js-bundle:{api_url}".encode("utf-8"),
                )
                archive.writestr("classes.dex", b"dex")
            self._rewrite_apk_checksum(directory)

            with self.assertRaisesRegex(VerificationError, "missing required Android member: AndroidManifest.xml"):
                verify_artifact(directory, commit, api_url)

    def test_rejects_bundle_without_manifest_endpoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)
            apk = directory / "nhl-gm-technical-alpha.apk"
            with ZipFile(apk, "w") as archive:
                archive.writestr(
                    "assets/index.android.bundle",
                    b"standalone-js-bundle:http://192.168.1.99:8000/api/v1",
                )
                archive.writestr("AndroidManifest.xml", b"manifest")
                archive.writestr("classes.dex", b"dex")
            self._rewrite_apk_checksum(directory)

            with self.assertRaisesRegex(VerificationError, "does not contain the expected API endpoint"):
                verify_artifact(directory, commit, api_url)

    def test_rejects_checksum_valid_apk_with_corrupt_zip_member(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)
            apk = directory / "nhl-gm-technical-alpha.apk"
            payload = bytearray(apk.read_bytes())
            marker = f"standalone-js-bundle:{api_url}".encode("utf-8")
            marker_offset = payload.index(marker)
            payload[marker_offset] ^= 0x01
            apk.write_bytes(payload)
            self._rewrite_apk_checksum(directory)

            with self.assertRaisesRegex(VerificationError, "ZIP integrity check failed"):
                verify_artifact(directory, commit, api_url)


if __name__ == "__main__":
    unittest.main()
