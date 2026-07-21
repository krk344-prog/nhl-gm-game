# Versioned NHL Rules Registry

## Purpose

The simulation must reproduce the legal environment of the selected season rather than rely on permanent constants. The registry makes rule changes explicit, reviewable, testable and source-backed.

## Design guarantees

- Every ruleset is immutable and identified by season.
- Every ruleset has effective dates and a lifecycle status.
- Official, projected and deprecated rules cannot be confused.
- Material rules retain source provenance and verification status.
- The engine refuses to invent an accrual-day denominator.
- Future CBA changes require a new configuration file rather than code edits throughout the application.

## Directory layout

```text
config/rules/
  2025-26.json
  2026-27.json
src/
  rules_registry.py
tests/
  test_rules_registry.py
```

## Ruleset statuses

| Status | Gameplay use |
|---|---|
| `official` | Allowed |
| `official_with_pending_operational_details` | Allowed, but individual rules may require stronger provenance |
| `projected` | Blocked unless the caller explicitly opts into scenario planning |
| `deprecated` | Blocked |

## Evidence model

Each source declares:

- authority level;
- verification status;
- source title and URL;
- exact dotted rule paths it supports.

The strict `require_verified()` gate accepts only rules marked `verified` or `inherited`. A public summary can seed a future feature, but it cannot silently authorize a legally sensitive transaction engine.

## Integration pattern

```python
from datetime import date
from src.rules_registry import RulesRegistry

registry = RulesRegistry()
rules = registry.for_date(date.today())

cap_ceiling = rules.salary_system["upper_limit"]
roster_max = rules.salary_system["active_roster_maximum"]
```

Daily cap calculations must use the actual official schedule span:

```python
daily_charge = rules.daily_cap_charge(
    annual_cap_hit=8_000_000,
    accrual_days=official_schedule.accrual_days,
)
```

This intentionally replaces the former `AAV / 186` assumption. The denominator is a property of the league calendar, not a universal CBA constant.

## Migration plan

1. Add `season_id` to league and save-game records.
2. Load the corresponding `SeasonRules` during game initialization.
3. Replace hard-coded cap, roster and contract constants with registry lookups.
4. Derive accrual days from the generated official schedule and persist the derived value.
5. Require verified provenance at Central Registry transaction submission.
6. Add rule migrations only when loading an older save into a newer simulation version; never mutate the historical ruleset itself.

## Initial supported seasons

### 2025-26

- 82-game regular season.
- $95.5 million upper limit.
- $70.6 million lower limit.
- Legacy maximum contract terms of eight years for a re-signing and seven years with a new club.

### 2026-27

- 84-game regular season.
- $104 million upper limit.
- $76.9 million lower limit.
- $850,000 minimum NHL salary.
- Maximum terms of seven years for a re-signing and six years with a new club.
- Playoff-cap and paper-transaction changes represented, but held below strict verification until full operational language is mapped.

## Next engineering integration

The next commit should update database initialization to persist `season_id`, load the registry before creating league state, and replace the current hard-coded cap ceiling and fixed 186-day assumption. A data migration must preserve existing prototype saves by assigning them an explicit legacy ruleset rather than silently changing their economics.
