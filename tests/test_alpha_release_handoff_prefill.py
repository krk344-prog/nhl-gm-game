from __future__ import annotations

import importlib.util
import sys
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


class AlphaReleaseHandoffPrefillTests(unittest.TestCase):
    def test_returns_exact_identity_and_writes_private_evidence_prefills(self):
        handoff = {
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "season_id": "2026-27",
            "qualification_record": "artifacts/alpha-endpoint-qualification.json",
            "qualification_argv": ["python", "scripts/qualify_alpha_endpoint.py"],
            "build_argv": ["python", "scripts/build_alpha_apk_local.py", "--execute"],
        }
        commit = "b" * 40
        apk_sha256 = "c" * 64
        writes = []

        def runner(argv, *, check):
            return SimpleNamespace(returncode=0)

        def evidence_writer(template_path, output_path, identity):
            writes.append((template_path, output_path, dict(identity)))
            return output_path

        with patch.object(module, "prepare_build_handoff", return_value=handoff):
            result = module.run_release_handoff(
                runner=runner,
                record_exists=lambda path: True,
                artifact_exists=lambda path: True,
                checksum_reader=lambda path: apk_sha256,
                evidence_directory=".alpha-private-test",
                evidence_writer=evidence_writer,
                check_output=lambda *args, **kwargs: commit + "\n",
            )

        expected_identity = {
            "commit_sha": commit,
            "api_base_url": handoff["api_base_url"],
            "application_package": "com.krk344.nhlgmgame",
            "build_type": "standalone-release-apk",
            "apk_sha256": apk_sha256,
        }
        self.assertEqual(result["device_smoke_prefill"], expected_identity)
        self.assertEqual(result["stage3_capture_prefill"], expected_identity)
        self.assertEqual(result["device_smoke_private_record"], ".alpha-private-test/technical-alpha-device-smoke.json")
        self.assertEqual(result["stage3_capture_private_record"], ".alpha-private-test/technical-alpha-stage3-capture.json")
        self.assertEqual(
            writes,
            [
                (
                    module.DEVICE_SMOKE_TEMPLATE,
                    ".alpha-private-test/technical-alpha-device-smoke.json",
                    expected_identity,
                ),
                (
                    module.STAGE3_CAPTURE_TEMPLATE,
                    ".alpha-private-test/technical-alpha-stage3-capture.json",
                    expected_identity,
                ),
            ],
        )
        self.assertIn("prefilled private device-smoke record", result["next_action"])
        self.assertIn("prefilled Stage 3 capture record", result["next_action"])


if __name__ == "__main__":
    unittest.main()
