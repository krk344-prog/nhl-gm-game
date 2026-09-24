import importlib.util
import json
import unittest
from datetime import datetime, timedelta, timezone
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

    def completed_record(self):
        record = self.load_template()
        now = datetime.now(timezone.utc)
        record.update(
            {
                "commit_sha": "a24e0c4fdf43d87d5a6752ab0bfd96dcdeb27e71",
                "api_base_url": "http://192.168.1.25:8000/api/v1",
                "device_model": "Pixel 9",
                "android_version": "16",
                "apk_sha256": "a" * 64,
                "qualified_at_utc": (now - timedelta(minutes=10)).isoformat(),
                "tested_at": now.isoformat(),
                "blockers": [],
            }
        )
        for field in VALIDATOR.REQUIRED_TRUE_FIELDS:
            record[field] = True
        return record

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
        self.assertIn("REPLACE_WITH", record["qualified_at_utc"])

    def test_completed_copy_of_template_passes_validator(self):
        self.assertEqual([], VALIDATOR.validate_record(self.completed_record()))

    def test_qualification_provenance_is_required_and_must_precede_device_test(self):
        missing = self.completed_record()
        missing.pop("qualified_at_utc")
        self.assertIn("missing_or_blank:qualified_at_utc", VALIDATOR.validate_record(missing))

        after_test = self.completed_record()
        tested_at = datetime.fromisoformat(after_test["tested_at"])
        after_test["qualified_at_utc"] = (tested_at + timedelta(minutes=10)).isoformat()
        self.assertIn("after_test:qualified_at_utc", VALIDATOR.validate_record(after_test))

        non_utc = self.completed_record()
        non_utc["qualified_at_utc"] = datetime.now(timezone(timedelta(hours=-4))).isoformat()
        self.assertIn("non_utc:qualified_at_utc", VALIDATOR.validate_record(non_utc))


if __name__ == "__main__":
    unittest.main()