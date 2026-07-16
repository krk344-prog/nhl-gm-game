# Controlled Cycle 10 — Premium Atmosphere and Eligibility Notes

Status: `UI Review Pending`

## NHL Operations — traveling emergency-goaltender eligibility contract

Beginning with the 2026–27 ruleset, emergency-goaltender staffing must be represented as a season-versioned eligibility record rather than a free-text staff assignment.

**Testable requirement:** a club may not mark its traveling emergency goaltender as `verified` unless the record contains the candidate identity, verification date, source reference, ruleset ID, prior-three-season professional-play check, career professional-games count, NHL Standard Player Contract appearance check, and current reserve-list/RFA-list check. Any missing or stale check produces `review_required`; an explicitly failed check produces `ineligible`.

**Edge case:** a candidate can hold another non-player club duty, but that employment relationship must not bypass the hockey-experience and player-rights eligibility checks.

Rules basis: the NHL/NHLPA four-year agreement was ratified July 8, 2025, and the traveling emergency-goaltender model begins with the 2026–27 ruleset. The implementation must retain separate 2025–26 behavior for historical saves.

Sources:
- https://www.nhl.com/news/nhl-nhlpa-ratify-four-year-collective-bargaining-agreement
- https://www.reuters.com/sports/nhl-players-association-ratify-four-year-labor-deal-2025-07-08/

## Competing Games — clean-room readiness preflight

Management simulations often let users configure a career world before committing. The original differentiated requirement is a **readiness preflight** that summarizes decision consequences instead of presenting a long settings form.

Before creating a save, the selected roster source must show exactly four readiness groups:

1. identity coverage;
2. rules compatibility;
3. generated or unknown simulation data;
4. blocking actions.

The primary screen shows one recommendation and at most three consequences. Full provenance and exceptions remain in a desktop drawer or mobile bottom sheet. No proprietary layout, wording, database, assets, or implementation details are reused.

Implementation notes:

- derive the preflight from a normalized view model rather than importer-specific fields;
- preserve the selected source while details are open;
- make blocking actions directly actionable;
- keep readiness labels and icons visible without relying on color.

## Coding — restrained premium atmosphere tokens

The reusable premium token contract now permits visual depth without turning the black interface into a decorative or broadcast-style surface.

Added constraints:

- ambient gradient opacity is capped at 18%;
- texture opacity is capped at 4%;
- no more than two glow regions may be visible;
- every glow must anchor franchise identity or a selected action;
- decorative motion is prohibited;
- franchise color may cover no more than 15% of the visible surface.

Files:

- `docs/ui/premium-surface-tokens-v1.json`
- `tests/test_premium_surface_tokens.py`

This remains reversible design-system preparation. It does not authorize production implementation or advance the screen beyond Stage 1.

## Testing — premium-atmosphere contract validation

Added one focused automated test that rejects excessive gradients, texture, glow count, decorative motion, and franchise-color saturation.

Acceptance result at commit time: source-level review passed. GitHub Actions validation is required on the latest branch head before the cycle is considered CI-green.

## UI/UX Design — premium depth without clutter

The roster-source screen should gain depth through restrained atmosphere rather than additional cards or equal-weight decoration.

Design requirement:

- retain the true-black canvas;
- use one subtle ambient gradient behind the controlled-franchise identity and, when selected, one restrained action glow;
- add an optional near-imperceptible material texture only to large empty canvas areas;
- keep comparison cards neutral charcoal so data remains the visual priority;
- use crisp typography, border highlights, spacing, and elevation before adding ornament;
- disable nonessential atmosphere in reduced-motion and high-contrast modes when it harms clarity.

Responsive behavior:

- desktop may use two localized ambient regions;
- mobile uses one identity-anchored region and removes texture when it reduces legibility or rendering performance;
- neither layout may place glow behind body copy, blockers, or small team marks.

Visual acceptance criteria:

- the screen reads as black, not blue;
- depth is visible without obvious gradients or gaming-neon effects;
- franchise identity is recognizable before reading the team name;
- blockers and provenance remain more prominent than decoration;
- selected state remains explicit through text and iconography;
- no decorative element moves or creates layout shift.
