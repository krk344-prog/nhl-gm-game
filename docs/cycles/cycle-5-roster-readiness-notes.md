# Controlled Cycle — Roster Readiness Notes

## NHL Operations — waiver-state provenance requirement

A roster snapshot may establish a player's starting NHL or AHL organizational assignment, but it must not establish live waiver clearance. Waiver state is transaction state, not roster-source identity.

**Testable requirement:** every promoted player record must begin with `waiver_status = unknown` unless a separately versioned transaction ledger supplies an effective date, ruleset identifier and auditable source. Any post-creation NHL-to-AHL assignment must call the season-aware transaction service; the roster importer cannot infer or persist `cleared` from an AHL assignment alone.

**Edge case:** a player listed on an AHL opening roster may have cleared waivers before the snapshot date, may be waiver-exempt, or may have been assigned under another exception. Because the roster pack does not encode that transaction history, promotion must not choose among those states.

Rules basis: NHL/NHLPA CBA Article 13 governs waivers. The implementation remains season-versioned and auditable rather than hard-coding an assumed exemption.

## Competing Games — clean-room career-start consequence preview

A useful management-simulation pattern is to let the user configure the starting world before committing to a career. The original product requirement is a **consequence preview** attached to each roster source rather than a settings list.

Each source card must summarize four consequences:

1. identity authenticity;
2. simulation substitutions;
3. organizational completeness;
4. save compatibility.

Selecting a card updates one persistent creation summary. Detailed provenance remains in progressive disclosure. This differs from a generic database picker by explaining what the choice changes in the GM experience and by treating the fictional world as a complete supported mode.

Implementation notes:

- expose a normalized `consequences` view model rather than binding presentation directly to importer fields;
- keep blocker severity separate from descriptive consequences;
- preserve the selected card while a desktop drawer or mobile sheet is open;
- do not use proprietary layouts, wording, assets, databases or implementation details.

## UI/UX Design — roster-source card anatomy

This cycle defines one reusable `RosterSourceCard` design contract without advancing beyond Stage 1 approval.

### Required anatomy

- **Identity row:** source name, season and non-color readiness label;
- **Coverage row:** NHL and AHL club counts presented as paired compact metrics;
- **Disclosure row:** short “Real identity / Generated ratings / Contract status” summary;
- **Consequence row:** up to three concise effects on the new game;
- **Action row:** Select plus a secondary View details control;
- **Selected state:** restrained franchise-color border, check icon and explicit `Selected` text.

### Density and responsive behavior

- desktop cards align comparable fields by row so users can scan horizontally;
- mobile cards become self-contained vertical summaries and never require side-by-side comparison;
- blocker text is limited to the highest-priority reason with an additional-count disclosure;
- full blocker and provenance lists open in the existing drawer/sheet pattern;
- compact marks use original fictional crests or stable fallback initials.

### Accessibility acceptance criteria

- the entire card is not one oversized interactive target; Select and View details remain distinct controls;
- focus indicators are visible against neutral and team-accent borders;
- readiness, selection and blocker states never rely on color alone;
- card headings and consequence labels retain semantic structure for screen readers;
- controls meet a 44-by-44 CSS-pixel minimum touch target;
- at 320 CSS pixels, all primary content remains readable without horizontal scrolling.

**Approval status:** `Stage 1 — UI Review Pending`. This specification is reversible preparation and does not authorize production implementation.
