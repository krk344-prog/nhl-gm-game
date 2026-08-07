import unittest

from scripts.validate_alpha_pilot_readiness import DEVICE_PASSES, validate


class AlphaPilotReadinessValidatorTests(unittest.TestCase):
    def _device(self):
        record = {
            "commit_sha": "a" * 40,
            "apk_sha256": "b" * 64,
            "blockers": [],
        }
        record.update({field: True for field in DEVICE_PASSES})
        return record

    def _stage3(self):
        return {
            "commit_sha": "a" * 40,
            "apk_sha256": "b" * 64,
            "application_package": "com.krk344.nhlgmgame",
            "build_type": "standalone-release-apk",
            "stage3_decision": "COMPLETE_UI_REVIEW_PENDING",
            "blockers": [],
            "open_major_defects": [],
        }

    def _first_session(self):
        return {
            "schema_version": 1,
            "package_identity": {
                "pr_number": 13,
                "commit_sha": "a" * 40,
                "apk_sha256": "b" * 64,
                "android_package": "com.krk344.nhlgmgame",
            },
            "observation": {
                "tester_code": "T01",
                "fictional_alpha_disclosure_acknowledged": True,
                "coaching_withheld_until_first_interpretation": True,
                "first_interpretation": "The dashboard shows the next management decision.",
                "first_attempted_action": "Selected a franchise.",
                "highest_friction_moment": "Locating the standings tab took one scan.",
                "independent_next_step": "Advance Day",
                "launch_reached": True,
                "franchise_selection_reached": True,
                "advance_day_identified_without_coaching": True,
            },
            "ui_review": {
                "implemented_screens_status": "UI Review Pending",
                "stage2_direction_preserved": True,
            },
            "authorization": {
                "pilot_approved_by_kyle": False,
                "merge_approved_by_kyle": False,
            },
        }

    def test_matching_complete_evidence_is_ready_for_approval(self):
        self.assertEqual(
            [], validate(self._device(), self._stage3(), self._first_session())
        )

    def test_package_identity_mismatch_blocks(self):
        first_session = self._first_session()
        first_session["package_identity"]["apk_sha256"] = "c" * 64
        self.assertIn(
            "identity_mismatch:apk_sha256",
            validate(self._device(), self._stage3(), first_session),
        )

    def test_matching_but_malformed_hashes_block(self):
        device = self._device()
        stage3 = self._stage3()
        first_session = self._first_session()
        for record in (device, stage3):
            record["commit_sha"] = "not-a-commit"
            record["apk_sha256"] = "not-a-sha256"
        first_session["package_identity"]["commit_sha"] = "not-a-commit"
        first_session["package_identity"]["apk_sha256"] = "not-a-sha256"
        errors = validate(device, stage3, first_session)
        self.assertIn("invalid_format:commit_sha", errors)
        self.assertIn("invalid_format:apk_sha256", errors)
        self.assertNotIn("identity_mismatch:commit_sha", errors)
        self.assertNotIn("identity_mismatch:apk_sha256", errors)

    def test_incomplete_route_and_major_defect_block(self):
        device = self._device()
        device["trade_passed"] = False
        stage3 = self._stage3()
        stage3["open_major_defects"] = ["TA-17"]
        errors = validate(device, stage3, self._first_session())
        self.assertIn("device_not_passed:trade_passed", errors)
        self.assertIn("stage3_major_defects_present", errors)

    def test_coached_or_incomplete_first_session_blocks(self):
        first_session = self._first_session()
        first_session["observation"][
            "coaching_withheld_until_first_interpretation"
        ] = False
        first_session["observation"][
            "advance_day_identified_without_coaching"
        ] = False
        errors = validate(self._device(), self._stage3(), first_session)
        self.assertTrue(
            any(error.startswith("first_session:") for error in errors), errors
        )


if __name__ == "__main__":
    unittest.main()
