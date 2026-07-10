# NHL GM Game

A Python-based NHL general manager simulation game built around persistent franchise state, CBA-style cap logic, scouting uncertainty, tactical match simulation, trade evaluation, executive risk management, and a mobile-first franchise UI. Alpha 0.2 is designed for closed mechanics testing.

## Alpha 0.2 Testing Loop

- Eight balanced fictional NHL franchises with 23-player rosters.
- Persistent controlled-franchise selection and automatic local saving.
- Guarded New Game/reset flow with deterministic test seeds.
- 82-game schedules, live results, recent games, and eight-team standings.
- Functional roster position filters.
- Live trade partner selection, CASV evaluation, execution, and history.
- Clearly disabled placeholders for systems not yet implemented.

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

Start the API and mobile client together with:

```bash
python scripts/start_dev.py
```

The launcher installs mobile dependencies on the first run, detects the computer's LAN address, starts the API, and configures Expo Go automatically. Use `python scripts/start_dev.py --lan-ip 192.168.1.10` if LAN detection needs to be overridden.

The dashboard, roster, Game Center, and Trade Center load persisted state from the Python API. If the API is unavailable, the client reports the connection failure and disables state-changing controls. Set `EXPO_PUBLIC_API_URL` when the mobile client cannot reach the default `http://127.0.0.1:8000/api/v1` address.

## JSON API

The dependency-free API initializes the same SQLite game state as the terminal app:

```bash
python src/nhl_gm_api.py --host 0.0.0.0 --port 8000
```

Available read endpoints:

- `GET /api/v1/health`
- `GET /api/v1/game`
- `GET /api/v1/debug-report`
- `GET /api/v1/teams`
- `GET /api/v1/teams/{team_id}/dashboard`
- `GET /api/v1/teams/{team_id}/roster`
- `GET /api/v1/standings`
- `GET /api/v1/schedule?day={day}&team_id={team_id}`
- `GET /api/v1/trade-market?user_team_id={team_id}`
- `GET /api/v1/trades/history?user_team_id={team_id}`
- `POST /api/v1/advance-day`
- `POST /api/v1/game/select-team`
- `POST /api/v1/game/reset`
- `POST /api/v1/trades/evaluate`
- `POST /api/v1/trades/execute`

Advancing a day settles cap charges, recovers player fatigue, simulates every scheduled game, and updates persistent standings. The seeded eight-team alpha produces 328 games, with 82 games per franchise across the 186-day calendar.

The Trade Center reads both persisted rosters, recalculates CASV against the rival mandate and GM relationship premium, and records approved, rejected, or CBA-blocked proposals. Approved one-for-one trades swap player rights in a single SQLite transaction only after both post-trade rosters pass the cap and 23-player checks.

Use `--db path/to/game.db` or `NHL_GM_DB_PATH` to select a different save file.

## Implemented Systems

- **Persistent SQLite state machine** for teams, players, league calendar, budgets, cap state, and roster data.
- **Daily cap charge engine** using `Daily Charge = Player AAV / 186`.
- **Accrued deadline buying power** using unused daily cap margin and deadline scaling.
- **Roster legality checks** for 23-player roster limits and the $92,000,000 salary cap ceiling.
- **Scouting fog-of-war** with exponential uncertainty decay based on observation count.
- **60-minute tactical match simulator** using possession, Corsi-style shot attempts, line chemistry, xG modifiers, royal-road passing, and goalie fatigue.
- **Persistent league loop** with schedule generation, structured game results, standings, overtime points, streaks, and daily slate automation.
- **Live Contract-Adjusted Surplus Value trade desk** with persisted market rosters, relationship premiums, transactional execution, CBA revalidation, and proposal history.
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

The suite includes a complete 186-day/328-game season simulation. Pull requests also run this suite and an Android production export through GitHub Actions.

See [`docs/alpha_testing_guide.md`](docs/alpha_testing_guide.md) for the closed-test checklist and bug-report format.

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
