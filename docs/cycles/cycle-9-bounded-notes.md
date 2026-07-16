# Controlled Development Cycle 9 — Bounded Notes

Status: UI Review Pending. This cycle advances the existing roster-source draft PR without merging or beginning broad implementation.

## NHL Operations — emergency-goaltender staffing readiness

Requirement: for 2026–27 and later rulesets, each organization must maintain an eligible traveling emergency-goaltender assignment before opening night. The readiness check must record eligibility evidence, assignment status, travel availability, and a named front-office owner. A save may continue with a warning during preseason, but opening-night advancement must fail closed when the role is unassigned or the eligibility review is incomplete.

Acceptance cases:
1. Eligible emergency goaltender, reviewed and assigned => opening-night readiness passes.
2. Candidate exists but eligibility is unverified => blocking readiness item.
3. No assigned candidate => blocking readiness item with owner and corrective action.
4. 2025–26 ruleset => legacy emergency-goaltender workflow remains season-versioned and is not silently replaced.

Source basis: the NHL/NHLPA agreement effective for 2026–27 changes emergency-goaltender operations and requires team-specific readiness rather than relying on the prior home-market shared model. Final implementation must bind to the versioned CBA source record, not this summary alone.

## Competing Games — clean-room consequence comparison

Observed category pattern: strong management simulations help users compare options by showing the operational consequences of a choice, while keeping detailed rules available on demand.

Original requirement: when comparing roster packs, each option must use the same four-row structure: identity coverage, rules compatibility, management uncertainty, and blocking readiness. Differences must be highlighted by label and icon, not only color. Detailed field provenance remains in the existing desktop drawer or mobile bottom sheet.

Differentiation: the comparison is framed around what the GM can safely decide on day one rather than generic database completeness. No proprietary text, layout, data, or assets are reused.

## Coding — premium interaction tokens

Added reusable interaction tokens to `docs/ui/premium-surface-tokens-v1.json` for bounded transitions, zero hover layout shift, reduced-motion behavior, blocker explanations, and persistent selected-state indicators. This is a small reversible design-contract change on draft PR #10; no production UI behavior changed.

## Testing — focused interaction-token validation

Added `test_premium_interaction_tokens_prevent_motion_and_state_regressions` to validate:
- transition duration stays within the bounded premium range;
- hover cannot move content;
- reduced motion removes nonessential animation;
- blocked states include a reason;
- selected states retain a persistent non-color indicator.

Result at commit time: change committed; GitHub Actions validation pending. Prior head run #99 passed.

## UI/UX Design — premium comparison rhythm

Design improvement: roster-source choices should read as a controlled comparison, not two independent decorative cards. Both cards use identical row order and baseline alignment, while only the selected card receives elevated depth and restrained franchise lighting. The blocked card remains visually polished and readable rather than dimmed into illegibility.

Premium acceptance criteria:
- one dominant selected state, with no competing glow effects;
- identical label order and metric alignment across options;
- black canvas and charcoal layers remain visually distinct;
- team color accents stay localized to identity, focus, selected state, and primary action;
- blocked and error states retain full text contrast and an explicit next action;
- desktop details open in a drawer; mobile details open in a bottom sheet;
- focus, selection, and blocker state never rely on color alone.

## Coordination boundary

No PR was merged, no broad branch was created, and no copyrighted league or club visual assets were introduced. The current roster-selector direction remains Stage 1 and UI Review Pending. Stage 2 desktop/mobile composition remains gated on Kyle's explicit direction approval.
