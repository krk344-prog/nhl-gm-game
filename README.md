# NHL GM Game

A Python-based NHL general manager simulation game built around persistent franchise state, CBA-style cap logic, scouting uncertainty, tactical match simulation, trade evaluation, and executive risk management.

## Current Core

The initial game engine lives in:

```bash
src/nhl_gm_core.py
```

It currently runs as a terminal-based simulation app with SQLite persistence.

## Implemented Systems

- **Persistent SQLite state machine** for teams, players, league calendar, budgets, cap state, and roster data.
- **Daily cap charge engine** using `Daily Charge = Player AAV / 186`.
- **Accrued deadline buying power** using unused daily cap margin and deadline scaling.
- **Roster legality checks** for 23-player roster limits and the $92,000,000 salary cap ceiling.
- **Scouting fog-of-war** with exponential uncertainty decay based on observation count.
- **60-minute tactical match simulator** using possession, Corsi-style shot attempts, line chemistry, xG modifiers, royal-road passing, and goalie fatigue.
- **Contract-Adjusted Surplus Value trade desk** for evaluating player trades against team mandates and relationship friction.
- **Advisor Risk Scoring Engine** for cap exposure, overpaid assets, and league trust risk.
- **Executive terminal shell** with box-drawing interface panels and command-driven simulation controls.

## Run Locally

```bash
python src/nhl_gm_core.py
```

The app creates a local SQLite database named:

```bash
nhl_gm_core.db
```

## Roadmap Direction

The next development phase is to move from a single-file terminal prototype into a modular, multi-season franchise engine. Planned modules include:

- Out-of-town match automation
- Draft lottery allocation
- Player lifecycle progression and veteran decline
- Retirement and buyout processing
- UFA auction / July 1 free agency matrix
- Waiver wire and reassignment systems
- LTIR emergency cap relief
- Coaching staff and tactical system mastery
- Business operations, revenue, and attendance modeling
- Fan volatility, media pressure, and GM job security systems

See [`docs/feature_landscape_and_roadmap.md`](docs/feature_landscape_and_roadmap.md) for the fuller architecture and roadmap notes.
