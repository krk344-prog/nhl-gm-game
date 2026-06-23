# NHL GM Mobile UI

This folder contains the first mobile game UI prototype for the NHL GM game, built with Expo and React Native.

## What is included

The prototype currently includes five main mobile screens:

- **Dashboard** — team overview, cap space, job security, next game, and quick actions.
- **Roster** — NHL roster table with age, position, overall, AAV, and fog-of-war uncertainty.
- **Game Simulation** — final score, shot/corsi comparison, game log, and result summary.
- **Trade Center** — player offer cards, CASV analysis, relationship friction, and submit button.
- **Front Office** — advisor risk panel, coaching, scouting, injuries, waivers, business operations, fan volatility, and GM relationships.

The UI currently uses mock state that mirrors the Python simulation engine. The next step is to connect this front end to the persistent SQLite simulation logic through an API layer.

## Run locally

From the repository root:

```bash
cd mobile
npm install
npm start
```

Then open it with Expo Go on your phone, or run it in an Android/iOS simulator.

## Current architecture

```text
mobile/
├── App.js          # Main React Native UI prototype
├── app.json        # Expo app config
├── package.json    # Expo dependencies and scripts
└── README.md       # Mobile setup notes
```

## Backend connection plan

The existing simulation engine lives at:

```text
../src/nhl_gm_core.py
```

Recommended next step:

1. Split the Python engine into service modules.
2. Add a small FastAPI backend around the SQLite state.
3. Expose endpoints such as `/dashboard`, `/roster`, `/simulate-game`, `/trade-evaluation`, and `/advance-day`.
4. Replace the mock state in `mobile/App.js` with API calls.
