from __future__ import annotations

import importlib.util
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
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("{}\n", encoding="utf-8")
            return output_path

        expected_identity = {
            "commit_sha": commit,
            "api_base_url": handoff["api_base_url"],
            "application_package": "com.krk344.nhlgmgame",
            "build_type": "standalone-release-apk",
            "apk_sha256": apk_sha256,
        }
        expected_route = [
            "New Game",
            "Select Franchise",
            "Advance Day",
            "Roster",
            "Standings",
            "Trade",
            "Trade History",
            "Save",
            "Reload",
            "Generate Debug Report",
            "Reset",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            private_root = Path(tmpdir) / "alpha-private-test"
            device_path = private_root / module.DEVICE_SMOKE_PRIVATE_FILENAME
            stage3_path = private_root / module.STAGE3_CAPTURE_PRIVATE_FILENAME
            device_tmp = private_root / f".{module.DEVICE_SMOKE_PRIVATE_FILENAME}.tmp"
            stage3_tmp = private_root / f".{module.STAGE3_CAPTURE_PRIVATE_FILENAME}.tmp"

            with patch.object(module, "prepare_build_handoff", return_value=handoff):
                result = module.run_release_handoff(
                    runner=runner,
                    record_exists=lambda path: True,
                    artifact_exists=lambda path: True,
                    checksum_reader=lambda path: apk_sha256,
                    evidence_directory=str(private_root),
                    evidence_writer=evidence_writer,
                    check_output=lambda *args, **kwargs: commit + "\n",
                )

            self.assertEqual(result["device_smoke_prefill"], expected_identity)
            self.assertEqual(result["stage3_capture_prefill"], expected_identity)
            self.assertEqual(result["device_smoke_route"], expected_route)
            self.assertEqual(result["device_smoke_private_record"], str(device_path))
            self.assertEqual(result["stage3_capture_private_record"], str(stage3_path))
            self.assertTrue(device_path.is_file())
            self.assertTrue(stage3_path.is_file())
            self.assertFalse(device_tmp.exists())
            self.assertFalse(stage3_tmp.exists())
            self.assertEqual(
                writes,
                [
                    (
                        module.DEVICE_SMOKE_TEMPLATE,
                        str(device_tmp),
                        expected_identity,
                    ),
                    (
                        module.STAGE3_CAPTURE_TEMPLATE,
                        str(stage3_tmp),
                        expected_identity,
                    ),
                ],
            )
            self.assertIn("device_smoke_route", result["next_action"])
            self.assertIn("prefilled private device-smoke record", result["next_action"])
            self.assertIn("prefilled Stage 3 capture record", result["next_action"])


if __name__ == "__main__":
    unittest.main()