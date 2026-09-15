# Technical Alpha exact-package execution checkpoint

Status: **Pilot blocked until completed**  
Integration lane: **PR #13 — `agent/alpha-rules-integration-v1`**  
UI status: **UI Review Pending**

This checkpoint is the facilitator's final identity boundary for the controlled 3–5 person Technical Alpha. It prevents evidence from different commits, APKs, endpoints, installs, save sessions, or screenshot runs from being combined into a false readiness pass.

## Authoritative application path

- Backend/application launcher: `python scripts/start_dev.py`
- Packaged Android application ID: `com.krk344.nhlgmgame`
- Required gameplay route: new game → franchise selection → advance day → roster → standings → trade → save → reload → reset
- Reset expectation: the fictional Alpha save returns to Day 1.

The Alpha contains eight fictional franchises and an 82-game test schedule. It is not an official NHL schedule, licensed roster product, or production rules simulation. Testers must see this limitation before beginning the route.

## One-session identity record

Record these values once, before installation. Any later change invalidates downstream evidence and requires a new checkpoint.

| Identity field | Required value/evidence |
|---|---|
| PR | `13` |
| Branch | `agent/alpha-rules-integration-v1` |
| Commit SHA | Exact green-CI head used for the build |
| CI run | Successful Alpha validation run for that exact SHA |
| API endpoint class | Tester-reachable, non-loopback endpoint; keep the address private |
| Endpoint qualification | At least 15 uninterrupted minutes with passing backend checks |
| APK SHA-256 | Exact verified release artifact checksum |
| Build type | Configured standalone release APK |
| Android package | `com.krk344.nhlgmgame` |
| Installed package result | Verified install and confirmed application process |
| Save/session identifier | Private facilitator record tying route, reload, reset, and captures together |

## Fail-closed execution sequence

1. Confirm PR #13 remains open, draft, unmerged, and mergeable.
2. Confirm the selected commit has a successful Alpha validation run.
3. Qualify the tester-reachable endpoint for at least 15 uninterrupted minutes.
4. Build the configured release APK from a clean working tree at the recorded commit.
5. Verify the artifact identity, embedded endpoint class, package name, and SHA-256.
6. Install and launch the exact APK on the authorized Android device or approved equivalent packaged-build environment.
7. Complete the required route without substituting a different build or endpoint.
8. Prove save/reload continuity, then prove reset returns the fictional session to Day 1.
9. Capture the nine required Stage 3 implemented states from this same package and session.
10. Reconcile defects, privacy review, the redacted public summary, and the go/no-go record.

A missed step, identity mismatch, interrupted route, persistence mismatch, reset mismatch, open Blocker, or relevant unresolved Major defect is a **no-go**.

## Competing-games usability requirement — persistent build identity

Early management-game tests often fail because facilitators and testers discuss a screen without knowing whether they used the same build. The Alpha must therefore expose a compact, non-intrusive test identity in the facilitator-accessible diagnostic surface:

- shortened commit identity;
- build type;
- package version;
- save/session identifier;
- endpoint class, never the private address;
- `UI Review Pending` status.

This is an original testability requirement. It must not imitate another game's branded layout, copy, assets, or implementation.

## UI/UX implemented-state specification

For Stage 3 evidence, the diagnostic identity should appear as a compact expandable **Test Build** row rather than a permanent banner competing with hockey decisions.

Acceptance criteria:

- collapsed state shows `Test Build`, package version, and a non-color status label;
- expanded state exposes the shortened commit, build type, endpoint class, and session identifier;
- private endpoint addresses, device serials, credentials, database paths, saves, and raw logs never appear in public captures;
- the row is keyboard reachable and screen-reader labeled;
- touch target is at least 44 × 44 CSS pixels;
- 200% zoom does not create horizontal page scrolling;
- offline or identity-mismatch states use text and iconography, not color alone;
- the row remains secondary to the current gameplay task and does not obscure advance-day or required decisions;
- all implemented screens remain `UI Review Pending` until Kyle approves Stage 3 and Stage 4 evidence.

## Tester feedback requirement

Before coaching, record for each anonymous tester:

1. what they believed the current screen asked them to do;
2. their first attempted action;
3. the highest-friction moment;
4. whether the next step was independently discoverable;
5. whether the Test Build identity was understandable when opened.

## Privacy boundary

The public issue report may include the PR number, shortened commit, CI run number, pass/fail status, package name, build type, route completion, defect counts, and UI approval state. Keep endpoint addresses, tester identities, device identifiers, credentials, databases, save files/paths, and raw logs private.

## Approval boundary

Completion of this checkpoint may mark the Technical Alpha gate **ready for Kyle's approval** only when every item is evidenced and a tester-accessible build or URL exists. It does not authorize the pilot, merge PR #13, or mark the UI approved. Those remain separate explicit Kyle decisions.
