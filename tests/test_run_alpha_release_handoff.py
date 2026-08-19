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


class RunAlphaReleaseHandoffTests(unittest.TestCase):
    def setUp(self):
        self.handoff = {
            "api_base_url": "http://192.168.1.20:8000/api/v1",
            "season_id": "2026-27",
            "qualification_record": "artifacts/alpha-endpoint-qualification.json",
            "qualification_argv": ["python", "scripts/qualify_alpha_endpoint.py"],
            "build_argv": ["python", "scripts/build_alpha_apk_local.py", "--execute"],
        }

    def test_runs_qualification_then_exact_build(self):
        calls = []

        def runner(argv, *, check):
            calls.append((list(argv), check))
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            result = module.run_release_handoff(
                api_base_url=self.handoff["api_base_url"],
                runner=runner,
                record_exists=lambda path: True,
            )

        self.assertTrue(result["ready"])
        self.assertEqual(result["completed_phases"], ["qualification", "build"])
        self.assertEqual(
            calls,
            [
                (self.handoff["qualification_argv"], False),
                (self.handoff["build_argv"], False),
            ],
        )

    def test_missing_qualification_record_blocks_build(self):
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            return SimpleNamespace(returncode=0)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "required qualification record"):
                module.run_release_handoff(
                    runner=runner,
                    record_exists=lambda path: False,
                )

        self.assertEqual(calls, [self.handoff["qualification_argv"]])

    def test_failed_qualification_stops_before_build(self):
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            return SimpleNamespace(returncode=9)

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "qualification failed with exit code 9"):
                module.run_release_handoff(
                    runner=runner,
                    record_exists=lambda path: True,
                )

        self.assertEqual(calls, [self.handoff["qualification_argv"]])

    def test_failed_build_is_reported_after_successful_qualification(self):
        returncodes = iter((0, 7))

        def runner(argv, *, check):
            return SimpleNamespace(returncode=next(returncodes))

        with patch.object(module, "prepare_build_handoff", return_value=self.handoff):
            with self.assertRaisesRegex(RuntimeError, "build failed with exit code 7"):
                module.run_release_handoff(
                    runner=runner,
                    record_exists=lambda path: True,
                )


if __name__ == "__main__":
    unittest.main()
