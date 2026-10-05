import json
import unittest
from pathlib import Path


class MobilePackagedEntrypointTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_package_uses_registered_expo_entrypoint(self):
        package = json.loads(
            (self.repo_root / "mobile" / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(package["main"], "index.js")

        entrypoint = (self.repo_root / "mobile" / "index.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("registerRootComponent", entrypoint)
        self.assertIn("import App from './App'", entrypoint)
        self.assertIn("registerRootComponent(App)", entrypoint)

    def test_emulator_workflow_runs_fail_closed_launch_validation(self):
        workflow = (self.repo_root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("validate_alpha_emulator_launch.py", workflow)
        self.assertIn("sleep 30", workflow)
        self.assertIn("dumpsys activity activities", workflow)
        self.assertIn("adb shell pidof com.krk344.nhlgmgame >/dev/null", workflow)


if __name__ == "__main__":
    unittest.main()
