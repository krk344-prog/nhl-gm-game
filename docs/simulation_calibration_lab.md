# Simulation Calibration Lab

The calibration lab runs the actual persistent league engine through isolated, deterministic seasons and produces both machine-readable and human-readable evidence about simulation quality.

## What it validates

The lab separates three different failure classes:

1. **Structural integrity** — every scheduled game completes, every team plays the expected home/away schedule, standings records reconcile, goals-for equals goals-against, standings points reconcile with overtime results, ties do not survive, and every game contains the expected simulation telemetry.
2. **Behavioral calibration** — scoring, home advantage, overtime frequency, close-game frequency, event volume, standings dispersion, and the relationship between roster strength and results are compared with configurable guardrails.
3. **Adversarial sensitivity** — paired seasons stress one attribute at a time to identify whether speed, shooting, or goaltending becomes a dominant strategy.

Structural failures are always blockers. Benchmark misses create a tuning queue but do not fail the normal command. `--strict` converts every calibration miss into a non-zero exit status for a future release gate.

## Run it

Quick baseline pass:

```bash
python -m src.simulation_calibration \
  --seasons 3 \
  --no-reproducibility
```

Recommended development pass:

```bash
python -m src.simulation_calibration \
  --seasons 10 \
  --adversarial
```

Larger release-candidate pass:

```bash
python -m src.simulation_calibration \
  --seasons 25 \
  --adversarial \
  --strict
```

Default outputs:

- `artifacts/calibration/latest.json`
- `artifacts/calibration/latest.md`

The JSON file retains every season sample, scenario summary, benchmark result, structural failure, reproducibility digest, and sensitivity finding. The Markdown file is the review-ready tuning report.

## Determinism

Each run creates a temporary SQLite save, regenerates the league from the requested seed, and seeds match randomness independently from roster generation. Re-running the same baseline seed must produce the same schedule-and-standings digest. Calibration never modifies the user's normal save.

## Benchmark profile

Guardrails live in `config/calibration_benchmarks.json`. The initial `nhl-2025-26-alpha-v0` profile is intentionally broad because the current game is still an eight-team alpha. It is a tuning envelope rather than an official NHL statistical snapshot.

The profile is versioned and contains:

- league structure assumptions
- metric minimums and maximums
- minimum sample requirements
- adversarial dominance thresholds
- public source references

Tighten the ranges only after importing and validating a reproducible league-statistics snapshot. Do not silently change an existing profile after it has been used for release evidence; add a new profile version.

## Metrics

| Metric | Grain | Purpose |
|---|---|---|
| Combined goals per game | Game | Detect under- or over-scoring |
| Home-team win rate | Game | Detect missing or excessive home advantage |
| Overtime rate | Game | Validate regulation score distribution |
| One-goal game rate | Game | Measure competitive closeness |
| Simulated shot attempts per team | Team-game | Validate event volume before interpreting finishing/goaltending |
| Points standard deviation | Team-season | Measure standings separation |
| Roster-strength/points correlation | Team-season pooled across seeds | Ensure ratings matter without making outcomes deterministic |
| Champion concentration | Multi-season | Detect hidden team-ID or schedule advantages |

## Adversarial scenarios

The stress tests apply the same seed to baseline and modified saves, then compare the controlled team's points:

- `speed_stack`: +8 speed to all controlled-team forwards
- `shooting_stack`: +8 shooting to all controlled-team forwards
- `goalie_stack`: +8 positioning and reflexes to both controlled-team goalies

These are controlled sensitivity experiments, not legal roster-building actions. A scenario is labeled `dominant` when its paired average point uplift exceeds the threshold in the benchmark profile.

## Tests

```bash
python -m unittest tests.test_simulation_calibration -v
```

The tests run two complete seeded seasons once per test class, then verify structural reconciliation, deterministic replay, benchmark classification, report serialization, and the adversarial scenario catalog.
