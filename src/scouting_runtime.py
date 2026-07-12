"""Low-cost daily gate for scouting report processing."""

import sqlite3
from contextlib import closing

try:
    from .nhl_gm_core import connect_database
    from .scouting_service import process_scouting_day
except ImportError:  # pragma: no cover
    from nhl_gm_core import connect_database
    from scouting_service import process_scouting_day


def process_scouting_if_due(day):
    """Avoid scanning or reseeding scouting state on empty calendar days."""
    with closing(connect_database()) as conn:
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'scouting_assignments'"
        ).fetchone()
        if table is None:
            return {"completed_report_ids": [], "completed_count": 0}
        due = conn.execute(
            "SELECT 1 FROM scouting_assignments WHERE status = 'active' AND due_day <= ? LIMIT 1",
            (day,),
        ).fetchone()
    if due is None:
        return {"completed_report_ids": [], "completed_count": 0}
    return process_scouting_day(day)
