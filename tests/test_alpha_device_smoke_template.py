import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "technical_alpha_device_smoke_record.template.json"
VALIDATOR_PATH = ROOT / "scripts" / "validate_alpha_device_smoke.py"
SPEC = importlib.util.spec_from_file_location("validate_alpha_device_smoke", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class AlphaDeviceSmokeTemplateTests(unittest.TestCase):
    def load_template(self):
        return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

    def test_template_contains_every_validator_field_and_starts_blocked(self):
        record = self.load_template()

        for field in VALIDATOR.REQUIRED_TEXT_FIELDS:
            self.assertIn(field, record)
        for field in VALIDATOR.REQUIRED_TRUE_FIELDS:
            self.assertIn(field, record)
            self.assertIs(record[field], False)

        self.assertTrue(record["blockers"])
        self.assertIn("REPLACE_WITH", record["commit_sha"])
        self.assertIn("REPLACE_WITH", record["api_base_url"])

    def test_completed_copy_of_template_passes_validator(self):
        record = self.load_template()
        record.update(
            {
                "commit_sha": "a24e0c4fdf43d87d5a6752ab0bfd96dcdeb27e71",
                "api_base_url": "http://192.168.1.25:8000/api/v1",
                "device_model": "Pixel 9",
                "android_version": "16",
                "apk_sha256": "a" * 64,
                "tested_at": datetime.now(timezone.utc).isoformat(),
                "blockers": [],
            }
        )
        for field in VALIDATOR.REQUIRED_TRUE_FIELDS:
            record[field] = True

        self.assertEqual([], VALIDATOR.validate_record(record))


if __name__ == "__main__":
    unittest.main()
