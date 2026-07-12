"""Simulation calibration and adversarial testing for the NHL GM engine.

The lab runs isolated, seeded seasons, validates structural invariants, compares
aggregate behavior with configurable guardrails, and measures whether a single
attribute can become a dominant roster-building strategy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import statistics
import tempfile
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

try:
    from .game_service import reset_game
    from .league_orchestrator import advance_day
    from .nhl_gm_core import connect_database
except ImportError:  # Support direct execution from src/.
    from game_service import reset_game
    from league_orchestrator import advance_day
    from nhl_gm_core import connect_database


DEFAULT_PROFILE_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "calibration_benchmarks.json"
)
CORSI_PATTERN = re.compile(
    r"CORSI EQUIVALENTS METRIC: HOME SHOTS: (?P<home>\d+) \| AWAY SHOTS: (?P<away>\d+)"
)


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    statements: tuple[tuple[str, tuple[object, ...]], ...] = ()


SCENARIOS: Mapping[str, Scenario] = {
    "baseline": Scenario(
        "baseline",
        "Unmodified seeded rosters.",
    ),
    "speed_stack": Scenario(
        "speed_stack",
        "Raise every controlled-team forward's speed by eight points.",
        ((
            "UPDATE players SET speed = MIN(99, speed + 8) "
            "WHERE team_id = 1 AND position = 'F'",
            (),
        ),),
    ),
    "shooting_stack": Scenario(
        "shooting_stack",
        "Raise every controlled-team forward's shooting by eight points.",
        ((
            "UPDATE players SET shooting = MIN(99, shooting + 8) "
            "WHERE team_id = 1 AND position = 'F'",
            (),
        ),),
    ),
    "goalie_stack": Scenario(
        "goalie_stack",
        "Raise both controlled-team goalies' positioning and reflexes by eight points.",
        ((
            "UPDATE players "
            "SET positioning = MIN(99, positioning + 8), "
            "    reflexes = MIN(99, reflexes + 8) "
            "WHERE team_id = 1 AND position = 'G'",
            (),
        ),),
    ),
}


@dataclass(frozen=True)
class SeasonSample:
    seed: int
    scenario: str
    digest: str
    team_count: int
    scheduled_games: int
    completed_games: int
    total_goals: int
    home_wins: int
    overtime_games: int
    one_goal_games: int
    total_shot_attempts: int
    parsed_shot_attempt_games: int
    ties: int
    minimum_games_played: int
    maximum_games_played: int
    minimum_home_games: int
    maximum_home_games: int
    minimum_away_games: int
    maximum_away_games: int
    total_standings_points: int
    expected_standings_points: int
    total_goals_for: int
    total_goals_against: int
    points_stddev: float
    points_range: int
    strength_points_correlation: float
    champion_team_id: int
    controlled_team_points: int
    team_points: dict[str, int]
    team_strengths: dict[str, float]
    structural_errors: tuple[str, ...]


@dataclass(frozen=True)
class MetricFinding:
    metric: str
    label: str
    value: float | None
    minimum: float
    maximum: float
    unit: str
    status: str
    sample_count: int


@dataclass(frozen=True)
class SensitivityFinding:
    scenario: str
    mean_points_uplift: float
    median_points_uplift: float
    maximum_points_uplift: int
    mean_strength_uplift: float
    threshold: float
    status: str


class CalibrationProfileError(ValueError):
    pass


def load_profile(path: Path | str = DEFAULT_PROFILE_PATH) -> dict:
    profile_path = Path(path)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    required = {"profile_id", "as_of", "league_structure", "metric_targets", "adversarial"}
    missing = sorted(required - profile.keys())
    if missing:
        raise CalibrationProfileError(
            f"Calibration profile is missing required fields: {', '.join(missing)}"
        )
    structure = profile["league_structure"]
    for key in ("games_per_team", "home_games_per_team", "away_games_per_team"):
        if int(structure.get(key, 0)) <= 0:
            raise CalibrationProfileError(f"league_structure.{key} must be positive")
    for metric, target in profile["metric_targets"].items():
        if float(target["minimum"]) > float(target["maximum"]):
            raise CalibrationProfileError(f"{metric} minimum cannot exceed maximum")
    return profile


@contextmanager
def _isolated_database(path: Path):
    previous = os.environ.get("NHL_GM_DB_PATH")
    os.environ["NHL_GM_DB_PATH"] = str(path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("NHL_GM_DB_PATH", None)
        else:
            os.environ["NHL_GM_DB_PATH"] = previous


def _pearson(xs: Iterable[float], ys: Iterable[float]) -> float:
    left = list(xs)
    right = list(ys)
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    left_variance = sum((x - left_mean) ** 2 for x in left)
    right_variance = sum((y - right_mean) ** 2 for y in right)
    denominator = math.sqrt(left_variance * right_variance)
    return numerator / denominator if denominator else 0.0


def _team_strength_snapshot() -> dict[int, float]:
    with connect_database() as conn:
        rows = conn.execute(
            """
            SELECT team_id, position, shooting, passing, positioning,
                   reflexes, speed, checking
            FROM players
            WHERE team_id IN (SELECT id FROM teams WHERE tier = 'NHL')
            ORDER BY team_id, id
            """
        ).fetchall()
    grouped: dict[int, dict[str, list[float]]] = {}
    for row in rows:
        team_id, position, shooting, passing, positioning, reflexes, speed, checking = row
        bucket = grouped.setdefault(team_id, {"skaters": [], "goalies": []})
        if position == "G":
            bucket["goalies"].append((positioning + reflexes) / 2.0)
        else:
            bucket["skaters"].append(
                (shooting + passing + positioning + speed + checking) / 5.0
            )
    strengths = {}
    for team_id, groups in grouped.items():
        skater_score = statistics.fmean(groups["skaters"]) if groups["skaters"] else 0.0
        goalie_score = statistics.fmean(groups["goalies"]) if groups["goalies"] else 0.0
        strengths[team_id] = round(skater_score * 0.88 + goalie_score * 0.12, 6)
    return strengths


def _apply_scenario(scenario: Scenario) -> None:
    if not scenario.statements:
        return
    with connect_database() as conn:
        for statement, parameters in scenario.statements:
            conn.execute(statement, parameters)
        conn.commit()


def _schedule_digest(schedule_rows: list[tuple], standings_rows: list[tuple]) -> str:
    payload = {
        "schedule": [list(row[:-1]) for row in schedule_rows],
        "standings": [list(row) for row in standings_rows],
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class CalibrationLab:
    def __init__(self, profile: dict | None = None):
        self.profile = profile or load_profile()

    def run_season(self, seed: int, scenario_name: str = "baseline") -> SeasonSample:
        if scenario_name not in SCENARIOS:
            raise KeyError(
                f"Unknown scenario {scenario_name!r}; choose from {', '.join(SCENARIOS)}"
            )
        scenario = SCENARIOS[scenario_name]
        with tempfile.TemporaryDirectory(prefix="nhl-gm-calibration-") as temp_dir:
            db_path = Path(temp_dir) / "calibration.db"
            with _isolated_database(db_path):
                reset_game(seed=int(seed), save_name=f"Calibration {seed} {scenario_name}")
                _apply_scenario(scenario)
                team_strengths = _team_strength_snapshot()

                # Match randomness is separate from deterministic roster generation.
                # Keeping it scenario-independent supports paired sensitivity comparisons.
                random.seed(int(seed) * 1_000_003 + 97)
                with connect_database() as conn:
                    current_day, max_days = conn.execute(
                        "SELECT current_day, max_days FROM league_calendar WHERE id = 1"
                    ).fetchone()
                for _ in range(current_day, max_days):
                    advance_day()

                return self._collect_sample(int(seed), scenario_name, team_strengths)

    def _collect_sample(
        self,
        seed: int,
        scenario_name: str,
        team_strengths: dict[int, float],
    ) -> SeasonSample:
        with connect_database() as conn:
            schedule_rows = conn.execute(
                """
                SELECT id, day, home_team_id, away_team_id, status,
                       home_score, away_score, overtime, result_log
                FROM schedule
                ORDER BY id
                """
            ).fetchall()
            standings_rows = conn.execute(
                """
                SELECT team_id, games_played, wins, losses, overtime_losses,
                       points, goals_for, goals_against
                FROM standings
                ORDER BY team_id
                """
            ).fetchall()

        team_count = len(standings_rows)
        completed = [row for row in schedule_rows if row[4] == "completed"]
        total_goals = 0
        home_wins = 0
        overtime_games = 0
        one_goal_games = 0
        total_shot_attempts = 0
        parsed_shot_attempt_games = 0
        ties = 0
        home_counts: Counter[int] = Counter()
        away_counts: Counter[int] = Counter()
        for row in schedule_rows:
            _, _, home_id, away_id, status, home_score, away_score, overtime, result_log = row
            home_counts[home_id] += 1
            away_counts[away_id] += 1
            if status != "completed" or home_score is None or away_score is None:
                continue
            total_goals += home_score + away_score
            home_wins += int(home_score > away_score)
            overtime_games += int(bool(overtime))
            one_goal_games += int(abs(home_score - away_score) == 1)
            ties += int(home_score == away_score)
            match = CORSI_PATTERN.search(result_log or "")
            if match:
                total_shot_attempts += int(match.group("home")) + int(match.group("away"))
                parsed_shot_attempt_games += 1

        games_played = [row[1] for row in standings_rows]
        points = [row[5] for row in standings_rows]
        total_standings_points = sum(points)
        expected_standings_points = len(completed) * 2 + overtime_games
        total_goals_for = sum(row[6] for row in standings_rows)
        total_goals_against = sum(row[7] for row in standings_rows)
        point_map = {str(row[0]): row[5] for row in standings_rows}
        strength_map = {str(key): value for key, value in sorted(team_strengths.items())}
        strength_vector = [team_strengths[row[0]] for row in standings_rows]
        champion_team_id = max(
            standings_rows,
            key=lambda row: (row[5], row[2], row[6] - row[7], -row[0]),
        )[0]

        structure = self.profile["league_structure"]
        games_per_team = int(structure["games_per_team"])
        home_games_per_team = int(structure["home_games_per_team"])
        away_games_per_team = int(structure["away_games_per_team"])
        expected_schedule = team_count * games_per_team // 2
        errors = []
        if len(schedule_rows) != expected_schedule:
            errors.append(
                f"scheduled_games={len(schedule_rows)} expected={expected_schedule}"
            )
        if len(completed) != len(schedule_rows):
            errors.append(
                f"completed_games={len(completed)} scheduled_games={len(schedule_rows)}"
            )
        if games_played and (min(games_played) != games_per_team or max(games_played) != games_per_team):
            errors.append(
                f"games_played_range={min(games_played)}-{max(games_played)} expected={games_per_team}"
            )
        home_values = [home_counts[row[0]] for row in standings_rows]
        away_values = [away_counts[row[0]] for row in standings_rows]
        if home_values and (min(home_values) != home_games_per_team or max(home_values) != home_games_per_team):
            errors.append(
                f"home_games_range={min(home_values)}-{max(home_values)} expected={home_games_per_team}"
            )
        if away_values and (min(away_values) != away_games_per_team or max(away_values) != away_games_per_team):
            errors.append(
                f"away_games_range={min(away_values)}-{max(away_values)} expected={away_games_per_team}"
            )
        if ties:
            errors.append(f"unresolved_ties={ties}")
        if total_goals_for != total_goals_against or total_goals_for != total_goals:
            errors.append(
                "goal-ledger mismatch: "
                f"GF={total_goals_for} GA={total_goals_against} schedule={total_goals}"
            )
        if total_standings_points != expected_standings_points:
            errors.append(
                "standings-points mismatch: "
                f"actual={total_standings_points} expected={expected_standings_points}"
            )
        invalid_records = [
            row[0]
            for row in standings_rows
            if row[2] + row[3] + row[4] != row[1]
        ]
        if invalid_records:
            errors.append(f"invalid team records={invalid_records}")
        if parsed_shot_attempt_games != len(completed):
            errors.append(
                "missing shot-attempt logs: "
                f"parsed={parsed_shot_attempt_games} completed={len(completed)}"
            )

        return SeasonSample(
            seed=seed,
            scenario=scenario_name,
            digest=_schedule_digest(schedule_rows, standings_rows),
            team_count=team_count,
            scheduled_games=len(schedule_rows),
            completed_games=len(completed),
            total_goals=total_goals,
            home_wins=home_wins,
            overtime_games=overtime_games,
            one_goal_games=one_goal_games,
            total_shot_attempts=total_shot_attempts,
            parsed_shot_attempt_games=parsed_shot_attempt_games,
            ties=ties,
            minimum_games_played=min(games_played) if games_played else 0,
            maximum_games_played=max(games_played) if games_played else 0,
            minimum_home_games=min(home_values) if home_values else 0,
            maximum_home_games=max(home_values) if home_values else 0,
            minimum_away_games=min(away_values) if away_values else 0,
            maximum_away_games=max(away_values) if away_values else 0,
            total_standings_points=total_standings_points,
            expected_standings_points=expected_standings_points,
            total_goals_for=total_goals_for,
            total_goals_against=total_goals_against,
            points_stddev=statistics.pstdev(points) if len(points) > 1 else 0.0,
            points_range=max(points) - min(points) if points else 0,
            strength_points_correlation=_pearson(strength_vector, points),
            champion_team_id=champion_team_id,
            controlled_team_points=point_map.get("1", 0),
            team_points=point_map,
            team_strengths=strength_map,
            structural_errors=tuple(errors),
        )

    def run(
        self,
        seasons: int = 10,
        start_seed: int = 1000,
        scenarios: Iterable[str] = ("baseline",),
        check_reproducibility: bool = True,
    ) -> dict:
        if seasons < 1 or seasons > 100:
            raise ValueError("seasons must be between 1 and 100")
        scenario_names = tuple(dict.fromkeys(scenarios))
        if "baseline" not in scenario_names:
            scenario_names = ("baseline", *scenario_names)
        unknown = [name for name in scenario_names if name not in SCENARIOS]
        if unknown:
            raise KeyError(f"Unknown scenarios: {', '.join(unknown)}")

        samples = []
        for scenario_name in scenario_names:
            for seed in range(start_seed, start_seed + seasons):
                samples.append(self.run_season(seed, scenario_name))

        reproducibility = None
        if check_reproducibility:
            first = next(
                sample
                for sample in samples
                if sample.scenario == "baseline" and sample.seed == start_seed
            )
            repeat = self.run_season(start_seed, "baseline")
            reproducibility = {
                "seed": start_seed,
                "first_digest": first.digest,
                "repeat_digest": repeat.digest,
                "passed": first.digest == repeat.digest,
            }
        return analyze_samples(self.profile, samples, reproducibility)


def _scenario_summary(samples: list[SeasonSample]) -> dict:
    games = sum(sample.completed_games for sample in samples)
    pooled_strengths = []
    pooled_points = []
    for sample in samples:
        for team_id, strength in sample.team_strengths.items():
            pooled_strengths.append(strength)
            pooled_points.append(sample.team_points[team_id])
    champions = Counter(sample.champion_team_id for sample in samples)
    return {
        "seasons": len(samples),
        "games": games,
        "average_combined_goals": (
            sum(sample.total_goals for sample in samples) / games if games else 0.0
        ),
        "home_win_rate": (
            sum(sample.home_wins for sample in samples) / games if games else 0.0
        ),
        "overtime_rate": (
            sum(sample.overtime_games for sample in samples) / games if games else 0.0
        ),
        "one_goal_game_rate": (
            sum(sample.one_goal_games for sample in samples) / games if games else 0.0
        ),
        "average_shot_attempts_per_team": (
            sum(sample.total_shot_attempts for sample in samples) / (2 * games)
            if games
            else 0.0
        ),
        "average_points_stddev": statistics.fmean(
            sample.points_stddev for sample in samples
        ),
        "average_points_range": statistics.fmean(
            sample.points_range for sample in samples
        ),
        "strength_points_correlation": _pearson(pooled_strengths, pooled_points),
        "champion_concentration": max(champions.values()) / len(samples),
        "champion_counts": {str(key): value for key, value in sorted(champions.items())},
    }


def _metric_findings(profile: dict, baseline: dict) -> list[MetricFinding]:
    findings = []
    season_count = int(baseline["seasons"])
    for metric, target in profile["metric_targets"].items():
        minimum = float(target["minimum"])
        maximum = float(target["maximum"])
        min_samples = int(target.get("min_samples", 1))
        if season_count < min_samples:
            findings.append(
                MetricFinding(
                    metric,
                    target["label"],
                    None,
                    minimum,
                    maximum,
                    target.get("unit", ""),
                    "skipped",
                    season_count,
                )
            )
            continue
        value = float(baseline[metric])
        status = "pass" if minimum <= value <= maximum else "low" if value < minimum else "high"
        findings.append(
            MetricFinding(
                metric,
                target["label"],
                value,
                minimum,
                maximum,
                target.get("unit", ""),
                status,
                season_count,
            )
        )
    return findings


def _sensitivity_findings(
    profile: dict,
    grouped: Mapping[str, list[SeasonSample]],
) -> list[SensitivityFinding]:
    baseline = {sample.seed: sample for sample in grouped.get("baseline", [])}
    threshold = float(profile["adversarial"]["dominance_threshold_points"])
    findings = []
    for scenario_name, samples in grouped.items():
        if scenario_name == "baseline":
            continue
        point_uplifts = []
        strength_uplifts = []
        for sample in samples:
            paired = baseline.get(sample.seed)
            if paired is None:
                continue
            point_uplifts.append(
                sample.controlled_team_points - paired.controlled_team_points
            )
            strength_uplifts.append(
                sample.team_strengths["1"] - paired.team_strengths["1"]
            )
        if not point_uplifts:
            continue
        mean_uplift = statistics.fmean(point_uplifts)
        findings.append(
            SensitivityFinding(
                scenario=scenario_name,
                mean_points_uplift=mean_uplift,
                median_points_uplift=statistics.median(point_uplifts),
                maximum_points_uplift=max(point_uplifts),
                mean_strength_uplift=statistics.fmean(strength_uplifts),
                threshold=threshold,
                status="dominant" if mean_uplift > threshold else "within_limit",
            )
        )
    return findings


def _tuning_recommendations(findings: Iterable[MetricFinding]) -> list[str]:
    messages = {
        "average_combined_goals": "Tune shot-quality and save-conversion equations before adding more offensive systems.",
        "home_win_rate": "Add or reduce a bounded home-ice effect and validate it across many seeds.",
        "overtime_rate": "Adjust regulation scoring variance before changing overtime resolution.",
        "one_goal_game_rate": "Review score dispersion and late-game behavior so close-game frequency is credible.",
        "average_shot_attempts_per_team": "Tune possession-event volume before interpreting shooting or goaltending results.",
        "average_points_stddev": "Adjust team-strength separation or game randomness to improve standings dispersion.",
        "strength_points_correlation": "Rebalance attribute influence versus randomness; ratings should matter without making outcomes deterministic.",
        "champion_concentration": "Review franchise symmetry and repeated-winner concentration for hidden team-ID advantages.",
    }
    return [messages[item.metric] for item in findings if item.status in {"low", "high"}]


def analyze_samples(
    profile: dict,
    samples: Iterable[SeasonSample],
    reproducibility: dict | None = None,
) -> dict:
    materialized = list(samples)
    if not materialized:
        raise ValueError("At least one season sample is required")
    grouped: dict[str, list[SeasonSample]] = {}
    for sample in materialized:
        grouped.setdefault(sample.scenario, []).append(sample)
    if "baseline" not in grouped:
        raise ValueError("A baseline sample is required")

    summaries = {
        scenario: _scenario_summary(group)
        for scenario, group in sorted(grouped.items())
    }
    findings = _metric_findings(profile, summaries["baseline"])
    sensitivity = _sensitivity_findings(profile, grouped)
    structural_failures = [
        {
            "seed": sample.seed,
            "scenario": sample.scenario,
            "errors": list(sample.structural_errors),
        }
        for sample in materialized
        if sample.structural_errors
    ]
    reproducibility_failed = bool(
        reproducibility is not None and not reproducibility.get("passed", False)
    )
    benchmark_misses = [
        item for item in findings if item.status in {"low", "high"}
    ]
    dominance_alerts = [item for item in sensitivity if item.status == "dominant"]
    if structural_failures or reproducibility_failed:
        status = "invalid"
    elif benchmark_misses or dominance_alerts:
        status = "needs_tuning"
    else:
        status = "within_guardrails"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "profile_id": profile["profile_id"],
            "as_of": profile["as_of"],
            "description": profile.get("description", ""),
            "sources": profile.get("sources", []),
        },
        "status": status,
        "run": {
            "samples": len(materialized),
            "baseline_seasons": len(grouped["baseline"]),
            "scenarios": list(sorted(grouped)),
        },
        "structural_integrity": {
            "status": "fail" if structural_failures else "pass",
            "failures": structural_failures,
        },
        "reproducibility": reproducibility,
        "scenario_summaries": summaries,
        "benchmark_findings": [asdict(item) for item in findings],
        "sensitivity_findings": [asdict(item) for item in sensitivity],
        "tuning_recommendations": list(dict.fromkeys(_tuning_recommendations(findings))),
        "samples": [asdict(sample) for sample in materialized],
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# NHL GM Simulation Calibration Report",
        "",
        f"**Overall status:** `{report['status']}`  ",
        f"**Profile:** `{report['profile']['profile_id']}` (as of {report['profile']['as_of']})  ",
        f"**Baseline seasons:** {report['run']['baseline_seasons']}  ",
        f"**Scenarios:** {', '.join(report['run']['scenarios'])}",
        "",
        "## Structural integrity",
        "",
    ]
    structural = report["structural_integrity"]
    if structural["status"] == "pass":
        lines.append("All schedules, records, goal ledgers, point ledgers, and result logs reconciled.")
    else:
        lines.append("Structural failures must be fixed before tuning simulation realism:")
        for failure in structural["failures"]:
            lines.append(
                f"- Seed {failure['seed']} / {failure['scenario']}: "
                + "; ".join(failure["errors"])
            )
    if report["reproducibility"] is not None:
        lines += [
            "",
            "## Reproducibility",
            "",
            f"- Seed: {report['reproducibility']['seed']}",
            f"- Passed: {report['reproducibility']['passed']}",
            f"- Digest: `{report['reproducibility']['first_digest']}`",
        ]
    lines += [
        "",
        "## Baseline benchmark findings",
        "",
        "| Metric | Value | Guardrail | Status |",
        "|---|---:|---:|---|",
    ]
    for finding in report["benchmark_findings"]:
        value = "—" if finding["value"] is None else f"{finding['value']:.4f}"
        lines.append(
            f"| {finding['label']} | {value} | "
            f"{finding['minimum']:.4f}–{finding['maximum']:.4f} "
            f"{finding['unit']} | {finding['status']} |"
        )
    lines += [
        "",
        "## Scenario summaries",
        "",
        "| Scenario | Seasons | Goals/game | Home win | OT | One-goal | Attempts/team | Points SD | Strength→points |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario, summary in report["scenario_summaries"].items():
        lines.append(
            f"| {scenario} | {summary['seasons']} | "
            f"{summary['average_combined_goals']:.3f} | "
            f"{summary['home_win_rate']:.3f} | "
            f"{summary['overtime_rate']:.3f} | "
            f"{summary['one_goal_game_rate']:.3f} | "
            f"{summary['average_shot_attempts_per_team']:.3f} | "
            f"{summary['average_points_stddev']:.3f} | "
            f"{summary['strength_points_correlation']:.3f} |"
        )
    if report["sensitivity_findings"]:
        lines += [
            "",
            "## Single-axis adversarial sensitivity",
            "",
            "| Scenario | Mean point uplift | Median | Maximum | Strength uplift | Threshold | Status |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        for finding in report["sensitivity_findings"]:
            lines.append(
                f"| {finding['scenario']} | {finding['mean_points_uplift']:.2f} | "
                f"{finding['median_points_uplift']:.2f} | "
                f"{finding['maximum_points_uplift']} | "
                f"{finding['mean_strength_uplift']:.2f} | "
                f"{finding['threshold']:.2f} | {finding['status']} |"
            )
    lines += ["", "## Tuning queue", ""]
    recommendations = report["tuning_recommendations"]
    if recommendations:
        lines.extend(f"- {item}" for item in recommendations)
    else:
        lines.append("- No benchmark-driven tuning action was generated.")
    lines += [
        "",
        "## Interpretation boundary",
        "",
        report["profile"]["description"],
        "Structural failures are release blockers. Benchmark misses are tuning evidence and only become CI blockers when strict mode is enabled.",
        "",
    ]
    return "\n".join(lines)


def write_report(report: dict, json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run seeded NHL GM seasons and produce a calibration report."
    )
    parser.add_argument("--seasons", type=int, default=10)
    parser.add_argument("--start-seed", type=int, default=1000)
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["baseline"],
        choices=sorted(SCENARIOS),
    )
    parser.add_argument(
        "--adversarial",
        action="store_true",
        help="Include speed, shooting, and goaltending single-axis stress scenarios.",
    )
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE_PATH)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("artifacts/calibration/latest.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("artifacts/calibration/latest.md"),
    )
    parser.add_argument("--no-reproducibility", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit status unless every guardrail passes.",
    )
    args = parser.parse_args()

    scenarios = list(args.scenarios)
    if args.adversarial:
        scenarios.extend(["speed_stack", "shooting_stack", "goalie_stack"])
    profile = load_profile(args.profile)
    report = CalibrationLab(profile).run(
        seasons=args.seasons,
        start_seed=args.start_seed,
        scenarios=scenarios,
        check_reproducibility=not args.no_reproducibility,
    )
    write_report(report, args.json_output, args.markdown_output)
    baseline = report["scenario_summaries"]["baseline"]
    print(
        f"Calibration {report['status']}: {baseline['seasons']} baseline seasons, "
        f"{baseline['games']} games, {len(report['tuning_recommendations'])} tuning actions."
    )
    print(f"JSON: {args.json_output}")
    print(f"Markdown: {args.markdown_output}")
    return 2 if args.strict and report["status"] != "within_guardrails" else 0


if __name__ == "__main__":
    raise SystemExit(main())
