# Technical Alpha Pilot Go/No-Go Record

Use this record only after the exact tester package has completed the controlled device-smoke route. Keep endpoint addresses, device identifiers, saves, databases, authentication material, and raw logs in the private evidence bundle.

## Release identity

- Decision date/time:
- Facilitator:
- Source commit:
- APK SHA-256:
- Package: `com.krk344.nhlgmgame`
- Build type: configured standalone release APK
- Anonymous tester cohort ID:

## Required evidence

Mark each item `Pass`, `Pending`, or `Block` and reference the private evidence location.

- [ ] Artifact metadata matches the source commit, endpoint class, package, and checksum.
- [ ] Backend is tester-reachable before New Game and after save/close/reload.
- [ ] Exact APK installs and launches on the supported Android device.
- [ ] New Game and franchise selection pass.
- [ ] Advance Day, roster, standings, and trade pass.
- [ ] Save, close, reload, and state reconciliation pass.
- [ ] Reset returns the fictional Alpha save to Day 1 and its irreversible effect was acknowledged.
- [ ] Debug output is reproducible and privacy-reviewed.
- [ ] Stage 3 screenshots come from this exact package and session.
- [ ] No unresolved Blocker or Major defect affects the required route.
- [ ] Tester onboarding, known limitations, and private bug-report instructions are complete.

## Required disclosures

- This Technical Alpha uses eight fictional franchises and an 82-game test schedule.
- It is not an official NHL schedule, licensed league database, or representation of the current 32-team league format.
- Reset permanently returns the test save to Day 1.
- Implemented screens remain `UI Review Pending` until Kyle approves Stage 3/Stage 4 evidence.

## Decision

Select exactly one:

- [ ] **GO — Ready for Kyle approval.** Every readiness item is evidenced and a tester-accessible configured package is available. This does not authorize pilot start or PR merge.
- [ ] **NO-GO — Blocked.** Record the blocking item, owner, mitigation, and retest requirement below.

### Blocking item / residual risk

- Severity:
- Owner:
- Evidence:
- Mitigation:
- Retest required:

## Approvals

- Facilitator readiness sign-off:
- Release Engineering sign-off:
- Testing sign-off:
- UI evidence status: `UI Review Pending`
- Kyle pilot approval: `Not granted`
- Kyle merge approval: `Not granted`

The pilot must not begin and PR #13 must not merge until Kyle explicitly grants the corresponding approval.