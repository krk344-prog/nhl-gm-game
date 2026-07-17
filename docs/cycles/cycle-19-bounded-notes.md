# Development Cycle 19 — Bounded Notes

## NHL Operations requirement: season-versioned emergency recalls

The roster transaction layer must distinguish a regular recall from an emergency recall and resolve eligibility from the save's governing season rules.

For the current CBA through 2025-26, an emergency recall may be used only when injuries, illness, or suspension leave the club unable to dress the required lineup. The recall record must store the triggering shortage, date, affected position group, governing rule version, and whether the emergency condition still exists. When the emergency ends, the player must be returned or converted through the normal transaction path; the system must not silently retain emergency status.

For 2026-27 and later, the rules registry must permit a revised implementation without changing historical saves. Until the new CBA text is represented in the rules registry, the engine must mark the future-season emergency-recall rule as `verification_required` rather than inheriting the prior rule by assumption.

### Acceptance cases

1. A regular recall and an emergency recall produce different transaction types and audit records.
2. An emergency recall is rejected when the club can still dress a legal lineup.
3. A valid emergency recall records the shortage and governing season rule.
4. The player is flagged for review when the emergency condition ends; no silent permanent conversion occurs.
5. A 2026-27 save cannot use the 2025-26 emergency-recall rule unless the rules registry explicitly maps it.

## Clean-room product pattern: transaction audit ribbon

Management simulations benefit from preserving the reason and consequence of a move, not only the resulting roster. Add a compact transaction audit ribbon to roster and player detail views showing:

- move type;
- effective date;
- governing rule version;
- reason or triggering condition;
- status: active, resolved, reversed, or requires review.

The ribbon should open a detailed audit drawer on desktop and a bottom sheet on mobile. It must use text and icons in addition to color, retain original transaction intent after validation errors, and avoid exposing every compliance field in the default view.

## UI difficult-state capture contract

The next Stage 3 roster-selector package must include fixed desktop and mobile captures for:

- missing team mark with initials fallback;
- unavailable roster pack;
- loading state;
- validation error with preserved selection;
- high-density source list;
- 200% zoom or equivalent narrow-layout stress state.

Each capture must identify the viewport, keyboard/focus behavior, screen-reader announcement expectation, and any deliberate deviation from the approved preview.
