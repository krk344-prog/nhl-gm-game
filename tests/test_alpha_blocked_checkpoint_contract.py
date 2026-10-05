from pathlib import Path
import unittest


class AlphaBlockedCheckpointContractTests(unittest.TestCase):
    def test_unavailable_checkpoint_fails_closed(self) -> None:
        guide = Path("docs/alpha_testing_guide.md").read_text(encoding="utf-8")
        core = guide.split("## Core test pass", 1)[1].split("## Longer simulation pass", 1)[0]
        self.assertIn("record that checkpoint as **Blocked**", core)
        self.assertIn("Do not substitute a different route", core)
        self.assertIn("infer a pass from another screen", core)
        self.assertIn("one short observation", core)


if __name__ == "__main__":
    unittest.main()
