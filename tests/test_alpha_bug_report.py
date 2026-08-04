from __future__ import annotations

import copy
import unittest

from scripts.validate_alpha_bug_report import validate_report


class AlphaBugReportValidationTests(unittest.TestCase):
    def valid_report(self) -> dict:
        return {
            "schema_version": 1,
            "package_identity": {
                "pr_number": 13,
                "commit_sha": "a" * 40,
                "apk_sha256": "b" * 64,
                "android_package": "com.krk344.nhlgmgame",
            },
            "report": {
                "tester_code": "T01",
                "severity": "Major",
                "route": "reload",
                "reproducible": True,
                "expected": "The selected franchise and current day remain unchanged after reload.",
                "actual": "The application returned to franchise selection.",
                "steps": ["Select a franchise", "Advance one day", "Close and reopen the app"],
                "first_interpretation": "I thought my save had been deleted.",
                "highest_friction_moment": "There was no visible explanation of whether reload succeeded.",
                "fictional_alpha_limitation_acknowledged": True,
                "ui_status": "UI Review Pending",
            },
            "attachments": [
                {"kind": "screenshot", "reference": "private-evidence/reload-01", "privacy_reviewed": True}
            ],
            "authorization": {
                "pilot_approved_by_kyle": False,
                "merge_approved_by_kyle": False,
            },
        }

    def test_complete_report_passes(self) -> None:
        self.assertEqual(validate_report(self.valid_report()), [])

    def test_private_identity_field_blocks(self) -> None:
        report = self.valid_report()
        report["report"]["tester_name"] = "Private Tester"
        self.assertIn("report contains a prohibited private field", validate_report(report))

    def test_unknown_route_and_missing_first_interpretation_block(self) -> None:
        report = self.valid_report()
        report["report"]["route"] = "scouting"
        report["report"]["first_interpretation"] = ""
        errors = validate_report(report)
        self.assertIn("route is not part of the controlled Alpha smoke path", errors)
        self.assertIn("first interpretation must be recorded before coaching", errors)

    def test_unreviewed_attachment_and_premature_approval_block(self) -> None:
        report = copy.deepcopy(self.valid_report())
        report["attachments"][0]["privacy_reviewed"] = False
        report["authorization"]["pilot_approved_by_kyle"] = True
        errors = validate_report(report)
        self.assertIn("attachment 1 must be privacy reviewed", errors)
        self.assertIn("pilot approval must remain false until Kyle explicitly approves", errors)


if __name__ == "__main__":
    unittest.main()
