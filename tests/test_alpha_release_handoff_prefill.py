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
    def test_returns_exact_identity_for_private_device_smoke_prefill(self):
        handoff = {
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "season_id": "2026-27",
            "qualification_record": "artifacts/alpha-endpoint-qualification.json",
            "qualification_argv": ["python", "scripts/qualify_alpha_endpoint.py"],
            "build_argv": ["python", "scripts/build_alpha_apk_local.py", "--execute"],
        }
        commit = "b" * 40

        def runner(argv, *, check):
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=handoff):
            result = module.run_release_handoff(
                runner=runner,
                record_exists=lambda path: True,
                artifact_exists=lambda path: True,
                check_output=lambda *args, **kwargs: commit + "\n",
            )

        self.assertEqual(
            result["device_smoke_prefill"],
            {
                "commit_sha": commit,
                "api_base_url": handoff["api_base_url"],
                "application_package": "com.krk344.nhlgmgame",
            },
        )
        self.assertIn("returned exact commit/API/package identity", result["next_action"])


if __name__ == "__main__":
    unittest.main()
