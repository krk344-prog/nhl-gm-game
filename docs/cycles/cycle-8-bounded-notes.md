# Controlled Development Cycle 8 — Bounded Notes

Status: UI Review Pending. This file records one bounded deliverable per specialist and does not authorize merge or broad implementation.

## NHL Operations — season-bound schedule integrity

Requirement: a new save must derive `regular_season_games_per_team` from its selected, versioned season ruleset. The 2025–26 ruleset must remain at 82; the 2026–27 ruleset must require 84. Save creation must fail closed when the roster snapshot season and ruleset season do not match.

Acceptance cases:
1. `2025-2026` roster snapshot + `2025-2026` rules => 82 games per team.
2. `2026-2027` roster snapshot + `2026-2027` rules => 84 games per team.
3. Mixed-season snapshot/rules => blocking validation error before schedule generation.

Source basis: the NHL and NHLPA ratified a new CBA effective for 2026–27 that expands the regular season to 84 games.

## Competing Games — clean-room decision preview

Observed category pattern: deep management simulations reduce setup anxiety when a choice previews its downstream consequences before commitment.

Original requirement: every roster-source option exposes one primary recommendation and at most three visible management consequences. Detailed provenance, missing fields, and exceptions move into a desktop drawer or mobile bottom sheet. The implementation must not reuse proprietary text, layouts, data, or assets.

Differentiation: consequences are framed around training-grade GM decisions—cap confidence, roster eligibility confidence, scouting uncertainty, and save compatibility—rather than technical importer metadata.

## Coding — premium interaction-state contract

Bounded engineering task: define the required interaction behavior for premium selection cards without changing production UI.

- Resting: charcoal elevated surface with restrained franchise accent.
- Hover-capable devices: elevation and border emphasis may increase, but content must not shift position.
- Keyboard focus: clearly visible 2 px minimum focus treatment with at least 3:1 contrast against adjacent surfaces.
- Selected: persistent check/icon plus text label; color alone is insufficient.
- Disabled/blocked: preserve readable contrast, explain the blocker, and prevent activation.
- Motion: 120–180 ms for hover/focus transitions; honor `prefers-reduced-motion` by removing nonessential animation.
- Touch: minimum 44 x 44 px target and no hover-dependent information.

This contract is reversible documentation on the existing draft PR branch.

## Testing — focused acceptance review

Validation checklist for the interaction-state contract:

- [x] keyboard focus is explicitly defined;
- [x] selected and blocked states use non-color indicators;
- [x] touch minimum is 44 x 44 px;
- [x] reduced-motion behavior is specified;
- [x] no state may cause layout shift;
- [x] blocked choices explain why activation is unavailable;
- [x] mobile does not depend on hover.

Result: specification-level pass. Runtime and visual regression validation remain pending until Stage 2 approval and implementation.

## UI/UX Design — premium depth without decoration overload

Design improvement: use a three-layer visual hierarchy—true-black canvas, charcoal workspace panels, and selectively elevated decision cards. Add subtle radial lighting only near the controlled-franchise header and selected action area. Franchise color is limited to approximately 10–15% of the visible surface and should accent key borders, progress, focus, and selected states rather than fill entire panels.

Typography hierarchy:
- page title and franchise identity;
- section labels and decision headlines;
- concise supporting copy;
- low-emphasis metadata.

Premium acceptance criteria:
- no more than one dominant visual focal point per region;
- repeated card geometry and spacing tokens;
- restrained shadows and gradients that remain legible at high contrast;
- original fictional crest plus one opponent/league-context mark;
- dense and blocked states remain as polished as the ideal state;
- desktop and mobile use intentional composition rather than scaled copies.

## Coordination boundary

No production behavior changed, no PR was merged, and no new broad feature branch was opened. The next UI deliverable remains a Stage 2 polished desktop/mobile roster-source mockup after Kyle approves the current Stage 1 direction.