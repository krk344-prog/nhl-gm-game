from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_alpha_stage3_capture import validate_record


TEMPLATE_PATH = Path("docs/technical_alpha_stage3_capture_record.template.json")


def passing_record() -> dict:
    record = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    record.update(
        commit_sha="a" * 40,
        apk_sha256="b" * 64,
        api_base_url="http://192.168.1.25:8000/api/v1",
        endpoint_class="private_lan",
        anonymous_tester_id="tester-01",
        route_result_reference="private/session-01.json",
        captured_at="2026-08-02T11:30:00Z",
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
    def test_complete_exact_package_record_passes(self) -> None:
        self.assertEqual([], validate_record(passing_record()))

    def test_missing_api_endpoint_blocks(self) -> None:
        record = passing_record()
        record["api_base_url"] = ""
        self.assertIn("missing_or_blank:api_base_url", validate_record(record))

    def test_missing_non_ideal_capture_blocks(self) -> None:
        record = passing_record()
        del record["captures"]["S3-09"]
        self.assertIn("missing:capture.S3-09", validate_record(record))

    def test_mislabeled_capture_state_blocks(self) -> None:
        record = passing_record()
        record["captures"]["S3-09"]["state"] = "standings"
        self.assertIn("invalid_state:capture.S3-09", validate_record(record))

    def test_failed_privacy_and_major_defect_block(self) -> None:
        record = passing_record()
        record["ui_checks"]["privacy_boundary_passed"] = False
        record["open_major_defects"] = ["MAJOR-1"]
        errors = validate_record(record)
        self.assertIn("not_passed:ui_checks.privacy_boundary_passed", errors)
        self.assertIn("major_defects_present", errors)

    def test_template_is_intentionally_not_ready(self) -> None:
        template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        errors = validate_record(copy.deepcopy(template))
        self.assertIn("missing_or_blank:api_base_url", errors)
        self.assertIn("invalid:stage3_decision", errors)
        self.assertIn("not_passed:capture.S3-01", errors)
        self.assertIn("not_passed:capture.S3-09", errors)


if __name__ == "__main__":
    unittest.main()
