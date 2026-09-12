import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.verify_alpha_artifact import VerificationError, _read_build_manifest


class AlphaArtifactManifestTimestampTests(unittest.TestCase):
    def _write_manifest(self, directory: Path, qualified_at_utc: str) -> Path:
        path = directory / "technical-alpha-build.txt"
        path.write_text(
            (
                "commit=abc123def456\n"
                "api_base_url=http://192.168.1.25:8000/api/v1\n"
                "build_type=standalone-release-apk\n"
                f"qualified_at_utc={qualified_at_utc}\n"
            ),
            encoding="utf-8",
        )
        return path

    def test_accepts_timezone_aware_utc_qualification_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = _read_build_manifest(
                self._write_manifest(Path(temp_dir), "2026-09-12T07:00:00+00:00")
            )

            self.assertEqual(manifest["qualified_at_utc"], "2026-09-12T07:00:00+00:00")

    def test_rejects_malformed_qualification_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._write_manifest(Path(temp_dir), "not-a-timestamp")

            with self.assertRaisesRegex(VerificationError, "valid ISO-8601 timestamp"):
                _read_build_manifest(path)

    def test_rejects_timezone_naive_qualification_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._write_manifest(Path(temp_dir), "2026-09-12T07:00:00")

            with self.assertRaisesRegex(VerificationError, "timezone-aware"):
                _read_build_manifest(path)

    def test_rejects_non_utc_qualification_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._write_manifest(Path(temp_dir), "2026-09-12T03:00:00-04:00")

            with self.assertRaisesRegex(VerificationError, "must use UTC"):
                _read_build_manifest(path)

    def test_rejects_qualification_timestamp_materially_in_future(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._write_manifest(Path(temp_dir), future.isoformat())

            with self.assertRaisesRegex(VerificationError, "must not be in the future"):
                _read_build_manifest(path)


if __name__ == "__main__":
    unittest.main()
