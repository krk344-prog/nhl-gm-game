# New Game — Roster Pack Selection Direction v1

Status: **Stage 1 — UI Review Pending**

## Bounded cycle objective

Add a decision-safe selection step between franchise selection and game creation. The screen must clearly distinguish reviewed real-identity roster packs from the fictional default and must never imply that generated ratings or unknown contracts are official data.

## NHL Operations — testable promotion requirement

A roster pack may be offered as a complete NHL/AHL new-game seed only when:

1. it is tied to one explicit season identifier;
2. it contains the expected number of NHL and AHL clubs for that ruleset;
3. every promoted club contains at least one player record;
4. source provenance is retained for audit and refresh decisions; and
5. promotion creates a new save rather than rewriting an existing save.

**Acceptance case:** a reviewed catalog with 32 NHL clubs but an empty AHL affiliate remains importable for inspection but is blocked from new-game promotion with a team-specific reason.

This is deliberately separate from active-roster and game-day lineup limits. Imported identity data describes organizational assignment; the simulation rules registry remains authoritative for active roster, injured reserve, waivers, salary-cap and dressed-lineup compliance.

## Competing games — clean-room pattern translation

Sports-management games commonly let users choose roster databases or starting worlds before beginning a career. The useful pattern is **pre-start configuration with visible consequences**. The original requirement for this game is a comparison-first roster-pack selector that shows data provenance, season, completeness, simulation substitutions and save compatibility before the user commits.

### Differentiation

- Present a plain-language “what is real / what is simulated” disclosure.
- Run a readiness check inline and expose blockers without requiring a failed game creation.
- Preserve the fictional league as a first-class, fully supported option rather than treating it as a fallback error state.
- Show NHL and AHL organizational coverage together because affiliate control is part of the GM role.

No proprietary layouts, text, assets, databases or implementation details are used.

## Information architecture

1. **Franchise identity header** — original crest/monogram, selected club, affiliate, season.
2. **Roster source cards** — Fictional League, Reviewed NHL/AHL Pack, and future approved packs.
3. **Readiness summary** — Ready, Needs review, or Blocked with non-color icon and concise reason.
4. **Data disclosure drawer** — identity fields, generated ratings, unknown contracts, source timestamp.
5. **Creation summary** — selected franchise, affiliate, ruleset, roster pack and save behavior.
6. **Primary action** — Create New Game; disabled only with a visible blocker and corrective path.

## Team identity

- Use an original controlled-team crest and restrained team-color accent in the header and selected card.
- Show the AHL affiliate mark beside the development-pipeline summary.
- Show compact opponent/league marks only where they improve recognition.
- All marks require text alternatives and fallback initials; branding cannot be the sole identifier.

## Responsive behavior

- Desktop: two-column source comparison with a persistent creation summary.
- Mobile: source cards become a single vertical decision flow; readiness and disclosure appear before the final action.
- Minimum touch target: 44 by 44 CSS pixels.
- No horizontal scrolling for primary content at 320 CSS pixels.

## Visual acceptance criteria

- The user can identify the selected team, affiliate, season and roster source in the first viewport.
- Real identity data and generated simulation data are visually and textually distinguished.
- A blocked pack names the exact incomplete club or count mismatch.
- Status includes icon plus text and never relies on color alone.
- Keyboard focus follows source selection, disclosure, summary and create action.
- Dense provenance details are progressively disclosed rather than always expanded.
- Missing crests fall back to readable initials without layout shift.

## Implementation boundary

This cycle adds only the readiness guard and Stage 1 direction. It does not wire the selector into the running UI, seed a new game, change active saves or approve copyrighted league/team assets.
