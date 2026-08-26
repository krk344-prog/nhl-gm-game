from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.validate_alpha_stage3_capture import MAX_EVIDENCE_AGE, validate_record


TEMPLATE_PATH = Path("docs/technical_alpha_stage3_capture_record.template.json")
TEST_NOW = datetime(2026, 8, 26, 20, 0, 0, tzinfo=timezone.utc)


def passing_record() -> dict:
    record = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    record.update(
        commit_sha="a" * 40,
        apk_sha256="b" * 64,
        api_base_url="http://192.168.1.25:8000/api/v1",
        endpoint_class="private_lan",
        anonymous_tester_id="tester-01",
        route_result_reference="private/session-01.json",
        captured_at=(TEST_NOW - timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        stage3_decision="COMPLETE_UI_REVIEW_PENDING",
    )
    for key in record["preconditions"]:
        record["preconditions"][key] = True
    for capture_id, capture in record["captures"].items():
        capture["result"] = "PASS"
        capture["private_reference"] = f"private/{capture_id}.png"
    for key in record["ui_checks"]:
        record["ui_checks"][key] = True
    for key in record["sign_off"]:
        record["sign_off"][key] = "reviewer"
    return record


class AlphaStage3CaptureValidatorTests(unittest.TestCase):
    def validate(self, record: dict) -> list[str]:
        return validate_record(record, now=TEST_NOW)

    def test_complete_exact_package_record_passes(self) -> None:
        self.assertEqual([], self.validate(passing_record()))

    def test_missing_api_endpoint_blocks(self) -> None:
        record = passing_record()
        record["api_base_url"] = ""
        self.assertIn("missing_or_blank:api_base_url", self.validate(record))

    def test_non_authoritative_or_unsafe_api_endpoint_blocks(self) -> None:
        for endpoint in (
            "http://192.168.1.25:8000/health",
            "http://127.0.0.1:8000/api/v1",
            "http://tester:secret@192.168.1.25:8000/api/v1",
            "http://192.168.1.25:8000/api/v1?debug=1",
        ):
            with self.subTest(endpoint=endpoint):
                record = passing_record()
                record["api_base_url"] = endpoint
                self.assertIn("invalid:api_base_url", self.validate(record))

    def test_capture_timestamp_must_be_unambiguous_utc(self) -> None:
        for captured_at in (
            "2026-08-26 19:00:00",
            "2026-08-26T19:00:00",
            "2026-08-26T15:00:00-04:00",
            "not-a-timestamp",
        ):
            with self.subTest(captured_at=captured_at):
                record = passing_record()
                record["captured_at"] = captured_at
                self.assertIn("invalid:captured_at", self.validate(record))

    def test_stale_or_future_capture_timestamp_blocks(self) -> None:
        stale = passing_record()
        stale["captured_at"] = (TEST_NOW - MAX_EVIDENCE_AGE - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        self.assertIn("stale:captured_at", self.validate(stale))

        future = passing_record()
        future["captured_at"] = (TEST_NOW + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        self.assertIn("future:captured_at", self.validate(future))

    def test_missing_non_ideal_capture_blocks(self) -> None:
        record = passing_record()
        del record["captures"]["S3-09"]
        self.assertIn("missing:capture.S3-09", self.validate(record))

    def test_mislabeled_capture_state_blocks(self) -> None:
        record = passing_record()
        record["captures"]["S3-09"]["state"] = "standings"
        self.assertIn("invalid_state:capture.S3-09", self.validate(record))

    def test_failed_privacy_and_major_defect_block(self) -> None:
        record = passing_record()
        record["ui_checks"]["privacy_boundary_passed"] = False
        record["open_major_defects"] = ["MAJOR-1"]
        errors = self.validate(record)
        self.assertIn("not_passed:ui_checks.privacy_boundary_passed", errors)
        self.assertIn("major_defects_present", errors)

    def test_template_is_intentionally_not_ready(self) -> None:
        template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        errors = self.validate(copy.deepcopy(template))
        self.assertIn("missing_or_blank:api_base_url", errors)
        self.assertIn("invalid:stage3_decision", errors)
        self.assertIn("not_passed:capture.S3-01", errors)
        self.assertIn("not_passed:capture.S3-09", errors)


if __name__ == "__main__":
    unittest.main()
