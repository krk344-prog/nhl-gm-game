# Technical Alpha Go / No-Go Card

Use this card immediately before presenting the 3–5 tester pilot for Kyle's approval. It is a facilitator aid, not authorization to merge PR #13 or begin the pilot.

## Package identity

Record these values from the same validated build and session:

- PR: `#13`
- Branch: `agent/alpha-rules-integration-v1`
- Commit SHA: ______________________________
- APK SHA-256: _____________________________
- Android package: `com.krk344.nhlgmgame`
- Build type: standalone release APK
- Endpoint class: tester-reachable, non-loopback
- Endpoint qualification: at least 15 uninterrupted minutes

Any commit, APK checksum, package, build-type, or endpoint change invalidates the remaining evidence and requires a fresh card.

## Required route evidence

Every item must pass on the exact installed package above:

- [ ] Application installs and launches without facilitator repair.
- [ ] New game begins successfully.
- [ ] Tester selects one of the eight fictional franchises.
- [ ] Advance day completes and produces coherent league state.
- [ ] Roster view loads and remains actionable.
- [ ] Standings load and reconcile with the advanced state.
- [ ] Trade flow completes one bounded accepted, rejected, or blocked outcome.
- [ ] Save persists after application/backend restart.
- [ ] Reload restores the same controlled franchise and league state.
- [ ] Reset intentionally returns the fictional Alpha save to Day 1.
- [ ] Privacy-safe debug output can be reproduced for a defect report.

## Alpha disclosure

The facilitator must state before testing:

- This is an eight-franchise fictional Technical Alpha.
- The 82-game schedule is a test environment, not the official NHL schedule.
- Reset intentionally returns the save to Day 1.
- Official NHL branding, licensed data, and complete production rules are not represented.

## Tester-experience requirement

Before coaching, capture each tester's:

1. first interpretation of the screen or task;
2. first action attempted;
3. highest-friction moment;
4. whether the next step was discoverable without explanation.

A successful installation alone is not successful onboarding. The first actionable state must be understandable and stable.

## UI Preview / Approval

- Preserve all existing Stage 2 approvals.
- Capture the nine required Stage 3 implemented states from this exact package/session.
- Label every implemented screen `UI Review Pending` until Kyle explicitly approves Stage 3/Stage 4 evidence.
- Do not represent screenshots from another commit, APK, endpoint, or session as current evidence.

## Defect and privacy gate

The result is **NO-GO** when any of the following is true:

- one required route item fails or lacks evidence;
- save, reload, or reset state does not reconcile;
- any open Blocker exists;
- any relevant unresolved Major defect exists;
- evidence mixes package identities or sessions;
- tester identity, device serial, private endpoint, credentials, database, save path, or raw logs appear in public evidence;
- Stage 3 evidence is incomplete;
- Kyle's approval is absent.

## Decision

- [ ] **READY FOR KYLE APPROVAL** — all evidence is complete, reconciled, privacy-reviewed, and no Major/Blocker defect remains.
- [ ] **NO-GO** — record the failed condition, owner, mitigation, and required rerun.

Kyle's explicit approval is required separately for:

1. starting the 3–5 tester pilot; and
2. merging PR #13.
