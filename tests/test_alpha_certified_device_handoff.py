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
    "run_alpha_certified_release_handoff", SCRIPTS / "run_alpha_certified_release_handoff.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AlphaCertifiedDeviceHandoffTests(unittest.TestCase):
    def _runner(self, payload: str):
        def runner(argv, *, check, capture_output, text):
            return SimpleNamespace(returncode=0, stdout=payload, stderr="")
        return runner

    def test_matching_certified_device_proceeds_to_guarded_handoff(self):
        identity = "b" * 64
        device_payload = (
            '{"status":"ready","authorized_device_count":1,'
            '"selected_device":{"model":"Pixel 10 XL","android_version":"16","sdk_level":"36"},'
            f'"device_identity":"{identity}"}}'
        )
        expected = {"ready": True}
        with patch.object(module, "run_release_handoff", return_value=expected) as handoff:
            result = module.run_certified_handoff(
                api_base_url="http://192.168.1.20:8000/api/v1",
                season_id="2026-27",
                timeout=5.0,
                serial=None,
                evidence_directory=".alpha-private",
                expected_source_commit="a" * 40,
                readiness_checked_at="2026-09-02T07:00:00Z",
                expected_device_model="Pixel 10 XL",
                expected_android_version="16",
                expected_sdk_level="36",
                device_identity_key="11" * 32,
                expected_device_identity=identity,
                runner=self._runner(device_payload),
            )
        self.assertEqual(result, expected)
        handoff.assert_called_once()

    def test_same_model_but_different_device_identity_blocks(self):
        changed_identity = "c" * 64
        device_payload = (
            '{"status":"ready","authorized_device_count":1,'
            '"selected_device":{"model":"Pixel 10 XL","android_version":"16","sdk_level":"36"},'
            f'"device_identity":"{changed_identity}"}}'
        )
        with patch.object(module, "run_release_handoff") as handoff:
            with self.assertRaisesRegex(RuntimeError, "device identity changed"):
                module.run_certified_handoff(
                    api_base_url="http://192.168.1.20:8000/api/v1",
                    season_id="2026-27",
                    timeout=5.0,
                    serial=None,
                    evidence_directory=".alpha-private",
                    expected_source_commit="a" * 40,
                    readiness_checked_at="2026-09-02T07:00:00Z",
                    expected_device_model="Pixel 10 XL",
                    expected_android_version="16",
                    expected_sdk_level="36",
                    device_identity_key="11" * 32,
                    expected_device_identity="b" * 64,
                    runner=self._runner(device_payload),
                )
        handoff.assert_not_called()


if __name__ == "__main__":
    unittest.main()
