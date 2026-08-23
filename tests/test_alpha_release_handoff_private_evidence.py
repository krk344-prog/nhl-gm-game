from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "run_alpha_release_handoff", SCRIPTS / "run_alpha_release_handoff.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AlphaReleaseHandoffPrivateEvidenceTests(unittest.TestCase):
    def test_private_evidence_records_are_written_under_requested_root_with_exact_identity(self):
        commit = "a" * 40
        apk_sha256 = "b" * 64
        handoff = {
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "season_id": "2026-27",
            "qualification_record": "artifacts/alpha-endpoint-qualification.json",
            "qualification_argv": ["python", "scripts/qualify_alpha_endpoint.py"],
            "build_argv": ["python", "scripts/build_alpha_apk_local.py", "--execute"],
        }

        def runner(argv, *, check):
            return SimpleNamespace(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            private_root = Path(tmpdir) / "alpha-private"
            device_template = Path(tmpdir) / "device-template.json"
            stage3_template = Path(tmpdir) / "stage3-template.json"
            identity_template = {
                "commit_sha": "",
                "api_base_url": "",
                "application_package": "",
                "build_type": "",
                "apk_sha256": "",
            }
            device_template.write_text(json.dumps(identity_template), encoding="utf-8")
            stage3_template.write_text(json.dumps(identity_template), encoding="utf-8")

            with (
                patch.object(module, "prepare_build_handoff", return_value=handoff),
                patch.object(module, "DEVICE_SMOKE_TEMPLATE", str(device_template)),
                patch.object(module, "STAGE3_CAPTURE_TEMPLATE", str(stage3_template)),
            ):
                result = module.run_release_handoff(
                    evidence_directory=str(private_root),
                    runner=runner,
                    record_exists=lambda path: True,
                    artifact_exists=lambda path: True,
                    checksum_reader=lambda path: apk_sha256,
                    check_output=lambda *args, **kwargs: commit + "\n",
                )

            expected_identity = {
                "commit_sha": commit,
                "api_base_url": handoff["api_base_url"],
                "application_package": module.APPLICATION_PACKAGE,
                "build_type": module.BUILD_TYPE,
                "apk_sha256": apk_sha256,
            }
            device_path = private_root / module.DEVICE_SMOKE_PRIVATE_FILENAME
            stage3_path = private_root / module.STAGE3_CAPTURE_PRIVATE_FILENAME

            self.assertEqual(Path(result["device_smoke_private_record"]), device_path)
            self.assertEqual(Path(result["stage3_capture_private_record"]), stage3_path)
            self.assertEqual(json.loads(device_path.read_text(encoding="utf-8")), expected_identity)
            self.assertEqual(json.loads(stage3_path.read_text(encoding="utf-8")), expected_identity)
            self.assertTrue(device_path.is_relative_to(private_root))
            self.assertTrue(stage3_path.is_relative_to(private_root))


if __name__ == "__main__":
    unittest.main()
