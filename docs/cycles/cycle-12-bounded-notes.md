# Development Cycle 12 — Bounded Specialist Notes

## NHL Operations — roster-source activation provenance gate

A roster source may be displayed for comparison before every hockey-operations field is complete, but it must not be activated for new-game seeding until the following evidence is bound to the same season identifier:

- NHL and affiliate organization assignments;
- player identity and position provenance;
- roster snapshot effective date;
- ruleset identifier;
- explicit status for contracts, cap charges, waiver eligibility, reserve-list rights, injury status, and emergency-goaltender staffing.

Fields that are absent from an identity-only source must remain `unknown`; they must not be inferred from age, league assignment, salary estimates, ratings, or previous snapshots.

### Testable requirement

Given a roster pack with verified player identity but no reviewed contract or waiver source, the preflight may report `identity_ready = true`, but must report `activation_ready = false`, identify each unknown operational domain, and prevent the primary Continue action from creating a save.

## Competing Games — clean-room consequence-first card

Management simulations commonly help users choose between complex setup options by summarizing consequences before exposing configuration detail. The original NHL GM implementation differentiates itself by presenting each roster source as an operational readiness decision rather than a technical database choice.

### Product requirement

Each roster-source card must show, in a consistent order:

1. source identity and recommendation state;
2. one plain-language summary;
3. no more than three immediate management consequences;
4. one persistent availability, selected, recommended, or blocked label;
5. one primary action.

Detailed provenance, field coverage, and exceptions remain available through a desktop drawer or mobile bottom sheet. No proprietary text, assets, code, data, or branded layout is used.

## Coding — reusable `RosterSourceCard` vertical slice

Added `mobile/components/RosterSourceCard.js` as the first reversible Stage 3 component slice.

The component includes:

- approved charcoal, black, and restrained-gold treatment;
- selected, recommended, available, and blocked states;
- persistent text labels rather than color-only state;
- a maximum of three visible consequences;
- an explicit blocker explanation;
- screen-reader button semantics and state;
- visible focus treatment;
- a 44-pixel minimum primary action row.

The component is intentionally not wired into save creation or the full setup screen. This keeps the implementation reviewable and prevents an unapproved broad UI change.

## Testing — static component-contract validation

Added `tests/test_roster_source_card_contract.py`.

The focused test verifies the approved surface colors and radius, bounded decision density, non-color selected and blocked states, alert semantics, keyboard focus treatment, minimum touch target, and mandatory blocker explanation.

Runtime rendering, fixed-viewport screenshots, device accessibility, and visual-regression baselines remain Stage 3 tasks after the component is integrated into a review harness.

## UI/UX Design — card hierarchy and difficult-state review

The implemented slice preserves the approved mockup's detail without giving every data field equal weight:

- title and recommendation state lead the scan;
- the summary explains the choice;
- three consequences support comparison;
- blocker detail appears only when needed;
- the action remains anchored at the bottom for consistent card comparison.

The blocked state is deliberately polished rather than visually disabled into illegibility. It retains full explanation, a visible status label, and a clear next action while preventing selection.

### Visual acceptance criteria

- four cards can share one desktop comparison row at the final screen level without internal horizontal scrolling;
- mobile cards stack at full width with no page-level horizontal scrolling;
- card height may grow for blocker text but the action remains logically last;
- focus, selected, recommended, and blocked states remain distinguishable without color;
- gold remains limited to recommendation, franchise identity, progress, focus, and primary actions;
- no hover or press state causes layout movement;
- actual Stage 3 screenshots must include at least one blocked roster source.

## Approval status

- Approved Stage 2 visual target: preserved.
- First coded component slice: complete but not integrated.
- Full roster-selector implementation: `UI Review Pending`.
- Merge authorization: not granted.
