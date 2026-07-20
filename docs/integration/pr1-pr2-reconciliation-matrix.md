# PR #1 / PR #2 Reconciliation Matrix

Status: planning artifact only. No merge, schema rewrite, or runtime behavior is authorized by this document.

## Integration objective

Preserve PR #1 as the playable Alpha foundation while porting PR #2's season-aware rules and provenance controls incrementally. Do not replace PR #1's league loop, API/mobile contracts, deterministic save controls, schedule, standings, or trade history with PR #2's smaller prototype engine.

## Function and responsibility matrix

| Area | PR #1 authority | PR #2 authority | Integration decision | Required validation |
|---|---|---|---|---|
| Database path and connection | `get_database_path`, `connect_database` support CLI/API/tests | `_connect` enables row factory and foreign keys | Keep PR #1 public helpers; add foreign-key enforcement and row factory only where callers tolerate rows | Existing API and engine tests; foreign-key failure test |
| New-game seeding | Eight fictional NHL teams, 23-player rosters, deterministic seed | Two-team prototype seeded under a ruleset | Keep PR #1 seeding unchanged; bind generated save to one selected season ruleset after tables exist | Eight teams, 184 NHL players, deterministic seed, legal cap/roster |
| Save metadata | `game_settings`: controlled team, save name, seed, schema version | `league_calendar`: season ID, rules schema/status, cap limits, accrual days | Retain both responsibilities; never overload Alpha schema version with rules schema version | Restart persistence and season-mismatch tests |
| Schedule and calendar | Generated 328-game schedule, standings, results, current day | Accrual denominator and immutable season binding | Derive accrual days from PR #1's generated schedule; persist season fields through additive migration | Complete-season test; schedule/result preservation fixture |
| Roster compliance | Existing playable roster and trade workflows | Registry-driven cap ceiling and active-roster maximum | Port rule lookup into PR #1's compliance gate without replacing trade/roster services | Count boundary, cap boundary, projected/unverified-rule rejection |
| Daily cap accounting | Existing daily league advancement | Rules-aware denominator and persisted cap context | Use generated schedule denominator; retain PR #1 advancement and result persistence | Day advancement, accrued margin, deadline buying-power tests |
| Game simulation | Structured results, fatigue, standings and season end | Reduced prototype simulator | PR #1 remains authoritative; no simulator port from PR #2 | 328/328 games, deterministic digest, standings reconciliation |
| Trades | `trade_history`, multi-team partners, API/mobile flows | Basic rules-aware core does not replace Alpha trade service | PR #1 remains authoritative; season context may annotate validation later | Approved/rejected/blocked trade and migration preservation |
| API/mobile | Live routes, retries, offline state, roster filters | No equivalent production contract | PR #1 remains authoritative | Existing HTTP tests and Android export |
| Rules registry | No versioned source-of-truth layer | `RulesRegistry`, verified provenance, date/season resolution | Port PR #2 modules and configuration largely unchanged; adapt imports to Alpha package layout | Registry suite and date-gap/overlap tests |
| Research agent | None | Auditable front-office research workflow | Keep isolated from runtime engine; no startup dependency | Existing research-agent suite |

## First incremental compatibility patch

1. Start from PR #1's `src/nhl_gm_core.py`.
2. Add PR #2's rules registry as a separate dependency.
3. Extend `league_calendar` additively with season/rules fields.
4. Populate `accrual_days` from the generated Alpha schedule rather than an environment-only value.
5. Replace only hard-coded cap/roster constants in the existing compliance and cap-accounting paths.
6. Keep all PR #1 services, API routes, simulation functions, tables, and mobile payloads intact.

## Stop conditions

Stop the port and report a blocker if any patch:

- recreates or drops an Alpha table;
- changes existing API/mobile response keys without a versioned contract;
- changes deterministic schedule or simulation output unintentionally;
- loses save metadata, completed games, standings, result logs, or trade history;
- silently opens a save under a different season;
- uses projected or unverified rules without an explicit opt-in.

## Review gate

The first compatibility patch is reviewable only after all existing PR #1 backend tests and PR #2 rules tests pass together, plus one complete-season run and one migration fixture containing save metadata, completed schedule results, standings, and trade history.
