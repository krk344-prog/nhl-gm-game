# Cycle 15 — Team identity component contract

## NHL Operations — roster identity provenance gate

**Requirement:** A selectable real-world roster pack must not imply that club marks, player imagery, contract values, ratings, or scouting text are official merely because factual player identity data came from an official roster endpoint.

**Testable rule:** Each roster pack exposes independent provenance statuses for (1) factual player/team identity, (2) visual assets, (3) contracts, and (4) generated simulation attributes. The new-game flow blocks any pack whose required identity snapshot is unreviewed, and substitutes original/local team marks or accessible initials whenever visual-asset permission is absent.

This preserves the current catalog boundary: factual identity may be ingested while active saves and unlicensed visual assets remain isolated.

## Competing Games — persistent watch-list context

Franchise Hockey Manager's documented scouting workflow prioritizes players on a watch list and allows scouting knowledge to decay when players are not revisited. The useful pattern is persistent decision context rather than the proprietary presentation.

**Original requirement:** Team and player marks in scouting, trade, and roster rows may open a compact contextual drawer containing the user's latest report date, confidence trend, watch status, and one next action. The drawer must not expose hidden ratings and must remain one interaction away from the dense list.

**Differentiation:** The game connects visual recognition to accountable front-office action: every contextual drawer identifies which staff report informed the view and whether the information is stale.

## Coding — reusable `TeamMark`

Added `mobile/components/TeamMark.js` as a reversible presentation-layer primitive:

- accepts approved/local artwork only;
- degrades to two- or three-letter initials;
- provides an accessible image label;
- supports compact and restrained hero treatments;
- bounds rendered size from 24–72 px;
- confines franchise color to the mark surface instead of saturating the screen.

No NHL or third-party logo assets were imported.

## Testing — component contract

Added `tests/test_team_mark_contract.py` to validate:

- missing-artwork fallback;
- screen-reader semantics;
- small-size legibility and bounded sizing;
- restrained team-color use;
- absence of embedded remote or third-party assets.

## UI/UX — identity rhythm specification

Use `TeamMark` at three hierarchy levels:

1. **Hero (48–72 px):** controlled franchise in the command-center or workspace header, once per screen.
2. **Context (32–40 px):** next opponent, trade counterpart, or selected prospect comparison.
3. **Dense row (24–28 px):** standings, schedule, league news, scouting lists, and transaction history.

Acceptance criteria:

- no more than one hero mark in the initial viewport;
- repeated rows use compact marks and fallback initials;
- home/away distinction uses text plus restrained border treatment, never color alone;
- all marks retain contrast in dark and light contexts;
- team color accents remain subordinate to status and action hierarchy;
- missing assets never produce broken-image placeholders;
- mobile preserves a minimum 44 px interactive target around any tappable mark.

## Approval state

This cycle adds a reusable component contract, not a major screen redesign. Stage 2 roster-selector direction remains approved. Stage 3 remains `UI Review Pending` until the component is integrated into the running setup flow and desktop/mobile screenshots are captured with realistic dense and missing-logo states.
