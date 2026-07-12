# Scouting Intelligence v1

Scouting Intelligence replaces globally visible player ratings with organization-specific knowledge. The simulation engine and rival AI retain hidden true attributes, while user-facing roster, dashboard, trade, and scouting APIs expose only estimates, ranges, confidence, report history, and qualitative assessments.

## Core model

Each NHL organization receives:

- five scouts: pro, amateur, regional, goalie, and analytics
- independent knowledge records for every player in the database
- workload capacity and assignment costs
- persistent assignment and report history
- confidence for current ability, potential, health, character, and role fit
- stale-report detection after 30 simulation days

Players receive hidden simulation fields for potential, durability, character, and scouting region. These fields are never returned by normal player APIs.

## Assignment workflow

Assignments require a team, scout, player, focus, and depth.

Focus options:

- `overall`
- `potential`
- `health`
- `character`
- `role_fit`

Depth options:

| Depth | Duration | Observations | Cost | Use |
|---|---:|---:|---:|---|
| Quick | 2 days | 1 | $5,000 | Triage and deadline checks |
| Standard | 5 days | 3 | $12,500 | Normal pro or amateur coverage |
| Deep | 10 days | 6 | $25,000 | Draft, trade, and contract decisions |

A scout cannot exceed workload capacity. Multiple active assignments for the same player and focus are blocked. Costs are deducted from team operating cash when the assignment is created.

Completed assignments are processed automatically during `advance_day`. Reports remain fallible and retain at least a one-point uncertainty range even at the highest confidence level.

## Report quality

Report quality combines:

- accuracy or projection skill, depending on assignment focus
- communication
- efficiency
- active workload
- specialty fit
- regional fit
- scout bias
- assignment depth

Specialty bonuses apply to goalie scouting, amateur players, professional players, analytics-oriented reviews, and matching regional assignments.

## API

Read endpoints:

- `GET /api/v1/scouting?team_id={team_id}`
- `GET /api/v1/scouting/reports?team_id={team_id}&player_id={optional}`
- `GET /api/v1/scouting/player?team_id={team_id}&player_id={player_id}`
- `GET /api/v1/scouting/calibration?team_id={team_id}&samples={n}`

Create an assignment:

```http
POST /api/v1/scouting/assignments
Content-Type: application/json

{
  "team_id": 1,
  "scout_id": 3,
  "player_id": 47,
  "focus": "potential",
  "depth": "deep"
}
```

The existing roster, dashboard, and trade-market APIs are scouting-aware. They do not return shooting, passing, positioning, reflexes, speed, checking, hidden potential, durability, character rating, or scouting region.

## Accuracy calibration

The calibration endpoint repeatedly compares the strongest and weakest scout on the same external player pool. It also compares a regional specialist inside and outside the assigned territory.

The test suite requires stronger scouts to produce lower mean absolute error over a large deterministic sample. Regional results are reported separately because player-pool composition can affect small samples.

## Validation

```bash
python -m unittest tests.test_scouting_intelligence -v
python -m unittest discover -s tests -v
```

The integration tests verify:

- five staff roles and complete team/player knowledge coverage
- no hidden-rating leakage through roster or trade payloads
- report completion through calendar advancement
- uncertainty reduction after deep assignments
- workload enforcement
- stronger-scout calibration performance
- clean scouting state after a new-game reset

## Current UI boundary

The JSON API and data contracts are complete for the Scouting Center, assignment creation, report inbox, priority board, and player dossier. The mobile navigation and interactive assignment screens are the next presentation-layer pass; this branch does not remove or regress the existing Alpha 0.2 mobile screens.
