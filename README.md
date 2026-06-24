# NHL GM Game

A Python-based NHL general manager simulation game built around persistent franchise state, CBA-style cap logic, scouting uncertainty, tactical match simulation, trade evaluation, executive risk management, and a mobile-first franchise UI prototype.

## Current Core

The initial game engine lives in:

```bash
src/nhl_gm_core.py
```

It currently runs as a terminal-based simulation app with SQLite persistence.

## Mobile UI Prototype

A first-pass Expo / React Native mobile interface now lives in:

```bash
mobile/App.js
```

The mobile UI includes:

- Dashboard
- Roster
- Game Simulation
- Trade Center
- Front Office
- Advisor Risk panel

Run it locally with:

```bash
python src/nhl_gm_api.py

# In a second terminal:
cd mobile
npm install
npm start
```

The dashboard and roster load live persisted state from the Python API. If the API is unavailable, those screens remain usable with clearly labeled demo data. Set `EXPO_PUBLIC_API_URL` when the mobile client cannot reach the default `http://127.0.0.1:8000/api/v1` address.

## JSON API

The dependency-free API initializes the same SQLite game state as the terminal app:

```bash
python src/nhl_gm_api.py --host 0.0.0.0 --port 8000
```

Available read endpoints:

- `GET /api/v1/health`
- `GET /api/v1/teams`
- `GET /api/v1/teams/{team_id}/dashboard`
- `GET /api/v1/teams/{team_id}/roster`
- `GET /api/v1/standings`
- `GET /api/v1/schedule?day={day}&team_id={team_id}`
- `POST /api/v1/advance-day`

Advancing a day settles cap charges, recovers player fatigue, simulates every scheduled game, and updates persistent standings. The seeded two-team prototype produces a balanced 82-game home-and-away schedule across the 186-day calendar.

Use `--db path/to/game.db` or `NHL_GM_DB_PATH` to select a different save file.

## Implemented Systems

- **Persistent SQLite state machine** for teams, players, league calendar, budgets, cap state, and roster data.
- **Daily cap charge engine** using `Daily Charge = Player AAV / 186`.
- **Accrued deadline buying power** using unused daily cap margin and deadline scaling.
- **Roster legality checks** for 23-player roster limits and the $92,000,000 salary cap ceiling.
- **Scouting fog-of-war** with exponential uncertainty decay based on observation count.
- **60-minute tactical match simulator** using possession, Corsi-style shot attempts, line chemistry, xG modifiers, royal-road passing, and goalie fatigue.
- **Persistent league loop** with schedule generation, structured game results, standings, overtime points, streaks, and daily slate automation.
- **Contract-Adjusted Surplus Value trade desk** for evaluating player trades against team mandates and relationship friction.
- **Advisor Risk Scoring Engine** for cap exposure, overpaid assets, and league trust risk.
- **Executive terminal shell** with box-drawing interface panels and command-driven simulation controls.

## Run the Python Engine Locally

```bash
python src/nhl_gm_core.py
```

The app creates a local SQLite database named:

```bash
nhl_gm_core.db
```

Run the automated API tests with:

```bash
python -m unittest discover -s tests -v
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
