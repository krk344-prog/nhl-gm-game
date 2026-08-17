import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.validate_alpha_pilot_session_manifest import (
    validate_local_evidence_references,
    validate_manifest,
)


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
            api_base_url="http://192.168.1.50:8000/api/v1",
            artifact_verification="pass",
            installed_package_reconciled=True,
            launch_confirmation="pass",
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
        manifest["evidence"].update(
            endpoint_qualification_minutes=15,
            endpoint_qualification_reference="artifacts/alpha-endpoint-qualification.json",
            device_smoke_reference="private/device-smoke-record.json",
            save_reload_reference="private/device-smoke-record.json#save_reload",
            stage3_capture_reference="private/stage3-capture-record.json",
            privacy_review_reference="issue-6-private-evidence-review",
            public_summary_reference="issue-6-private-evidence-summary",
        )
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

    def test_endpoint_identity_missing_or_loopback_blocks(self):
        manifest = self.ready_manifest()
        manifest["build_identity"]["api_base_url"] = ""
        errors = validate_manifest(manifest)
        self.assertIn("api_base_url must identify the exact tester-accessible http(s) backend", errors)

        manifest["build_identity"]["api_base_url"] = "http://127.0.0.1:8000/api/v1"
        errors = validate_manifest(manifest)
        self.assertIn("api_base_url must identify the exact tester-accessible http(s) backend", errors)

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

    def test_short_endpoint_qualification_and_missing_launch_block(self):
        manifest = self.ready_manifest()
        manifest["evidence"]["endpoint_qualification_minutes"] = 14.5
        manifest["build_identity"]["launch_confirmation"] = "pending"
        errors = validate_manifest(manifest)
        self.assertIn("endpoint qualification must cover at least 15 uninterrupted minutes", errors)
        self.assertIn("installed application launch must be confirmed", errors)

    def test_missing_evidence_reference_blocks_ready_manifest(self):
        manifest = self.ready_manifest()
        manifest["evidence"]["stage3_capture_reference"] = ""
        errors = validate_manifest(manifest)
        self.assertIn("stage3_capture_reference is required", errors)

    def test_public_evidence_references_must_bind_to_issue_6(self):
        manifest = self.ready_manifest()
        manifest["evidence"]["privacy_review_reference"] = "issue-7-private-evidence-review"
        manifest["evidence"]["public_summary_reference"] = "random-summary"
        errors = validate_manifest(manifest)
        self.assertIn(
            "privacy_review_reference must identify an issue #6 coordination record using issue-6-<slug>",
            errors,
        )
        self.assertIn(
            "public_summary_reference must identify an issue #6 coordination record using issue-6-<slug>",
            errors,
        )

    def test_local_evidence_references_must_resolve_before_final_ready(self):
        manifest = self.ready_manifest()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "artifacts").mkdir()
            (root / "private").mkdir()
            (root / "artifacts/alpha-endpoint-qualification.json").write_text("{}", encoding="utf-8")
            (root / "private/device-smoke-record.json").write_text("{}", encoding="utf-8")
            (root / "private/stage3-capture-record.json").write_text("{}", encoding="utf-8")
            self.assertEqual([], validate_local_evidence_references(manifest, root))

            (root / "private/stage3-capture-record.json").unlink()
            errors = validate_local_evidence_references(manifest, root)
            self.assertIn(
                "stage3_capture_reference does not resolve to an existing evidence file: private/stage3-capture-record.json",
                errors,
            )

    def test_local_evidence_reference_cannot_escape_evidence_root(self):
        manifest = self.ready_manifest()
        manifest["evidence"]["device_smoke_reference"] = "../device-smoke-record.json"
        with TemporaryDirectory() as temp_dir:
            errors = validate_local_evidence_references(manifest, Path(temp_dir))
        self.assertIn("device_smoke_reference must be a safe relative evidence path", errors)


if __name__ == "__main__":
    unittest.main()
