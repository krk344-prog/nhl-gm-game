# Controlled Cycle 11 — Approved Visual Contract

Status: `Stage 2 Approved; Stage 3 UI Review Pending`

## NHL Operations — season-bound schedule preflight

Beginning with the 2026–27 ruleset, the roster-pack preflight must verify that the save configuration is bound to an 84-game regular season and four-game preseason before save creation. A 2025–26 roster/rules configuration remains bound to its historical 82-game regular-season behavior. A mixed roster season, ruleset season, or schedule template must block save creation rather than silently translating the data.

**Testable requirement:** the preflight returns `ready = false` and a corrective action whenever `roster_season_id`, `ruleset_season_id`, and `schedule_template_season_id` do not match. For 2026–27, the selected schedule template must declare 84 regular-season games and four preseason games per club.

Rules basis: the ratified NHL/NHLPA agreement takes effect for 2026–27 and expands the regular season to 84 games while reducing the preseason to four games.

Sources:
- https://www.nhl.com/news/nhl-nhlpa-ratify-four-year-collective-bargaining-agreement
- https://www.nhl.com/news/nhl-nhlpa-agree-on-4-year-extension-to-cba

## Competing Games — clean-room guided setup with persistent preview

Management simulations commonly divide career creation into sequential decisions and preserve a summary of the selected world before commitment. The original product requirement is a **guided setup rail with a persistent consequence preview**.

- Desktop keeps setup progress visible in a left rail while the current decision occupies the primary workspace.
- Mobile replaces the rail with compact progress and bottom navigation rather than shrinking the desktop layout.
- The franchise summary persists while roster sources are compared, so users understand which organization and league context the choice will affect.
- Each roster source uses the same comparison order and exposes one primary action.
- Detailed provenance and exceptions remain in a drawer or bottom sheet.

This is an original clean-room requirement. No proprietary assets, source code, databases, wording, or pixel-identical layout are reused.

## Coding — approved roster-selector visual contract

Updated `docs/ui/premium-surface-tokens-v1.json` from a generic premium token set to an enforceable Stage 2 visual contract for **New Game — Roster Pack Selection**.

The contract now requires:

- arena atmosphere behind a strong black scrim;
- restrained gold franchise/progress accents;
- four visible desktop roster options without horizontal scrolling;
- desktop setup rail, franchise summary, information panel, and estimated setup time;
- stacked mobile cards, compact franchise summary, and bottom navigation;
- fixed-viewport comparison, side-by-side mockup review, deviation logging, and a visual-regression baseline before final acceptance.

No production UI was implemented or merged.

## Testing — mockup-drift regression contract

Added one focused automated test, `test_approved_roster_selector_contract_prevents_mockup_drift`, that fails when future implementation preparation removes the approved screen structure or review controls.

The test verifies:

- exactly four roster options;
- desktop setup rail and supporting detail panels;
- mobile stacked cards and bottom navigation;
- no horizontal page scrolling on mobile;
- fixed viewport and side-by-side mockup comparison;
- deviation logging and visual-regression requirements;
- explicit Kyle approval before a major UI merge.

## UI/UX Design — Stage 2 approval normalization

Kyle approved the alternate premium concept and specifically requested that the actual UI retain its detail. The concept is now the visual target rather than optional inspiration.

### Visual acceptance criteria

- Preserve the arena-backed, black-and-charcoal atmosphere and restrained gold accent system.
- Preserve the desktop setup rail and mobile bottom navigation.
- Show four differentiated roster-source cards, including recommended and non-ideal/blocked states.
- Preserve franchise identity, crest treatment, record, rank, streak, arena, captain, top scorer, information panel, and estimated setup time when supported by the selected franchise.
- Maintain aligned metrics and equal comparison order across roster-source cards.
- Meet minimum touch, type, keyboard-focus, reduced-motion, non-color-status, and fallback-mark requirements.
- Stage 3 screenshots must be captured at fixed desktop and mobile viewports and reviewed beside the approved mockup.
- Every deliberate difference must be recorded; unexplained simplification is a defect.

### Approval state

Stage 2 is approved. The next approval request occurs at Stage 3 after actual desktop and mobile screenshots are available.
