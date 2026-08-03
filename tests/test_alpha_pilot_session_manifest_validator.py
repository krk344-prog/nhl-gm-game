import copy
import json
import unittest
from pathlib import Path

from scripts.validate_alpha_pilot_session_manifest import validate_manifest


TEMPLATE = Path("docs/technical_alpha_pilot_session_manifest.template.json")


class AlphaPilotSessionManifestValidatorTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def ready_manifest(self):
        manifest = copy.deepcopy(self.manifest)
        commit = "a" * 40
        manifest["status"] = "ready_for_kyle_approval"
        manifest["source_validation"].update(
            head_commit_sha=commit,
            alpha_validation_run_id="30794386792",
            alpha_validation_conclusion="success",
            working_tree_clean_at_build=True,
        )
        manifest["build_identity"].update(
            commit_sha=commit,
            apk_sha256="b" * 64,
            artifact_verification="pass",
            installed_package_reconciled=True,
        )
        manifest["session_scope"].update(
            tester_count=3,
            fictional_alpha_disclosure_acknowledged=True,
            known_limitations_acknowledged=True,
        )
        manifest["required_route"] = {key: "pass" for key in manifest["required_route"]}
        for key in (
            "endpoint_qualification",
            "physical_or_equivalent_device_smoke",
            "save_reload_reconciliation",
            "stage3_capture_validation",
            "privacy_review",
        ):
            manifest["evidence"][key] = "pass"
        manifest["evidence"]["public_summary_reference"] = "issue-6-private-evidence-summary"
        manifest["defects"]["go_no_go"] = "go-for-kyle-approval"
        return manifest

    def test_complete_exact_package_manifest_is_ready(self):
        self.assertEqual([], validate_manifest(self.ready_manifest()))

    def test_template_fails_closed(self):
        errors = validate_manifest(self.manifest)
        self.assertTrue(errors)
        self.assertIn("status must be ready_for_kyle_approval", errors)

    def test_package_identity_mismatch_blocks(self):
        manifest = self.ready_manifest()
        manifest["build_identity"]["commit_sha"] = "c" * 40
        errors = validate_manifest(manifest)
        self.assertIn("built commit must match the validated PR head", errors)

    def test_major_defect_and_missing_recovery_evidence_block(self):
        manifest = self.ready_manifest()
        manifest["defects"]["open_majors"] = 1
        manifest["evidence"]["save_reload_reconciliation"] = "fail"
        errors = validate_manifest(manifest)
        self.assertIn("open Major defects must be zero", errors)
        self.assertIn("evidence item save_reload_reconciliation must pass", errors)

    def test_kyle_approval_cannot_be_pre_recorded(self):
        manifest = self.ready_manifest()
        manifest["pilot_authorization"]["kyle_approval_recorded"] = True
        errors = validate_manifest(manifest)
        self.assertIn("pilot approval must remain false before Kyle approves", errors)


if __name__ == "__main__":
    unittest.main()
