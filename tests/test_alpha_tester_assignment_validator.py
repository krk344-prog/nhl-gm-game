import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_alpha_tester_assignment.py"
SPEC = importlib.util.spec_from_file_location("validate_alpha_tester_assignment", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def complete_assignment():
    return {
        "schema_version": 1,
        "package_identity": {
            "pr_number": 13,
            "commit_sha": "a" * 40,
            "apk_sha256": "b" * 64,
            "android_package": "com.krk344.nhlgmgame",
            "build_type": "release",
            "endpoint_class": "private-lan",
        },
        "session": {
            "tester_count": 3,
            "fictional_alpha_disclosure_acknowledged": True,
            "known_limitations_acknowledged": True,
            "facilitator_coaching_deferred_until_first_interpretation": True,
        },
        "testers": [
            {
                "code": "T01",
                "device_class": "Pixel-class Android phone",
                "primary_routes": ["application_launch", "new_game", "franchise_selection", "advance_day"],
                "backup_routes": ["roster", "standings"],
                "disclosure_acknowledged": True,
                "first_interpretation_recorded": True,
                "highest_friction_moment_recorded": True,
                "confidence_building_moment_recorded": True,
            },
            {
                "code": "T02",
                "device_class": "Samsung-class Android phone",
                "primary_routes": ["roster", "standings", "trade"],
                "backup_routes": ["save", "reload"],
                "disclosure_acknowledged": True,
                "first_interpretation_recorded": True,
                "highest_friction_moment_recorded": True,
                "confidence_building_moment_recorded": True,
            },
            {
                "code": "T03",
                "device_class": "Android tablet",
                "primary_routes": ["save", "reload", "reset"],
                "backup_routes": ["application_launch", "new_game", "franchise_selection", "advance_day", "trade", "reset"],
                "disclosure_acknowledged": True,
                "first_interpretation_recorded": True,
                "highest_friction_moment_recorded": True,
                "confidence_building_moment_recorded": True,
            },
        ],
        "ui_review": {
            "stage2_direction_preserved": True,
            "implemented_screens_status": "UI Review Pending",
            "required_stage3_capture_count": 9,
        },
        "authorization": {
            "pilot_approved_by_kyle": False,
            "merge_approved_by_kyle": False,
        },
    }


class AlphaTesterAssignmentValidatorTests(unittest.TestCase):
    def test_complete_assignment_passes(self):
        self.assertEqual([], MODULE.validate_assignment(complete_assignment()))

    def test_missing_backup_blocks(self):
        assignment = complete_assignment()
        assignment["testers"][2]["backup_routes"].remove("reset")
        errors = MODULE.validate_assignment(assignment)
        self.assertIn("route reset must have at least one backup observer", errors)

    def test_duplicate_primary_owner_blocks(self):
        assignment = complete_assignment()
        assignment["testers"][1]["primary_routes"].append("new_game")
        errors = MODULE.validate_assignment(assignment)
        self.assertIn("route new_game must have exactly one primary owner", errors)

    def test_coaching_or_premature_approval_blocks(self):
        assignment = copy.deepcopy(complete_assignment())
        assignment["session"]["facilitator_coaching_deferred_until_first_interpretation"] = False
        assignment["authorization"]["pilot_approved_by_kyle"] = True
        errors = MODULE.validate_assignment(assignment)
        self.assertIn("facilitator must defer coaching until first interpretation is recorded", errors)
        self.assertIn("pilot approval must remain false until Kyle explicitly approves", errors)


if __name__ == "__main__":
    unittest.main()
