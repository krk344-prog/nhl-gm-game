import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_alpha_device_smoke.py"
SPEC = importlib.util.spec_from_file_location("validate_alpha_device_smoke_trade_history", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AlphaDeviceSmokeTradeHistoryTests(unittest.TestCase):
    def valid_record(self):
        record = {
            "commit_sha": "1709302f98d1ae8113ed643ee97b1566ad387fba",
            "api_base_url": "http://192.168.1.25:8000/api/v1",
            "application_package": "com.krk344.nhlgmgame",
            "build_type": "standalone-release-apk",
            "device_model": "Pixel 9",
            "android_version": "16",
            "apk_sha256": "a" * 64,
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "blockers": [],
        }
        for field in MODULE.REQUIRED_TRUE_FIELDS:
            record[field] = True
        return record

    def test_trade_history_is_required_for_device_smoke(self):
        record = self.valid_record()
        record["trade_history_passed"] = False
        self.assertIn("not_passed:trade_history_passed", MODULE.validate_record(record))

    def test_missing_trade_history_is_blocked(self):
        record = self.valid_record()
        record.pop("trade_history_passed")
        self.assertIn("not_passed:trade_history_passed", MODULE.validate_record(record))


if __name__ == "__main__":
    unittest.main()
