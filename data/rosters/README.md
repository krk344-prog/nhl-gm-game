# Real NHL/AHL roster packs

This directory defines the versioned roster-data boundary for the simulation.

## What is safe to import

The roster pack may contain factual identity fields such as player name, team assignment, position, birth date, sweater number, and shooting/catching side. It must not include copied logos, headshots, scouting text, proprietary ratings, contract databases, or other licensed assets unless a separate license has been verified.

The game generates deterministic placeholder ratings and a minimum-salary placeholder only so imported players can be represented by the current simulation schema. Those values are labeled as generated and must not be presented as official evaluations or contract data.

## NHL roster source

`src.roster_import` can build an NHL snapshot from the NHL public roster endpoint:

```bash
python -m src.roster_import \
  --nhl-season 20252026 \
  --output data/rosters/nhl-2025-26.json
```

The generated snapshot must be reviewed and committed as an immutable season snapshot before it is used by a save.

## AHL roster source

The AHL portion uses the same normalized JSON contract, but no undocumented or unstable feed is hard-coded. Import an approved snapshot from official club/league roster materials:

```json
{
  "schema_version": 1,
  "season_id": "2025-2026",
  "created_at": "2026-07-13T00:00:00+00:00",
  "sources": [{"league": "AHL", "name": "Approved official roster snapshot"}],
  "teams": [
    {
      "league": "AHL",
      "abbreviation": "ROC",
      "players": [
        {
          "source_player_id": "source-stable-id",
          "name": "Player Name",
          "position": "C",
          "birth_date": "2002-01-01",
          "jersey_number": 19,
          "shoots_catches": "L",
          "roster_status": "active"
        }
      ]
    }
  ]
}
```

Merge approved NHL and AHL snapshots:

```bash
python -m src.roster_import \
  --nhl-season 20252026 \
  --ahl-snapshot data/rosters/ahl-2025-26.json \
  --output data/rosters/nhl-ahl-2025-26.json
```

Validate a pack:

```bash
python -m src.roster_import --validate data/rosters/nhl-ahl-2025-26.json
```

## Save integrity

This first slice stores imported players in a roster catalog and deliberately does **not** overwrite an active simulation save. Promotion of a reviewed snapshot into new-game seeding requires a separate guarded migration with save-versioning and contract/ratings disclosure.
