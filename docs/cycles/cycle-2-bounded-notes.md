# Controlled Development Cycle 2 — Bounded Outcomes

## NHL Operations — traveling emergency-goaltender readiness

**Requirement:** For saves using the 2026–27 ruleset or later, each club must have a designated traveling emergency goaltender record before opening night. The record must be separate from the active playing roster and must pass season-versioned eligibility validation.

**Acceptance criteria**
1. The rule is disabled for 2025–26 and enabled by the active 2026–27 ruleset.
2. A club cannot advance into its first regular-season game without a designated emergency-goaltender record.
3. Eligibility validation rejects a candidate who played professional hockey in the prior three seasons, appeared in an NHL game under a standard player contract, exceeded the career professional-game threshold, or remains on an NHL reserve/RFA list.
4. The record may also hold a non-player staff role, but cannot consume an active-roster or standard-player-contract slot unless separately signed as a player.
5. The UI presents failures as an operations-compliance task with the failed criterion and corrective action.

**Source basis:** NHL/NHLPA 2026–30 labor-agreement reporting and the ratified 2026–27 transition. Implementation must cite the final rules-registry source rather than relying on prose in this note.

## Competing Games — accountable delegation pattern

**Observed pattern:** Deep hockey-management simulations such as Franchise Hockey Manager expose broad control over staffing, scouting, tactics, finances, and affiliates. Depth is valuable, but assigning every subsystem equal urgency can overwhelm a user.

**Original requirement:** Every recurring operational task may be set to `GM decides`, `staff recommends`, or `staff executes`, with a visible responsibility owner and escalation threshold. Mandatory league-compliance decisions can never be fully hidden or auto-dismissed.

**Differentiation and implementation notes**
- Recommendations include rationale, confidence, deadline, and the staff member responsible.
- Executed delegated actions appear in an auditable activity feed and can be reverted only when league rules permit.
- Escalations enter `Needs Your Attention` when risk, cost, owner expectation, or uncertainty crosses a configured threshold.
- New users receive safe defaults; advanced users can tune delegation by workflow.
- Mobile exposes responsibility and escalation state without adding another dense settings screen.

No proprietary code, text, assets, databases, or layouts are used.

## Coding — Stage 2 artifact validator

Added `scripts/validate_ui_artifacts.py`, a dependency-free validator for the two Stage 2 SVG mockups. It verifies parseability, SVG root/namespace, responsive `viewBox`, image semantics, accessible title/description wiring, and presence of mandatory, offline, decision-queue, and advance-control state labels.

## Testing — focused validator execution

Validated the script logic against the checked-in desktop and mobile artifact contracts. The positive path passes both artifacts; missing required labels, missing `viewBox`, malformed XML, and broken accessible title/description references return actionable non-zero failures.

Runtime interaction validation remains intentionally deferred until Stage 3 because the current deliverables are mockups rather than running components.

## UI/UX Design — decision gate component contract

Defined a reusable `DecisionGate` interaction contract without changing the pending Stage 2 visual direction:

- The advance control displays the count of unresolved mandatory items.
- Activating a blocked advance opens a focused gate sheet listing only blockers, their deadlines, owners, and direct corrective actions.
- Optional work remains available outside the gate and is never visually equated with compliance blockers.
- Desktop uses an anchored modal or drawer no wider than the decision region; mobile uses a full-height sheet.
- Initial focus lands on the gate heading, keyboard focus remains trapped while open, `Escape` closes only when no irreversible action is underway, and focus returns to the invoking control.
- Status uses icon, label, and explanatory text rather than color alone.
- The gate must remain understandable at 200% zoom and with six or more blockers.

No new mockup was produced because Stage 2 desktop/mobile approval is still pending. This component contract is reversible preparation for a future implemented shell.
