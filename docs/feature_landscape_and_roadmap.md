# NHL GM Game — Feature Landscape and Roadmap

## Landscape of Features Built Into the Game Already

The core master state architecture has graduated from a sandbox model into an integrated, transaction-isolated simulation engine. The features currently written and communicating smoothly include the following systems.

## 1. Database Persistence and Entity State Anchor

### Transaction-Isolated State Machine

Implements strict data constraints across a relational database, tracking leagues, organizations, budgets, staff, and skaters across simulation loops to reduce data desynchronization.

## 2. Temporal Engine and Daily CBA Compliance

### Daily Cap Hit Tracking and Smoothing Loop

Abandons flat annual salary deductions in favor of real-time daily cap tracking calculated as:

```text
Daily Charge = Player AAV / 186
```

### Accrued Deadline Room Calculation

Unspent daily cap hit margins are dynamically stored in an accrual ledger, automatically amplifying Trade Deadline acquisition buying power via:

```text
Accrued Margin × (186 / Days Remaining)
```

### Roster Legal Fences

Enforces strict compliance checks, including the active 23-man roster limit and the active $92,000,000 maximum hard-cap upper roof.

## 3. Scouting Fog-of-War Vector Engine

### Exponential Attribute Uncertainty Decay

Attributes for players remain masked behind wide standard deviations to counteract user exploit loops.

### Observation Margin Compression

Applies an exponential decay equation where direct asset deployment and scouting observations actively collapse attribute uncertainty back to true data realities:

```text
sigma_current = sigma_base × e^-(lambda × N_obs × epsilon_s)
```

## 4. 60-Minute Tactical Shift Simulation Core

### Corsi-Driven Possession Calculator

Resolves games via a minute-by-minute tactical loop tracking shot attempts and possession curves rather than randomized goal assignment.

### Archetype Line Chemistry Handshakes

Forward line groups containing a designated **Elite Playmaker** alongside a **Volume Sniper** trigger a deterministic +15% execution bonus on possession loops and shot generation quality.

### Royal Road Attack Modifier

Cross-crease passing sequences simulate high-danger zone entry points, scaling expected goals by:

```text
xG × 1.45
```

### Goalie Fatigue Scheduling Guardrails

Goalies accumulate fatigue on consecutive nights. Overriding rest parameters inside back-to-back scheduling maps automatically levies a -5% performance tax onto baseline Positioning and Reflex indexes.

## 5. Contract-Adjusted Surplus Value Trade Desk

### Strategic Philosophy Alignment

Evaluates asset values by screening them against distinct rival Franchise Mandates. Pitching a contract to a **Moneyball Auditor** factors in heavy efficiency constraints, while a **Win-Now Titan** prioritizes immediate attribute values over cap weights.

### Relational Friction Modifier

Tracks a living network reputation score between GMs. Low relationship standing enforces a severe premium tax scalar on incoming trade inquiries, pricing the user out of the market unless an aggressive premium asset is provided.

```text
R_ij = relationship score between GM actors
```

### Pre-Commit Transaction Gates

Runs complete compliance checks on roster limits and cap bounds before executing database row migrations, rolling back any transactions that trigger long-term cap non-compliance.

## 6. AI Advisor Risk Scoring Engine

### Corporate Roster Audit Panel

A background compliance diagnostic interface that evaluates roster efficiency, salary overpayments, cap headroom margins, and average league trust to return a raw front-office risk vector between 0 and 100.

## 7. Level 1 and Level 2 Box-Drawing Interface Shell

### Executive Terminal Interface

Uses explicit Unicode box-drawing layouts to separate fixed status overview elements from dynamic, contextual data sheet views.

```text
┌ ─ ┐ │ └ ┘
```

# Roadmap: Direction of New Features to Be Added

To transform the game from an isolated standalone execution file into an enterprise-grade, multi-season franchise game loop, development should shift toward the **Seasonal Lifecycle Sequence** and **Subsidiary Front-Office Systems**.

## 1. Out-of-Town Match Automation Loop

### The Orchestrator Extension

The current simulation calculates single user-driven matchups. The next loop needs an out-of-town league automation grid to simulate parallel match results across the remaining AI teams simultaneously when the user advances time.

Proposed module:

```text
league_orchestrator.py
```

Primary responsibilities:

- Generate daily league schedule slate.
- Simulate non-user games during date advancement.
- Persist standings, goal differential, streaks, and team form.
- Feed standings and competitive tier into trade, free agency, and fan-pressure systems.

## 2. Offseason Lifecycle Phase Loop

### Draft Lottery Allocation Engine

Proposed module:

```text
draft_lottery_engine.py
```

Scale odds coefficients into an integer-array selection mapping to mimic real-world lotteries, while implementing a **Capped Vault Safety Bound** to prevent bubble teams from jumping past slot limits unearned.

### Non-Linear Player Progression and Attrition Core

Proposed module:

```text
player_lifecycle_progression.py
```

Move past flat attribute ticks by implementing an exponential veteran decay cliff calculated via:

```text
(new_age - floor)^1.3
```

This ensures aging stars experience minimal drops at age 31, but hit an accelerated performance cliff at age 34–35.

### Player Retirement and Buyout Penalties Matrix

Processes natural roster attrition based on age, clears dead contracts from active sheets, handles veteran legacy preservation boards, and writes compliance math for mid-season contract buyouts.

Proposed module:

```text
contract_exit_engine.py
```

### July 1 UFA Inflation Matrix

Runs competitive multi-team free-agent auctions driven by a **Player Interest Index**.

```text
PII = Player Interest Index
```

The index should score and resolve multi-team financial contract demands by balancing:

- Offer total value
- Team contention tier
- Regional tax bracket
- Immediate roster role
- Player loyalty and personality modifiers
- Prior GM relationship quality

Proposed module:

```text
free_agency_market.py
```

## 3. Roster Management Overhauls

### Waiver Wire Clearance and Reassignment Intercept

Implements 24-hour waiver placement log tables, waiver priority lists, and roster sizing intercept filters. This includes compliance rules for burying minor-league salary surpluses within the AHL affiliate space.

Proposed module:

```text
waiver_wire_engine.py
```

### Long-Term Injured Reserve Emergency Core

Integrates complex cap exceptions. When an asset experiences severe physical injury, their salary can be shifted into temporary emergency relief pools, allowing the franchise to exceed the hard ceiling within strict substitute boundaries.

Proposed module:

```text
ltir_engine.py
```

## 4. Auxiliary Operations Layers

### Coaching Staff and System Mastery

Tracks coach hiring carousels and maps a roster-to-system tactical compatibility filter.

```text
S_fit = roster-to-system fit score
```

Staff system mastery translates directly into active attribute multipliers on the ice. Example: executing a **1-3-1 Umbrella** scales passing capabilities but exposes defense lines to shorthanded counter-attacks.

Proposed module:

```text
coaching_systems.py
```

### Business Operations and Revenue Elasticity

Models ticket pricing curves, attendance metrics matching franchise win/loss momentum, arena facility upgrades, and stadium infrastructure capacity sheets.

Proposed module:

```text
business_operations.py
```

### Public Relations and Fan Volatility Intercept Engine

Tracks a running Fan Volatility Index.

```text
FVI = Fan Volatility Index
```

Trading a fan-favorite asset or making controversial roster splits triggers branching media press conference dialogue loops, impacting executive job security indicators.

Proposed module:

```text
public_relations_engine.py
```

# Suggested Development Order

## Phase 1 — Foundation Stabilization

1. Split `src/nhl_gm_core.py` into modules.
2. Add a shared database access layer.
3. Add test fixtures for rosters, teams, and calendar state.
4. Add a reset/dev seed command.

## Phase 2 — League Simulation Loop

1. Build the out-of-town orchestrator.
2. Add standings tables.
3. Add schedule generation.
4. Run daily user-team + AI-team result persistence.

## Phase 3 — Roster Lifecycle

1. Add injuries and LTIR.
2. Add waivers and AHL reassignment.
3. Add player progression/regression.
4. Add retirements and contract exits.

## Phase 4 — Offseason System

1. Add draft lottery.
2. Add draft class generation.
3. Add free agency auction logic.
4. Add contract negotiation and player-interest scoring.

## Phase 5 — Franchise Depth

1. Add coaching systems.
2. Add fan volatility and media pressure.
3. Add business operations.
4. Add ownership mandates and job-security consequences.
