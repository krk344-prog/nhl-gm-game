from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "run_alpha_release_handoff", SCRIPTS / "run_alpha_release_handoff.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AlphaReleaseHandoffExpectedCommitTests(unittest.TestCase):
    def test_matching_readiness_commit_is_allowed(self):
        commit = "a" * 40
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            raise RuntimeError("stop after source guard")

        with self.assertRaisesRegex(RuntimeError, "stop after source guard"):
            module.run_release_handoff(
                expected_source_commit=commit,
                runner=runner,
                check_output=lambda *args, **kwargs: commit + "\n",
            )

        self.assertEqual(calls, [[sys.executable, module.DEVICE_PREFLIGHT_SCRIPT]])

    def test_changed_source_commit_blocks_before_device_or_endpoint_work(self):
        certified = "a" * 40
        current = "b" * 40
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("device preflight must not run after source drift")

        with self.assertRaisesRegex(RuntimeError, "source commit changed after execution readiness"):
            module.run_release_handoff(
                expected_source_commit=certified,
                runner=runner,
                check_output=lambda *args, **kwargs: current + "\n",
            )

        self.assertEqual(calls, [])

    def test_invalid_expected_commit_blocks_before_device_work(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("device preflight must not run with invalid expected commit")

        with self.assertRaisesRegex(RuntimeError, "expected source commit is not a valid"):
            module.run_release_handoff(
                expected_source_commit="not-a-sha",
                runner=runner,
                check_output=lambda *args, **kwargs: ("a" * 40) + "\n",
            )

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
