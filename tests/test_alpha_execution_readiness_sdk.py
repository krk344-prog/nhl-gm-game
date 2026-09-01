from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "check_alpha_execution_readiness", SCRIPTS / "check_alpha_execution_readiness.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AlphaExecutionReadinessSdkTests(unittest.TestCase):
    def _payload(self, sdk_level: str) -> dict[str, object]:
        return {
            "status": "ready",
            "authorized_device_count": 1,
            "selected_device": {
                "model": "Pixel",
                "android_version": "16",
                "sdk_level": sdk_level,
            },
        }

    def test_numeric_sdk_level_is_accepted(self):
        module.validate_device_ready_payload(self._payload("36"))

    def test_malformed_sdk_level_is_blocked(self):
        for sdk_level in ("unknown", "36-preview", "0", "-1"):
            with self.subTest(sdk_level=sdk_level):
                with self.assertRaisesRegex(
                    module.ExecutionReadinessError,
                    "selected-device metadata has an invalid sdk_level",
                ) as raised:
                    module.validate_device_ready_payload(self._payload(sdk_level))
                self.assertEqual(raised.exception.blocker_scope, "device")


if __name__ == "__main__":
    unittest.main()
