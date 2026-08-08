import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_alpha_device_smoke.py"
SPEC = importlib.util.spec_from_file_location("validate_alpha_device_smoke", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AlphaDeviceSmokeValidatorTests(unittest.TestCase):
    def valid_record(self):
        record = {
            "commit_sha": "1709302f98d1ae8113ed643ee97b1566ad387fba",
            "api_base_url": "http://192.168.1.25:8000/api/v1",
            "device_model": "Pixel 9",
            "android_version": "16",
            "apk_sha256": "a" * 64,
            "tested_at": "2026-07-24T23:50:00-04:00",
            "blockers": [],
        }
        for field in MODULE.REQUIRED_TRUE_FIELDS:
            record[field] = True
        return record

    def test_valid_exact_package_record_passes(self):
        self.assertEqual([], MODULE.validate_record(self.valid_record()))

    def test_abbreviated_commit_sha_is_blocked(self):
        record = self.valid_record()
        record["commit_sha"] = "1709302"
        self.assertIn("invalid:commit_sha", MODULE.validate_record(record))

    def test_loopback_endpoint_is_blocked(self):
        record = self.valid_record()
        record["api_base_url"] = "http://127.0.0.1:8000/api/v1"
        self.assertIn("loopback:api_base_url", MODULE.validate_record(record))

    def test_localhost_subdomain_endpoint_is_blocked(self):
        record = self.valid_record()
        record["api_base_url"] = "http://alpha.localhost:8000/api/v1"
        self.assertIn("loopback:api_base_url", MODULE.validate_record(record))

    def test_endpoint_with_credentials_is_blocked(self):
        record = self.valid_record()
        record["api_base_url"] = "http://tester:secret@192.168.1.25:8000/api/v1"
        self.assertIn("noncanonical:api_base_url", MODULE.validate_record(record))

    def test_endpoint_with_query_is_blocked(self):
        record = self.valid_record()
        record["api_base_url"] = "http://192.168.1.25:8000/api/v1?token=secret"
        self.assertIn("noncanonical:api_base_url", MODULE.validate_record(record))

    def test_endpoint_with_fragment_is_blocked(self):
        record = self.valid_record()
        record["api_base_url"] = "http://192.168.1.25:8000/api/v1#device"
        self.assertIn("noncanonical:api_base_url", MODULE.validate_record(record))

    def test_failed_save_reload_blocks_pilot(self):
        record = self.valid_record()
        record["save_reload_passed"] = False
        self.assertIn("not_passed:save_reload_passed", MODULE.validate_record(record))

    def test_unconfirmed_launch_blocks_pilot(self):
        record = self.valid_record()
        record["launch_confirmed"] = False
        self.assertIn("not_passed:launch_confirmed", MODULE.validate_record(record))

    def test_tampered_digest_is_blocked(self):
        record = self.valid_record()
        record["apk_sha256"] = "not-a-digest"
        self.assertIn("invalid:apk_sha256", MODULE.validate_record(record))

    def test_timezone_less_timestamp_is_blocked(self):
        record = self.valid_record()
        record["tested_at"] = "2026-07-24T23:50:00"
        self.assertIn("invalid:tested_at", MODULE.validate_record(record))

    def test_malformed_timestamp_is_blocked(self):
        record = self.valid_record()
        record["tested_at"] = "last Friday evening"
        self.assertIn("invalid:tested_at", MODULE.validate_record(record))

    def test_declared_blocker_blocks_record(self):
        record = self.valid_record()
        record["blockers"] = ["trade history missing after restart"]
        self.assertIn("blockers_present", MODULE.validate_record(record))


if __name__ == "__main__":
    unittest.main()