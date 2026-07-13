# Controlled Development Cycle 3 — Bounded Outcomes

## NHL Operations — emergency-goaltender designation edge case

**Verified context:** The ratified 2026–30 NHL/NHLPA labor agreement takes effect for 2026–27 and replaces the shared home-arena emergency-goaltender model with a club-designated traveling emergency goaltender. Public reporting also identifies eligibility restrictions intended to prevent clubs from using the role as an undeclared third professional goaltender.

**Testable requirement:** A 2026–27-or-later club may replace its designated traveling emergency goaltender after opening night, but the replacement must complete the same season-versioned eligibility validation before the club may begin its next game. Historical designations remain in the audit log; replacing the record must not retroactively alter earlier compliance results.

**Acceptance criteria**
1. The rule is inactive for saves governed by the 2025–26 ruleset.
2. A designation change records effective date, prior designee, new designee, validating authority, and validation result.
3. A pending or failed replacement leaves the prior eligible designation active when still available; otherwise the next game is blocked with a compliance task.
4. The replacement cannot consume an active-roster slot merely by being designated.
5. The UI explains whether the blocker is missing designation, eligibility failure, or unavailable designee.

**Source basis:** NHL announcement of CBA ratification dated July 8, 2025; NHL/NHLPA 2026–30 memorandum reporting; secondary reporting used only to identify the edge case. Final implementation must cite the versioned rules-registry source.

## Competing Games — explainable daily briefing pattern

**Observed pattern:** Deep sports-management simulations commonly centralize staff messages, deadlines, results, and recommendations in an inbox or daily briefing. This reduces navigation cost, but conventional inboxes often become chronological dumping grounds where routine notices obscure decisions.

**Original clean-room requirement:** Add a generated `Morning Brief` that groups new information by decision consequence rather than source: `Must decide`, `Review recommended`, and `Recorded automatically`. Each item states what changed, why it matters, the responsible staff member, deadline, confidence, and one direct action.

**Differentiation and implementation notes**
- The brief is a derived view over existing events and tasks, not a separate source of truth.
- Duplicate notices from scouting, medical, cap, and schedule systems collapse into one explainable item with linked evidence.
- Users may defer optional items, but mandatory compliance items remain visible in the Command Center and DecisionGate.
- The system records why an item changed priority so users can learn front-office cause and effect.
- Desktop supports a compact split view; mobile opens one item at a time with a persistent next-critical action.

No proprietary code, text, assets, databases, or branded layouts are used.

## Coding — validate Stage 2 artifacts in existing CI

Updated `.github/workflows/ci.yml` on `agent/ui-dashboard-approval-v1` to run `python scripts/validate_ui_artifacts.py` in the existing backend job after compilation and before the backend/full-season suite. This is a reversible one-step workflow change with no production runtime impact and no new dependency.

## Testing — verify previous head and define CI acceptance

Inspected workflow run `29217895931` for the previous PR #7 head. Both jobs completed successfully:

- `backend`: compilation, backend/full-season tests, and test-log upload passed.
- `android-bundle`: clean dependency installation and Android production export passed.

Acceptance for the new head is now stricter: the backend job must additionally pass `Validate Stage 2 UI artifacts`. A failure in malformed SVG, accessibility metadata, responsive scaling, or required dense/non-ideal state labels will block the workflow before the broader test suite.

## UI/UX Design — Morning Brief triage contract

Defined a reusable briefing interaction that supports the clean-room requirement without changing the approved Stage 2 visual direction:

- The Command Center shows only the top three consequential items plus counts for lower-priority groups.
- Mandatory items use icon, severity word, deadline text, and consequence statement; color is supplementary.
- Expanding an item reveals evidence, responsible staff, recommendation confidence, and reversible actions without leaving the page.
- Desktop uses a two-column brief/detail pattern at wide widths and a single-column disclosure pattern below 900 px.
- Mobile uses 44 px minimum touch targets, preserves the critical-action control above the safe-area inset, and never places horizontal tables in the primary flow.
- Loading uses stable skeleton geometry; offline mode shows cached timestamp and disables actions requiring server confirmation; error mode preserves already loaded items and offers a scoped retry.
- Keyboard order follows priority order, expanded detail receives a programmatic heading, and focus returns to the triggering item when closed.

No new visual mockup was produced because Stage 2 desktop/mobile approval remains pending. The next expected preview is the Stage 3 implemented Command Center screenshot after Stage 2 approval.