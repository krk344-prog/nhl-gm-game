from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
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
    def setUp(self):
        self.now = datetime(2026, 8, 31, 10, 30, tzinfo=timezone.utc)
        self.fresh = (self.now - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")

    def test_matching_readiness_commit_and_fresh_timestamp_are_allowed(self):
        commit = "a" * 40
        calls = []

        def runner(argv, *, check):
            calls.append(list(argv))
            raise RuntimeError("stop after source guard")

        with self.assertRaisesRegex(RuntimeError, "stop after source guard"):
            module.run_release_handoff(
                expected_source_commit=commit,
                readiness_checked_at=self.fresh,
                runner=runner,
                check_output=lambda *args, **kwargs: commit + "\n",
                now=self.now,
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
                readiness_checked_at=self.fresh,
                runner=runner,
                check_output=lambda *args, **kwargs: current + "\n",
                now=self.now,
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
                readiness_checked_at=self.fresh,
                runner=runner,
                check_output=lambda *args, **kwargs: ("a" * 40) + "\n",
                now=self.now,
            )

        self.assertEqual(calls, [])

    def test_missing_readiness_timestamp_blocks_before_device_work(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("device preflight must not run without certified readiness time")

        with self.assertRaisesRegex(RuntimeError, "execution readiness timestamp is required"):
            module.run_release_handoff(
                expected_source_commit="a" * 40,
                runner=runner,
                check_output=lambda *args, **kwargs: ("a" * 40) + "\n",
                now=self.now,
            )

        self.assertEqual(calls, [])

    def test_stale_readiness_blocks_before_device_work(self):
        calls = []
        stale = (self.now - module.READINESS_MAX_AGE - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("device preflight must not run after readiness expires")

        with self.assertRaisesRegex(RuntimeError, "execution readiness is stale"):
            module.run_release_handoff(
                expected_source_commit="a" * 40,
                readiness_checked_at=stale,
                runner=runner,
                check_output=lambda *args, **kwargs: ("a" * 40) + "\n",
                now=self.now,
            )

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
