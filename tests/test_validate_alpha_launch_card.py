import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.validate_alpha_launch_card import LaunchCardError, validate_launch_card


READY_CARD = """NHL GM — TESTER LAUNCH CARD

Backend: READY
Verified at: 2026-09-06T07:30:00-04:00
Anonymous tester ID: T01
Private bug-report destination: organizer private inbox
Most important known limitation: Trade logic is simplified for this Alpha.
"""
READY_NOW = datetime(2026, 9, 6, 11, 45, tzinfo=timezone.utc)


class AlphaLaunchCardValidationTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "LAUNCH-CARD.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def test_ready_completed_card_passes_without_returning_private_destination(self):
        result = validate_launch_card(self._write(READY_CARD), now=READY_NOW)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["backend"], "READY")
        self.assertEqual(result["tester_id"], "T01")
        self.assertNotIn("bug_destination", result)
        self.assertNotIn("known_limitation", result)

    def test_wrong_or_duplicate_title_is_rejected(self):
        wrong_title = READY_CARD.replace("NHL GM — TESTER LAUNCH CARD", "NHL GM — NOTES")
        with self.assertRaisesRegex(LaunchCardError, "exactly one authoritative"):
            validate_launch_card(self._write(wrong_title), now=READY_NOW)
        with self.assertRaisesRegex(LaunchCardError, "exactly one authoritative"):
            validate_launch_card(self._write(READY_CARD + "\nNHL GM — TESTER LAUNCH CARD\n"), now=READY_NOW)

    def test_unavailable_backend_fails_closed(self):
        with self.assertRaisesRegex(LaunchCardError, "explicitly READY"):
            validate_launch_card(self._write(READY_CARD.replace("Backend: READY", "Backend: UNAVAILABLE")), now=READY_NOW)

    def test_placeholder_fields_fail_closed(self):
        text = READY_CARD.replace("Anonymous tester ID: T01", "Anonymous tester ID: [ T## ]")
        with self.assertRaisesRegex(LaunchCardError, "incomplete"):
            validate_launch_card(self._write(text), now=READY_NOW)

    def test_bad_timestamp_and_identity_are_rejected(self):
        with self.assertRaisesRegex(LaunchCardError, "ISO-8601"):
            validate_launch_card(self._write(READY_CARD.replace("2026-09-06T07:30:00-04:00", "this morning")), now=READY_NOW)
        with self.assertRaisesRegex(LaunchCardError, "T## format"):
            validate_launch_card(self._write(READY_CARD.replace("T01", "Kyle")), now=READY_NOW)

    def test_tester_id_must_belong_to_authorized_pilot_cohort(self):
        for tester_id in ("T00", "T06", "T99"):
            with self.subTest(tester_id=tester_id):
                text = READY_CARD.replace("Anonymous tester ID: T01", f"Anonymous tester ID: {tester_id}")
                with self.assertRaisesRegex(LaunchCardError, "authorized T01–T05 pilot cohort"):
                    validate_launch_card(self._write(text), now=READY_NOW)

    def test_timestamp_without_timezone_is_rejected(self):
        text = READY_CARD.replace("2026-09-06T07:30:00-04:00", "2026-09-06T07:30:00")
        with self.assertRaisesRegex(LaunchCardError, "timezone offset or Z"):
            validate_launch_card(self._write(text), now=READY_NOW)

    def test_future_timestamp_beyond_clock_skew_is_rejected(self):
        text = READY_CARD.replace("2026-09-06T07:30:00-04:00", "2999-01-01T00:00:00Z")
        with self.assertRaisesRegex(LaunchCardError, "future-dated"):
            validate_launch_card(self._write(text), now=READY_NOW)

    def test_stale_ready_timestamp_requires_backend_recheck(self):
        text = READY_CARD.replace("2026-09-06T07:30:00-04:00", "2026-09-06T10:00:00Z")
        with self.assertRaisesRegex(LaunchCardError, "stale; re-check the backend"):
            validate_launch_card(self._write(text), now=READY_NOW)

    def test_duplicate_authoritative_field_is_rejected(self):
        text = READY_CARD + "\nBackend: UNAVAILABLE\n"
        with self.assertRaisesRegex(LaunchCardError, "must appear exactly once: backend"):
            validate_launch_card(self._write(text), now=READY_NOW)

    def test_known_limitation_must_be_concrete(self):
        text = READY_CARD.replace(
            "Trade logic is simplified for this Alpha.",
            "No known limitations.",
        )
        with self.assertRaisesRegex(LaunchCardError, "concrete Alpha limitation"):
            validate_launch_card(self._write(text), now=READY_NOW)


if __name__ == "__main__":
    unittest.main()
