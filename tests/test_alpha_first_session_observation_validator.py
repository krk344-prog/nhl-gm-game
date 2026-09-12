import copy
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_alpha_first_session_observation.py"
SPEC = importlib.util.spec_from_file_location("validate_alpha_first_session_observation", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def complete_observation():
    return {
        "schema_version": 1,
        "package_identity": {
            "pr_number": 13,
            "commit_sha": "a" * 40,
            "apk_sha256": "b" * 64,
            "android_package": "com.krk344.nhlgmgame",
            "build_type": "release",
            "api_base_url": "http://192.168.1.50:8000/api/v1",
        },
        "observation": {
            "tester_code": "T01",
            "fictional_alpha_disclosure_acknowledged": True,
            "coaching_withheld_until_first_interpretation": True,
            "first_interpretation": "This is a hockey front-office simulation with a clear new-game path.",
            "first_attempted_action": "Selected New Game and reviewed franchise choices.",
            "highest_friction_moment": "Needed a moment to distinguish standings from the game-day view.",
            "independent_next_step": "Use Advance Day after reviewing the current roster.",
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


class AlphaFirstSessionObservationValidatorTests(unittest.TestCase):
    def test_complete_observation_passes(self):
        self.assertEqual([], MODULE.validate_observation(complete_observation()))

    def test_non_release_build_blocks(self):
        payload = complete_observation()
        payload["package_identity"]["build_type"] = "debug"
        self.assertIn(
            "first-session evidence must come from a release APK build",
            MODULE.validate_observation(payload),
        )

    def test_coaching_or_missing_route_blocks(self):
        payload = complete_observation()
        payload["observation"]["coaching_withheld_until_first_interpretation"] = False
        payload["observation"]["advance_day_identified_without_coaching"] = False
        errors = MODULE.validate_observation(payload)
        self.assertIn("facilitator coaching must be withheld until first interpretation is recorded", errors)
        self.assertIn("tester must independently identify how to advance the day", errors)

    def test_private_detail_blocks(self):
        payload = complete_observation()
        payload["observation"]["highest_friction_moment"] = "Device serial was copied into the report."
        self.assertIn("highest_friction_moment contains prohibited private detail", MODULE.validate_observation(payload))

    def test_premature_approval_or_ui_status_blocks(self):
        payload = copy.deepcopy(complete_observation())
        payload["authorization"]["pilot_approved_by_kyle"] = True
        payload["ui_review"]["implemented_screens_status"] = "UI Approved"
        errors = MODULE.validate_observation(payload)
        self.assertIn("pilot approval must remain false until Kyle explicitly approves", errors)
        self.assertIn("implemented screens must remain UI Review Pending", errors)

    def test_missing_or_local_endpoint_blocks(self):
        payload = complete_observation()
        payload["package_identity"]["api_base_url"] = ""
        errors = MODULE.validate_observation(payload)
        self.assertIn(
            "api_base_url must be the explicit tester-reachable authoritative /api/v1 http(s) endpoint without credentials, query, or fragment",
            errors,
        )

        payload["package_identity"]["api_base_url"] = "http://127.0.0.1:8000/api/v1"
        errors = MODULE.validate_observation(payload)
        self.assertIn(
            "api_base_url must be the explicit tester-reachable authoritative /api/v1 http(s) endpoint without credentials, query, or fragment",
            errors,
        )

    def test_credential_bearing_endpoint_blocks(self):
        payload = complete_observation()
        payload["package_identity"]["api_base_url"] = "https://tester:secret@example.test/api/v1"
        self.assertIn(
            "api_base_url must be the explicit tester-reachable authoritative /api/v1 http(s) endpoint without credentials, query, or fragment",
            MODULE.validate_observation(payload),
        )

    def test_non_authoritative_path_query_or_fragment_blocks(self):
        for endpoint in (
            "http://192.168.1.50:8000/health",
            "http://192.168.1.50:8000/api/v1?debug=1",
            "http://192.168.1.50:8000/api/v1#session",
        ):
            with self.subTest(endpoint=endpoint):
                payload = complete_observation()
                payload["package_identity"]["api_base_url"] = endpoint
                self.assertIn(
                    "api_base_url must be the explicit tester-reachable authoritative /api/v1 http(s) endpoint without credentials, query, or fragment",
                    MODULE.validate_observation(payload),
                )


if __name__ == "__main__":
    unittest.main()
