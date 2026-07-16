# Controlled Cycle 14 — Roster Decision Clarity

Status: `UI Review Pending — Stage 3 direction approved; Stage 4 final acceptance pending`

## NHL Operations — season-versioned roster-lock requirement

A roster source promoted into a new save must persist its `ruleset_id`, `season_id`, source snapshot identifier, and promotion timestamp. The game must reject an in-place roster-pack replacement when any of those identifiers differ from the save's locked values. A later official roster correction must be imported as a new immutable snapshot and offered only through an explicit, reversible migration flow.

**Testable acceptance criteria**

- new saves store all four identifiers;
- a mismatched snapshot cannot silently overwrite the save;
- historical saves continue using the ruleset active when they were created;
- an attempted mismatch returns a user-readable reason and a migration path rather than a generic failure.

This requirement protects CBA-era behavior and roster provenance as league rules and official data evolve.

## Competing Games — clean-room decision receipt

Hockey-management games commonly confirm career-world settings before a save begins. The differentiated clean-room requirement is a compact **decision receipt** shown after roster-source selection and before save creation.

The receipt contains only:

1. selected data source and season;
2. generated or unknown data disclosures;
3. ruleset/save-compatibility status;
4. one primary action and one reversible back action.

Detailed provenance remains in a drawer on desktop and a bottom sheet on mobile. The receipt is generated from the normalized roster-readiness model, uses original wording and presentation, and copies no proprietary assets, layouts, databases, or implementation details.

## Coding — blocked-state live announcement

`RosterSourceCard` now marks its blocker panel as a polite live region in addition to its existing alert role. This makes a newly surfaced blocker reason discoverable to supported screen readers without changing the approved visual direction.

## Testing — focused accessibility contract

The roster-source contract suite now asserts that blocked reasons retain both `accessibilityRole="alert"` and `accessibilityLiveRegion="polite"`. The test is deliberately narrow and guards the exact accessibility behavior introduced this cycle.

## UI/UX Design — blocker hierarchy review

The blocked state keeps one coherent hierarchy:

- badge: `Unavailable`;
- concise blocker panel with a non-color `BLOCKED` label;
- explanatory reason;
- disabled footer with no arrow or false navigation affordance.

The live-region addition is nonvisual and does not alter spacing, typography, color, density, team identity, or responsive layout. The next visual deliverable remains the Stage 4 fixed-viewport desktop/mobile evidence package with realistic team identity, one dense state, and one non-ideal blocked state.
