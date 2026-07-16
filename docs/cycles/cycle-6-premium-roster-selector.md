# Development Cycle 6 — Premium roster selector

## NHL Operations requirement

A reviewed roster snapshot establishes player identity and organization assignment only. It must not establish NHL eligibility, waiver clearance, contract validity, cap charge, injury status, or lineup availability unless those fields are supplied by a separately versioned and auditable rules/transaction source.

**Acceptance case:** selecting a roster pack with complete player identity but no transaction ledger displays `eligibility: unknown`; the new-game preflight does not describe the player as waiver-cleared, cap-compliant, or game-eligible.

## Competing Games clean-room requirement

The roster-source selector uses an original **management consequence preview** rather than a technical database picker. Every source presents the same four comparison dimensions: organizational coverage, identity provenance, generated/unknown layers, and save-creation consequences. Detailed blocker evidence opens through progressive disclosure.

**Differentiation:** the game explains what a source changes in the GM experience before selection, while keeping authenticity and uncertainty visible. No proprietary code, assets, wording, databases, or layouts were copied.

## Coding task

Added `docs/ui/new-game-roster-pack-premium-v2.svg` on the existing `agent/real-roster-import-v1` branch. This is a reversible Stage 1 visual-direction artifact only; no runtime behavior changed.

## Testing task

Added one focused XML/static artifact test covering semantic labeling, true-black foundation, premium depth primitives, fictional franchise identity, disclosure labels, a realistic blocked state, and `UI Review Pending` status.

## UI/UX task

Refined the visual direction from flat black panels to a premium hockey-operations environment using layered neutral surfaces, restrained ambient franchise light, stronger typography, aligned comparison metrics, explicit uncertainty, a crest medallion, and a detailed creation summary. The design retains non-color status labels and avoids licensed team marks.

## Approval status

`UI Review Pending` — revised Stage 1 direction. Broad implementation remains blocked pending Kyle's explicit approval.
