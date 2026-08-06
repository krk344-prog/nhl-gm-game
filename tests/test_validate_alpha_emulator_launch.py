import tempfile
import unittest
from pathlib import Path

from scripts.validate_alpha_emulator_launch import (
    EmulatorLaunchError,
    validate_emulator_launch,
)


class ValidateAlphaEmulatorLaunchTests(unittest.TestCase):
    package = "com.krk344.nhlgmgame"

    def _write(self, directory: Path, logcat: str, activities: str):
        log_path = directory / "logcat.txt"
        activity_path = directory / "activities.txt"
        log_path.write_text(logcat, encoding="utf-8")
        activity_path.write_text(activities, encoding="utf-8")
        return log_path, activity_path

    def test_accepts_live_foreground_package_without_crash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log, activities = self._write(
                Path(temp_dir),
                "ActivityManager: Start proc 3120:com.krk344.nhlgmgame/u0a141\n",
                "mResumedActivity: ActivityRecord{abc com.krk344.nhlgmgame/.MainActivity}\n",
            )
            result = validate_emulator_launch(log, activities)
            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["foreground_confirmed"])

    def test_rejects_unregistered_expo_root_component(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log, activities = self._write(
                Path(temp_dir),
                'Invariant Violation: "main" has not been registered\n',
                "mResumedActivity: com.krk344.nhlgmgame/.MainActivity\n",
            )
            with self.assertRaisesRegex(EmulatorLaunchError, "root component"):
                validate_emulator_launch(log, activities)

    def test_rejects_fatal_exception_for_game_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log, activities = self._write(
                Path(temp_dir),
                "FATAL EXCEPTION: mqt_v_native\nProcess: com.krk344.nhlgmgame, PID: 3120\n",
                "mResumedActivity: com.krk344.nhlgmgame/.MainActivity\n",
            )
            with self.assertRaisesRegex(EmulatorLaunchError, "fatal Android"):
                validate_emulator_launch(log, activities)

    def test_ignores_other_process_crash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log, activities = self._write(
                Path(temp_dir),
                "FATAL EXCEPTION: main\nProcess: com.android.phone, PID: 100\n",
                "topResumedActivity=ActivityRecord{abc com.krk344.nhlgmgame/.MainActivity}\n",
            )
            self.assertEqual(validate_emulator_launch(log, activities)["status"], "pass")

    def test_rejects_package_that_is_not_foreground(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log, activities = self._write(
                Path(temp_dir),
                "ActivityManager: Start proc 3120:com.krk344.nhlgmgame/u0a141\n",
                "mResumedActivity: ActivityRecord{abc com.android.launcher/.Launcher}\n",
            )
            with self.assertRaisesRegex(EmulatorLaunchError, "not the resumed"):
                validate_emulator_launch(log, activities)


if __name__ == "__main__":
    unittest.main()
