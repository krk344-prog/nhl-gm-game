# Development Cycle 4 — Bounded Outcomes

## NHL Operations — schedule transition provenance

**Requirement:** season setup and migration must treat regular-season length as a versioned league rule. A 2025–26 save remains 82 games; a newly created 2026–27 save requires 84 games. A migrated legacy save must preserve its original denominator and display a legacy-rules notice rather than silently changing the schedule.

**Acceptance criteria**
- `season_id` resolves the expected regular-season length.
- New 2026–27 saves fail validation unless each team is scheduled for 84 games.
- Existing 82-game saves retain their original schedule and accounting denominator.
- The Command Center presents the mismatch as a blocking compliance item with a direct diagnostic action.

**Provenance:** NHL and NHLPA ratified the four-year CBA extension in July 2025; public league reporting states that the 84-game regular season begins in 2026–27.

## Competing Games — recognizable league-world pattern

Deep sports-management products commonly use compact club marks and contextual identity to reduce repeated reading of team names. The clean-room requirement is a reusable `TeamMark` presentation contract rather than a copied layout.

**Original requirement**
- Team marks may render as an original crest, monogram, or fallback initials.
- A mark is paired with the team name on first appearance; repeated compact appearances may use an accessible label.
- Matchups visually distinguish home and away without relying only on color.
- Controlled-team identity is strongest in the header; opponent identity is strongest in schedule, standings, news, and trade context.
- Marks must remain legible at 24, 32, 48, and 96 pixels.

**Differentiation:** branding supports decision recognition and league immersion, but the interface remains a management workstation rather than a broadcast overlay.

## Coding — Stage 2 team-identity revision

Added `docs/ui/main-dashboard-stage2-team-identity-desktop.svg` to the existing UI approval branch. The artifact introduces an original fictional Buffalo Frost crest, opponent marks, team record, streak, arena, captain, leading scorer, starting goalie, injuries, recent form, divisional context, and league activity. No runtime code, dependency, API, simulation, or persisted data changed.

## Testing — static identity and accessibility validation

Validation target: `docs/ui/main-dashboard-stage2-team-identity-desktop.svg`.

Pass criteria:
- parses as SVG/XML;
- includes a responsive `viewBox`;
- exposes a title and description through `aria-labelledby`;
- includes the controlled franchise and at least one opponent or league team context;
- contains a non-color home/away label;
- includes a non-ideal offline state;
- keeps mandatory schedule and roster decisions visible.

Result: pass by source inspection. Runtime focus, zoom, touch, and screen-reader behavior remain Stage 3 responsibilities.

## UI/UX Design — team identity without decorative overload

The revision concentrates branding in three locations: the franchise hero, the next-matchup card, and compact league-context marks. Team colors are limited to accents, selected standings text, and crests. Operational cards retain neutral surfaces so the screen remains readable and professional.

**Visual acceptance criteria**
- The controlled team is identifiable within two seconds without reading the full header.
- No card uses a team color as its only status signal.
- Opponent marks improve scan speed but do not compete with mandatory decisions.
- Identity remains legible at laptop scale and supports initials when assets are unavailable.
- The mobile revision must preserve the same identity hierarchy without placing oversized crests above urgent decisions.

**Approval status:** `UI Review Pending — Stage 2 Team Identity Revision`.
