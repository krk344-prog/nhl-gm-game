import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.verify_alpha_artifact import VerificationError, verify_artifact


class AlphaArtifactVerifierTests(unittest.TestCase):
    def _write_valid_artifact(self, directory: Path) -> tuple[str, str]:
        commit = "abc123def456"
        api_url = "http://192.168.1.25:8000/api/v1"
        files = {
            "nhl-gm-technical-alpha.apk": (
                b"apk-bytes",
                "nhl-gm-technical-alpha.apk.sha256",
            ),
            "nhl-gm-android-export.tar.gz": (
                b"export-bytes",
                "nhl-gm-android-export.sha256",
            ),
        }
        for name, (payload, checksum_name) in files.items():
            (directory / name).write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            (directory / checksum_name).write_text(
                f"{digest}  {name}\n", encoding="utf-8"
            )
        (directory / "technical-alpha-build.txt").write_text(
            f"commit={commit}\napi_base_url={api_url}\nbuild_type=debug-apk\n",
            encoding="utf-8",
        )
        return commit, api_url

    def test_valid_artifact_matches_commit_endpoint_and_checksums(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            commit, api_url = self._write_valid_artifact(directory)

            result = verify_artifact(directory, commit, api_url)

            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["commit"], commit)
            self.assertEqual(result["api_base_url"], api_url)
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
            digest = hashlib.sha256(b"apk-bytes").hexdigest()
            (directory / "nhl-gm-technical-alpha.apk.sha256").write_text(
                f"{digest}  /tmp/nhl-gm-technical-alpha.apk\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(VerificationError, "portable filename"):
                verify_artifact(directory, commit, api_url)


if __name__ == "__main__":
    unittest.main()
