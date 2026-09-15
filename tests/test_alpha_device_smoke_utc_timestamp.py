import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_alpha_device_smoke.py"
SPEC = importlib.util.spec_from_file_location("validate_alpha_device_smoke_utc", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AlphaDeviceSmokeUtcTimestampTests(unittest.TestCase):
    def valid_record(self):
        now = datetime.now(timezone.utc)
        record = {
            "commit_sha": "6852b06782766bd786ae7142a3347f54146c760b",
            "api_base_url": "http://192.168.1.25:8000/api/v1",
            "application_package": "com.krk344.nhlgmgame",
            "build_type": "standalone-release-apk",
            "device_model": "Pixel 9",
            "android_version": "16",
            "apk_sha256": "a" * 64,
            "qualified_at_utc": (now - timedelta(minutes=10)).isoformat(),
            "tested_at": now.isoformat(),
            "blockers": [],
        }
        for field in MODULE.REQUIRED_TRUE_FIELDS:
            record[field] = True
        return record

    def test_utc_device_smoke_timestamp_passes(self):
        self.assertNotIn("non_utc:tested_at", MODULE.validate_record(self.valid_record()))

    def test_non_utc_device_smoke_timestamp_is_blocked(self):
        record = self.valid_record()
        record["tested_at"] = datetime.now(timezone(timedelta(hours=-4))).isoformat()
        self.assertIn("non_utc:tested_at", MODULE.validate_record(record))


if __name__ == "__main__":
    unittest.main()
