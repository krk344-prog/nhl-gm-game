import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.simulation_calibration import (
    CalibrationLab,
    SCENARIOS,
    analyze_samples,
    load_profile,
    render_markdown,
    write_report,
)


class SimulationCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile()
        cls.lab = CalibrationLab(cls.profile)
        cls.first = cls.lab.run_season(421, "baseline")
        cls.repeat = cls.lab.run_season(421, "baseline")

    def test_full_season_reconciles_structural_invariants(self):
        sample = self.first
        self.assertEqual(sample.scheduled_games, 328)
        self.assertEqual(sample.completed_games, 328)
        self.assertEqual(sample.minimum_games_played, 82)
        self.assertEqual(sample.maximum_games_played, 82)
        self.assertEqual(sample.minimum_home_games, 41)
        self.assertEqual(sample.maximum_home_games, 41)
        self.assertEqual(sample.minimum_away_games, 41)
        self.assertEqual(sample.maximum_away_games, 41)
        self.assertEqual(sample.ties, 0)
        self.assertEqual(sample.total_goals_for, sample.total_goals_against)
        self.assertEqual(sample.total_goals_for, sample.total_goals)
        self.assertEqual(
            sample.total_standings_points,
            sample.expected_standings_points,
        )
        self.assertEqual(sample.parsed_shot_attempt_games, sample.completed_games)
        self.assertEqual(sample.structural_errors, ())

    def test_same_seed_produces_same_result_digest(self):
        self.assertEqual(self.first.digest, self.repeat.digest)
        self.assertEqual(self.first.team_points, self.repeat.team_points)

    def test_analysis_separates_structural_and_benchmark_failures(self):
        structurally_valid_but_low_scoring = replace(self.first, total_goals=0)
        report = analyze_samples(
            self.profile,
            [structurally_valid_but_low_scoring],
            {
                "seed": self.first.seed,
                "first_digest": self.first.digest,
                "repeat_digest": self.repeat.digest,
                "passed": True,
            },
        )
        self.assertEqual(report["structural_integrity"]["status"], "pass")
        self.assertEqual(report["status"], "needs_tuning")
        goals = next(
            finding
            for finding in report["benchmark_findings"]
            if finding["metric"] == "average_combined_goals"
        )
        self.assertEqual(goals["status"], "low")

    def test_report_outputs_are_machine_and_human_readable(self):
        report = analyze_samples(
            self.profile,
            [self.first],
            {
                "seed": self.first.seed,
                "first_digest": self.first.digest,
                "repeat_digest": self.repeat.digest,
                "passed": True,
            },
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "calibration.json"
            markdown_path = Path(temp_dir) / "calibration.md"
            write_report(report, json_path, markdown_path)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["profile"]["profile_id"], "nhl-2025-26-alpha-v0")
            rendered = markdown_path.read_text(encoding="utf-8")
            self.assertIn("Structural integrity", rendered)
            self.assertIn("Baseline benchmark findings", rendered)
            self.assertEqual(rendered, render_markdown(report))

    def test_adversarial_catalog_contains_single_axis_stress_tests(self):
        self.assertEqual(
            set(SCENARIOS),
            {"baseline", "speed_stack", "shooting_stack", "goalie_stack"},
        )


if __name__ == "__main__":
    unittest.main()
