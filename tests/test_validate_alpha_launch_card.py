import tempfile
import unittest
from pathlib import Path

from scripts.validate_alpha_launch_card import LaunchCardError, validate_launch_card


READY_CARD = """NHL GM — TESTER LAUNCH CARD

Backend: READY
Verified at: 2026-09-06T07:30:00-04:00
Anonymous tester ID: T01
Private bug-report destination: organizer private inbox
Most important known limitation: Trade logic is simplified for this Alpha.
"""


class AlphaLaunchCardValidationTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "LAUNCH-CARD.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def test_ready_completed_card_passes_without_returning_private_destination(self):
        result = validate_launch_card(self._write(READY_CARD))
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["backend"], "READY")
        self.assertEqual(result["tester_id"], "T01")
        self.assertNotIn("bug_destination", result)
        self.assertNotIn("known_limitation", result)

    def test_unavailable_backend_fails_closed(self):
        with self.assertRaisesRegex(LaunchCardError, "explicitly READY"):
            validate_launch_card(self._write(READY_CARD.replace("Backend: READY", "Backend: UNAVAILABLE")))

    def test_placeholder_fields_fail_closed(self):
        text = READY_CARD.replace("Anonymous tester ID: T01", "Anonymous tester ID: [ T## ]")
        with self.assertRaisesRegex(LaunchCardError, "incomplete"):
            validate_launch_card(self._write(text))

    def test_bad_timestamp_and_identity_are_rejected(self):
        with self.assertRaisesRegex(LaunchCardError, "ISO-8601"):
            validate_launch_card(self._write(READY_CARD.replace("2026-09-06T07:30:00-04:00", "this morning")))
        with self.assertRaisesRegex(LaunchCardError, "T## format"):
            validate_launch_card(self._write(READY_CARD.replace("T01", "Kyle")))


if __name__ == "__main__":
    unittest.main()
