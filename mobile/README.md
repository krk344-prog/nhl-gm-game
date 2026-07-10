# NHL GM Mobile UI

This folder contains the Alpha 0.2 mobile client for the NHL GM game, built with Expo and React Native.

## What is included

The alpha client includes five main mobile screens:

- **Dashboard** — team overview, cap space, job security, next game, and quick actions.
- **Roster** — NHL roster table with age, position, overall, AAV, and fog-of-war uncertainty.
- **Game Center** — latest result, next opponent, recent games, and live league standings.
- **Trade Center** — trade partner selection, live roster selection, server-side CASV analysis, transactional proposals, and trade history.
- **Front Office** — automatic-save metadata, guarded New Game/reset controls, and clearly labeled future systems.

The dashboard, roster, Game Center, Trade Center, and save controls now read persistent state from the Python API. Systems not included in Alpha 0.2 are disabled and labeled as coming soon.

## Run locally

From the repository root, use the one-command launcher:

```bash
python scripts/start_dev.py
```

Then open it with Expo Go on your phone, or run it in an Android/iOS simulator.

The launcher sets the API URL to the development computer's detected LAN address. To override it:

```bash
python scripts/start_dev.py --lan-ip 192.168.1.10
```

## Current architecture

```text
mobile/
├── App.js          # Main React Native alpha client
├── app.json        # Expo app config
├── package.json    # Expo dependencies and scripts
└── README.md       # Mobile setup notes
```

## Backend connection

The existing simulation engine lives at:

```text
../src/nhl_gm_core.py
```

The dependency-free HTTP service lives at `../src/nhl_gm_api.py`, save controls live at `../src/game_service.py`, schedule and standings orchestration lives at `../src/league_orchestrator.py`, and structured trade evaluation/execution lives at `../src/trade_service.py`.
