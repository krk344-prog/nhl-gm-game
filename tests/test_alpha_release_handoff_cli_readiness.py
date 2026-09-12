from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "run_alpha_release_handoff_cli_readiness", SCRIPTS / "run_alpha_release_handoff.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AlphaReleaseHandoffCliReadinessTests(unittest.TestCase):
    def test_cli_blocks_when_readiness_certificate_is_missing(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                module.main(["--api-base-url", "http://192.168.1.20:8000/api/v1"])
        self.assertEqual(context.exception.code, 2)

    def test_cli_passes_readiness_certificate_to_guarded_handoff(self):
        commit = "a" * 40
        checked_at = "2026-09-01T16:00:00Z"
        payload = {"ready": True}
        with patch.object(module, "run_release_handoff", return_value=payload) as run_mock:
            with redirect_stdout(io.StringIO()):
                result = module.main(
                    [
                        "--api-base-url",
                        "http://192.168.1.20:8000/api/v1",
                        "--expected-source-commit",
                        commit,
                        "--readiness-checked-at",
                        checked_at,
                    ]
                )

        self.assertEqual(result, 0)
        self.assertEqual(run_mock.call_args.kwargs["expected_source_commit"], commit)
        self.assertEqual(run_mock.call_args.kwargs["readiness_checked_at"], checked_at)


if __name__ == "__main__":
    unittest.main()
