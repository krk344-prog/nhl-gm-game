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

    def test_matching_complete_evidence_is_ready_for_approval(self):
        self.assertEqual([], validate(self._device(), self._stage3()))

    def test_package_identity_mismatch_blocks(self):
        stage3 = self._stage3()
        stage3["apk_sha256"] = "c" * 64
        self.assertIn("identity_mismatch:apk_sha256", validate(self._device(), stage3))

    def test_incomplete_route_and_major_defect_block(self):
        device = self._device()
        device["trade_passed"] = False
        stage3 = self._stage3()
        stage3["open_major_defects"] = ["TA-17"]
        errors = validate(device, stage3)
        self.assertIn("device_not_passed:trade_passed", errors)
        self.assertIn("stage3_major_defects_present", errors)


if __name__ == "__main__":
    unittest.main()
