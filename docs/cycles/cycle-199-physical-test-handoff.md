# Cycle 199 — Physical Test Handoff

## Purpose

PR #13 is green in automated Alpha validation. This checkpoint does not add feature scope or new validation machinery. It freezes the next action to the first real physical execution chain and records the tester-facing acceptance boundaries before that run begins.

## NHL operations disclosure

The Technical Alpha uses a fictional eight-team league and is not a current-NHL rules simulator. For roster interpretation during the pilot, do not imply that every in-game roster state mirrors the current NHL active-roster rule. NHL Hockey Operations guidance states that clubs may carry no more than 23 players on the playing roster from the start of the regular season through the trade deadline, with a minimum playing roster of 18 skaters and two goaltenders; injured-reserve players do not count against the 23-player limit.

Tester wording: **Roster screens in this Alpha validate navigation, persistence, and trade workflow. Treat current-NHL roster-limit realism as a disclosed simulation limitation unless the screen explicitly states otherwise.**

## First-session install/launch recovery requirement

A failed install or launch must not send the facilitator back through already-passed gates without evidence that those gates were invalidated.

Required presentation:

1. retain every valid prior gate as `Passed`;
2. mark the earliest failed gate as `Blocked`;
3. show one recovery action for that failure;
4. do not expose endpoint, device selector, serial, identity-key, or other private execution detail in the shareable tester status;
5. rerun only the invalidated gate and its downstream dependents.

Example public state: `Blocked — install/launch. Recovery: reconnect the authorized device and rerun device preflight.`

## Authoritative physical execution sequence

1. Select and qualify one stable tester-reachable backend endpoint.
2. Run the share-safe readiness check and require `ready: true`.
3. Build the exact PR #13 `standalone-release-apk` against that qualified endpoint.
4. Verify commit, endpoint identity, package, build type, and checksums.
5. Preflight one supported, authorized physical Android device.
6. Install and launch the exact verified APK.
7. Run the ordered smoke: new game → franchise selection → advance day → roster → standings → trade → save → reload → reset.
8. Produce the private device-smoke record and approved redacted summary.
9. Capture Stage 3 screenshots from that exact APK/backend pairing.

Stop at the first failed gate. Fix only the concrete failure before continuing.

## UI approval boundary

The approved Stage 2 Team-Branded Command Center direction remains unchanged. No production UI is modified by this checkpoint. Implemented screens remain `UI Review Pending` until Stage 3 captures from the exact pilot candidate are reviewed and approved by Kyle.

## Release decision

This checkpoint does not authorize merge or pilot start. The Technical Alpha gate remains blocked until the tester-accessible endpoint/build/device evidence chain is complete.
