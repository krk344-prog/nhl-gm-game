# NHL GM Alpha 0.2 Closed Testing Guide

## Start the game

For the controlled 3–5 person Technical Alpha, use only the facilitator-provided certified Android APK and backend endpoint. Do not substitute Expo Go, a local development checkout, or a different APK during the certified smoke pass.

1. Confirm the facilitator identifies the certified test device and current backend as Ready.
2. Install the exact facilitator-provided APK on the assigned Android test phone.
3. Launch that installed app and wait for the facilitator to confirm the current backend remains Ready.
4. Record the facilitator-provided privacy-safe build/session reference before starting gameplay. This reference must identify the certified test session without exposing the backend address, raw device serial, credentials, or other private infrastructure details.
5. Begin the core test pass only after that readiness confirmation and session reference are available.

If the facilitator reports the device or backend as Not Ready at any point, stop the certified smoke pass at the current step. Do not retry against another endpoint, reinstall a different APK, or continue collecting pass evidence until the facilitator re-establishes the certified Ready state.

Development launch instructions are intentionally excluded from tester onboarding. Repository maintainers should use the authoritative development launcher (`python scripts/start_dev.py`) only for development/debug work, not as a substitute for the certified pilot package.

## Core test pass

1. Confirm eight franchises appear on the Dashboard.
2. Select a different franchise and restart the mobile client; the selection should persist.
3. Advance through at least ten calendar days.
4. Confirm scheduled games produce final scores without ties.
5. Open Game Center and verify the latest result, recent results, and standings agree.
6. Filter the roster by forwards, defense, and goalies.
7. Open Trade Center, change the trade partner, cycle both player cards, and submit one likely accepted and one likely rejected offer.
8. Confirm both proposals appear in Trade History.
9. Restart the API and mobile client; the season day, results, team selection, and trade history should persist.
10. Use Front Office → New Game / Reset Save and confirm the season returns to Day 1.

## Longer simulation pass

- Advance through a full season and confirm every team finishes with 84 games.
- Confirm the schedule and standings remain internally consistent through the final game.
- Confirm the calendar stops cleanly at the configured season end.

The Technical Alpha uses a fictional eight-team simulation. Its 84-game schedule contract is a test fixture and must not be presented as the official NHL schedule, clubs, branding, or licensed data.

## Bug report format

Include:

- Short title and severity: blocker, major, minor, or visual.
- Exact steps that caused the problem.
- Expected result and actual result.
- Phone model and Android version.
- Current game day and controlled franchise.
- Screenshot or screen recording when possible.
- The privacy-safe build/session reference recorded before the test pass.
- The facilitator-provided privacy-safe debug report or additional session evidence reference, when available.

After a blocker or major failure, stop at the observed failure and preserve the current app state until the facilitator has collected the needed evidence. Do not clear app data, reset the save, reinstall the APK, or continue the smoke route unless the facilitator explicitly releases the session for recovery. This keeps the failing state reproducible and prevents a recovery action from being mistaken for a passing retest.

Testers should not switch to a localhost/development endpoint or run repository tooling to collect evidence. If deeper diagnostics are needed, stop at the observed failure and let the facilitator collect them from the certified backend/session so the tested package and endpoint remain unchanged.

Do not include the SQLite database, backend address, raw device serial, credentials, or other private infrastructure details in a public issue. Share save-level or infrastructure evidence privately when reproduction requires it.
