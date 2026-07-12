# NHL GM Game

A Python-based NHL general manager simulation game built around persistent franchise state, season-versioned rules, CBA-style cap logic, scouting uncertainty, tactical match simulation, trade evaluation, executive risk management, and a mobile-first franchise UI prototype.

## Current Core

The simulation engine lives in:

```bash
src/nhl_gm_core.py
```

It now binds every save to an immutable season ruleset from `config/rules/`. New saves must receive a cap-accrual denominator derived from the generated official schedule; existing prototype saves migrate their stored `max_days` value automatically.

Run a new 2025-26 prototype save locally with:

```bash
NHL_GM_ACCRUAL_DAYS=192 python src/nhl_gm_core.py
```

The environment value is an explicit schedule input, not a permanent league constant. When schedule generation is added, the engine will pass this value directly from the persisted league calendar.

## Mobile UI Prototype

A first-pass Expo / React Native mobile interface lives in:

```bash
mobile/App.js
```

The mobile UI currently uses mock game state. The next engineering step is to expose the season-aware Python simulation through an API layer and replace mock state with live persisted data.

## Implemented Systems

- Persistent SQLite state for teams, players, league calendar, budgets, cap state, and roster data.
- Versioned season rules registry with source provenance and verification controls.
- Backward-compatible save migration adding season ID, rules schema, cap floor, roster limit, and accrual days.
- Daily cap charge and deadline-room calculations using the saved schedule denominator.
- Registry-driven roster and salary-cap compliance checks.
- Scouting fog-of-war with exponential uncertainty decay.
- Contract-adjusted surplus-value analysis.
- Advisor risk scoring.
- Front-office research and training curriculum agent.

## Tests

```bash
pytest
```

The integration suite covers season binding, legacy migration, season mismatch protection, dynamic daily accounting, and registry-driven compliance.
