# NHL GM Mobile UI

This folder contains the first mobile game UI prototype for the NHL GM game, built with Expo and React Native.

## What is included

The prototype currently includes five main mobile screens:

- **Dashboard** — team overview, cap space, job security, next game, and quick actions.
- **Roster** — NHL roster table with age, position, overall, AAV, and fog-of-war uncertainty.
- **Game Simulation** — final score, shot/corsi comparison, game log, and result summary.
- **Trade Center** — live roster selection, server-side CASV analysis, relationship friction, transactional proposals, and decision feedback.
- **Front Office** — advisor risk panel, coaching, scouting, injuries, waivers, business operations, fan volatility, and GM relationships.

The dashboard, roster, and Trade Center now read persistent game state from the Python API. The dashboard's **Advance Day** action settles daily finances, simulates the scheduled league slate, updates standings, and refreshes the mobile state. The Trade Center cycles through both live rosters, recalculates CASV for each player pairing, and submits accepted swaps through an atomic backend transaction. Game Simulation and Front Office still use prototype data while their endpoints are developed. If the API is unavailable, connected read-only screens display clearly labeled offline demo data.

## Run locally

From the repository root:

```bash
python src/nhl_gm_api.py

# In a second terminal:
cd mobile
npm install
npm start
```

Then open it with Expo Go on your phone, or run it in an Android/iOS simulator.

The default API URL is `http://127.0.0.1:8000/api/v1`. For Expo Go on a physical device, point the app at the development computer's LAN address before starting Expo:

```bash
EXPO_PUBLIC_API_URL=http://192.168.1.10:8000/api/v1 npm start
```

In PowerShell, use `$env:EXPO_PUBLIC_API_URL='http://192.168.1.10:8000/api/v1'` before `npm start`.

## Current architecture

```text
mobile/
├── App.js          # Main React Native UI prototype
├── app.json        # Expo app config
├── package.json    # Expo dependencies and scripts
└── README.md       # Mobile setup notes
```

## Backend connection

The existing simulation engine lives at:

```text
../src/nhl_gm_core.py
```

The dependency-free HTTP service lives at `../src/nhl_gm_api.py`, schedule and standings orchestration lives at `../src/league_orchestrator.py`, and structured trade evaluation/execution lives at `../src/trade_service.py`. The next backend increment is to connect direct game simulation or scouting actions to the mobile UI.
