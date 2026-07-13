"""Versioned NHL/AHL roster-pack import utilities.

The importer keeps external identity data separate from simulation ratings. Real
names, positions, sweater numbers, and team assignments come from a versioned
snapshot. Ratings and contract values remain explicitly generated/unknown until
a licensed data source is approved.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import sqlite3
import urllib.request
from pathlib import Path
from typing import Any, Iterable

NHL_API_BASE = "https://api-web.nhle.com/v1"
SNAPSHOT_SCHEMA_VERSION = 1
NHL_TEAM_ABBREVIATIONS = (
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD",
    "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS",
    "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WSH", "WPG",
)


def _localized(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("default") or value.get("en") or next(iter(value.values()), ""))
    return str(value or "")


def normalize_position(code: str) -> str:
    code = (code or "").upper()
    if code == "G":
        return "G"
    if code in {"D", "LD", "RD"}:
        return "D"
    return "F"


def player_age(birth_date: str | None, as_of: str | None = None) -> int:
    if not birth_date:
        return 24
    born = dt.date.fromisoformat(birth_date)
    date = dt.date.fromisoformat(as_of) if as_of else dt.date.today()
    return date.year - born.year - ((date.month, date.day) < (born.month, born.day))


def deterministic_simulation_profile(player: dict[str, Any], season_id: str) -> dict[str, Any]:
    """Generate stable placeholder ratings without presenting them as real data."""
    identity = f"{season_id}|{player.get('source_player_id')}|{player['name']}|{player['position']}"
    seed = int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    position = normalize_position(player["position"])
    age = player_age(player.get("birth_date"))

    if position == "G":
        archetype = rng.choice(["Butterfly Goalie", "Hybrid Goalie"])
        ratings = {
            "shooting": rng.randint(30, 42),
            "passing": rng.randint(48, 70),
            "positioning": rng.randint(68, 88),
            "reflexes": rng.randint(68, 89),
            "speed": rng.randint(58, 78),
            "checking": rng.randint(30, 38),
        }
    elif position == "D":
        archetype = rng.choice(["Offensive D-Man", "Defensive D-Man", "Two-Way Defenseman"])
        ratings = {
            "shooting": rng.randint(55, 79),
            "passing": rng.randint(63, 85),
            "positioning": rng.randint(66, 87),
            "reflexes": rng.randint(30, 46),
            "speed": rng.randint(63, 84),
            "checking": rng.randint(65, 89),
        }
    else:
        archetype = rng.choice(["Elite Playmaker", "Volume Sniper", "Two-Way Forward"])
        ratings = {
            "shooting": rng.randint(63, 88),
            "passing": rng.randint(63, 89),
            "positioning": rng.randint(62, 85),
            "reflexes": rng.randint(30, 46),
            "speed": rng.randint(67, 90),
            "checking": rng.randint(52, 82),
        }

    return {
        **ratings,
        "age": max(18, min(44, age)),
        "position": position,
        "archetype": archetype,
        "aav": 775000.0,
        "contract_years": 1,
        "ratings_source": "deterministic_placeholder",
        "contract_data_status": "unknown_placeholder",
    }


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "nhl-gm-game-roster-import/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_nhl_team_roster(
    abbreviation: str,
    payload: dict[str, Any],
    season_code: str,
) -> dict[str, Any]:
    players: list[dict[str, Any]] = []
    for bucket in ("forwards", "defensemen", "goalies"):
        for raw in payload.get(bucket, []):
            first = _localized(raw.get("firstName"))
            last = _localized(raw.get("lastName"))
            name = " ".join(part for part in (first, last) if part).strip()
            players.append(
                {
                    "source_player_id": str(raw.get("id") or name),
                    "name": name,
                    "position": str(raw.get("positionCode") or "F"),
                    "birth_date": raw.get("birthDate"),
                    "jersey_number": raw.get("sweaterNumber"),
                    "shoots_catches": raw.get("shootsCatches"),
                    "roster_status": "active",
                }
            )
    return {
        "league": "NHL",
        "abbreviation": abbreviation,
        "season_code": season_code,
        "source_url": f"{NHL_API_BASE}/roster/{abbreviation}/{season_code}",
        "players": players,
    }


def fetch_nhl_snapshot(
    season_code: str,
    team_abbreviations: Iterable[str] = NHL_TEAM_ABBREVIATIONS,
) -> dict[str, Any]:
    teams = []
    for abbreviation in team_abbreviations:
        url = f"{NHL_API_BASE}/roster/{abbreviation}/{season_code}"
        teams.append(normalize_nhl_team_roster(abbreviation, fetch_json(url), season_code))
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "season_id": f"{season_code[:4]}-{season_code[4:]}",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": [
            {
                "league": "NHL",
                "name": "NHL public roster endpoint",
                "base_url": NHL_API_BASE,
            }
        ],
        "teams": teams,
    }


def merge_snapshots(*snapshots: dict[str, Any]) -> dict[str, Any]:
    snapshots = tuple(snapshots)
    if not snapshots:
        raise ValueError("At least one roster snapshot is required.")
    season_ids = {item.get("season_id") for item in snapshots}
    if len(season_ids) != 1:
        raise ValueError("Roster snapshots must use the same season_id.")
    merged = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "season_id": snapshots[0]["season_id"],
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": [],
        "teams": [],
    }
    for snapshot in snapshots:
        validate_snapshot(snapshot)
        merged["sources"].extend(snapshot.get("sources", []))
        merged["teams"].extend(snapshot["teams"])
    validate_snapshot(merged)
    return merged


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("Unsupported roster snapshot schema_version.")
    if not snapshot.get("season_id"):
        raise ValueError("Roster snapshot requires season_id.")
    teams = snapshot.get("teams")
    if not isinstance(teams, list) or not teams:
        raise ValueError("Roster snapshot requires at least one team.")

    team_keys: set[tuple[str, str]] = set()
    for team in teams:
        league = str(team.get("league") or "").upper()
        abbreviation = str(team.get("abbreviation") or "").upper()
        if league not in {"NHL", "AHL"}:
            raise ValueError(f"Unsupported league: {league or '<missing>'}")
        if not abbreviation:
            raise ValueError("Every team requires an abbreviation.")
        key = (league, abbreviation)
        if key in team_keys:
            raise ValueError(f"Duplicate team in snapshot: {league} {abbreviation}")
        team_keys.add(key)

        player_keys: set[str] = set()
        for player in team.get("players", []):
            name = str(player.get("name") or "").strip()
            if not name:
                raise ValueError(f"{league} {abbreviation} contains a player without a name.")
            source_id = str(player.get("source_player_id") or name)
            if source_id in player_keys:
                raise ValueError(f"Duplicate player {source_id} on {league} {abbreviation}.")
            player_keys.add(source_id)
            if normalize_position(str(player.get("position") or "F")) not in {"F", "D", "G"}:
                raise ValueError(f"Invalid position for {name}.")


def snapshot_checksum(snapshot: dict[str, Any]) -> str:
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def ensure_import_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS roster_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season_id TEXT NOT NULL,
            checksum TEXT NOT NULL UNIQUE,
            source_summary TEXT NOT NULL,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS roster_import_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            source_league TEXT NOT NULL,
            source_team_abbreviation TEXT NOT NULL,
            source_player_id TEXT NOT NULL,
            name TEXT NOT NULL,
            detailed_position TEXT,
            normalized_position TEXT NOT NULL,
            birth_date TEXT,
            jersey_number INTEGER,
            shoots_catches TEXT,
            roster_status TEXT NOT NULL,
            raw_json TEXT NOT NULL,
            UNIQUE(snapshot_id, source_league, source_team_abbreviation, source_player_id),
            FOREIGN KEY(snapshot_id) REFERENCES roster_snapshots(id)
        )
        """
    )


def import_snapshot_catalog(conn: sqlite3.Connection, snapshot: dict[str, Any]) -> dict[str, int]:
    """Store a validated snapshot without modifying the active simulation save."""
    validate_snapshot(snapshot)
    ensure_import_schema(conn)
    checksum = snapshot_checksum(snapshot)
    existing = conn.execute(
        "SELECT id FROM roster_snapshots WHERE checksum = ?", (checksum,)
    ).fetchone()
    if existing:
        return {"snapshot_id": int(existing[0]), "players_imported": 0, "duplicate": 1}

    source_summary = json.dumps(snapshot.get("sources", []), sort_keys=True)
    cursor = conn.execute(
        "INSERT INTO roster_snapshots (season_id, checksum, source_summary) VALUES (?, ?, ?)",
        (snapshot["season_id"], checksum, source_summary),
    )
    snapshot_id = int(cursor.lastrowid)
    player_count = 0
    for team in snapshot["teams"]:
        for player in team.get("players", []):
            conn.execute(
                """
                INSERT INTO roster_import_players (
                    snapshot_id, source_league, source_team_abbreviation,
                    source_player_id, name, detailed_position, normalized_position,
                    birth_date, jersey_number, shoots_catches, roster_status, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    team["league"].upper(),
                    team["abbreviation"].upper(),
                    str(player.get("source_player_id") or player["name"]),
                    player["name"],
                    player.get("position"),
                    normalize_position(player.get("position") or "F"),
                    player.get("birth_date"),
                    player.get("jersey_number"),
                    player.get("shoots_catches"),
                    player.get("roster_status") or "active",
                    json.dumps(player, sort_keys=True),
                ),
            )
            player_count += 1
    conn.commit()
    return {"snapshot_id": snapshot_id, "players_imported": player_count, "duplicate": 0}


def load_snapshot(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        snapshot = json.load(handle)
    validate_snapshot(snapshot)
    return snapshot


def write_snapshot(snapshot: dict[str, Any], path: str | Path) -> None:
    validate_snapshot(snapshot)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and validate versioned NHL/AHL roster packs.")
    parser.add_argument("--nhl-season", help="NHL season code, for example 20252026.")
    parser.add_argument("--ahl-snapshot", help="Approved normalized AHL JSON snapshot to merge.")
    parser.add_argument("--validate", help="Validate an existing normalized snapshot.")
    parser.add_argument("--output", help="Output path for the merged roster pack.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.validate:
        snapshot = load_snapshot(args.validate)
        print(f"Valid roster snapshot: {len(snapshot['teams'])} teams")
        return 0

    snapshots = []
    if args.nhl_season:
        snapshots.append(fetch_nhl_snapshot(args.nhl_season))
    if args.ahl_snapshot:
        snapshots.append(load_snapshot(args.ahl_snapshot))
    if not snapshots or not args.output:
        raise SystemExit("Provide a source and --output, or use --validate.")
    snapshot = merge_snapshots(*snapshots) if len(snapshots) > 1 else snapshots[0]
    write_snapshot(snapshot, args.output)
    print(f"Wrote {len(snapshot['teams'])} teams to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
