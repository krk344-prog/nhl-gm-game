from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.validate_alpha_stage3_capture import validate_record


TEMPLATE_PATH = Path("docs/technical_alpha_stage3_capture_record.template.json")
TEST_NOW = datetime(2026, 8, 27, 22, 0, 0, tzinfo=timezone.utc)


def passing_record() -> dict:
    record = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    record.update(
        commit_sha="a" * 40,
        apk_sha256="b" * 64,
        api_base_url="http://192.168.1.25:8000/api/v1",
        endpoint_class="private_lan",
        anonymous_tester_id="T01",
        route_result_reference="private/route-result.json",
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


class AlphaStage3RouteReferenceTests(unittest.TestCase):
    def test_route_result_reference_must_remain_in_private_evidence_tree(self) -> None:
        self.assertEqual([], validate_record(passing_record(), now=TEST_NOW))

        for reference in (
            "/tmp/route-result.json",
            "../outside/route-result.json",
            "private/../../outside/route-result.json",
            r"C:\temp\route-result.json",
            "reports/route-result.json",
            "private",
            "private/",
        ):
            with self.subTest(reference=reference):
                record = passing_record()
                record["route_result_reference"] = reference
                self.assertIn("invalid:route_result_reference", validate_record(record, now=TEST_NOW))

    def test_capture_reference_requires_a_private_evidence_leaf(self) -> None:
        for reference in ("private", "private/"):
            with self.subTest(reference=reference):
                record = passing_record()
                record["captures"]["S3-01"]["private_reference"] = reference
                self.assertIn("invalid_private_reference:capture.S3-01", validate_record(record, now=TEST_NOW))


if __name__ == "__main__":
    unittest.main()
