# NHL GM Technical Alpha Pilot Guide

## Pilot purpose

This is a controlled technical-alpha test for 3–5 invited participants. The goal is to validate installation, navigation, save integrity, the core franchise loop, and the quality of bug reports. It is not a content-complete or production-ready release.

## Required disclosure

- The pilot uses eight original fictional franchises and one fictional AHL affiliate.
- The pilot uses an 82-game test schedule. The official 2026–27 NHL schedule uses 32 teams and 84 games per club, so testers must not interpret the Alpha league structure as a current NHL rules representation.
- Some front-office, scouting, contract, waiver, draft, free-agency, staffing, business-operations, and multi-season systems are incomplete or unavailable.
- Ratings, contracts, team marks, player identities, and outcomes in the fictional pack are simulation data, not official NHL data.
- The build may reset or invalidate test saves before a later release.

## Facilitator readiness check

Do not distribute the build until all of the following are true:

1. The exact package or controlled URL has a version identifier and commit SHA.
2. The API and application use the supported integrated launch path.
3. A clean-install smoke test has passed on the same package testers will receive.
4. New Game, franchise selection, advance day, roster, standings, trade, save, reload, debug report, and reset have passed.
5. Known limitations and issue-report instructions are included with the build.
6. A private channel exists for any save file or personally identifying device information.

## Configured APK release procedure

Use this sequence for every physical-device pilot build. Do not distribute a pull-request APK that was built with `127.0.0.1`, `localhost`, or another endpoint the tester device cannot reach.

1. Connect the facilitator computer and supported Android device to the same trusted network.
2. From the repository root, run `python scripts/select_alpha_api_endpoint.py` and copy `recommended_api_base_url` from the JSON output. Stop when the command returns `"ready": false`; do not guess an address.
3. Start the integrated backend from the repository root with `python scripts/start_dev.py`.
4. Use the selector's exact recommended URL, including `/api/v1`, as `<URL>`. Confirm the device can remain on that network for the full smoke test and pilot session.
5. Before building, run `python scripts/check_alpha_backend.py --api-base-url <URL> --season-id 2026-27` from a second terminal.
6. Continue only when the preflight returns a successful health check, the expected season context, and a non-loopback endpoint.
7. In GitHub Actions, manually run **Alpha validation** for the PR #13 head and supply the same URL as the required `api_base_url` input.
8. Download and extract the artifact named `nhl-gm-technical-alpha-android-<commit>` from that completed workflow run.
9. From the repository root, run `python scripts/verify_alpha_artifact.py <ARTIFACT_DIR> --expected-commit <COMMIT_SHA> --expected-api-base-url <URL>`.
10. Continue only when the verifier returns JSON with `"status": "pass"`; this single check validates `nhl-gm-technical-alpha.apk`, `nhl-gm-technical-alpha.apk.sha256`, `nhl-gm-technical-alpha-android-export.zip.sha256`, both portable checksum files, `technical-alpha-build.txt`, the exact commit, the exact non-loopback API URL, and the expected `debug-apk` build type.
11. Install that exact APK on the supported Android test device. Do not substitute a locally rebuilt or earlier APK.
12. With the device on the approved network, confirm health, season context, franchise selection, day advancement, save/reload, trade history, debug report, and reset.
13. Copy `docs/technical_alpha_device_smoke_record.template.json` to a private working location. Replace every placeholder, set a check to `true` only after directly observing it pass on the exact installed APK, and leave any unresolved problem in `blockers`.
14. Record the device model, Android version, commit, exact APK SHA-256, approved API base URL, test timestamp, artifact-verifier result, installation result, gameplay-route results, persistence result, reset result, and blockers in that private copy. Do not commit a completed device record containing local network or device details.
15. Validate the completed private record with `python scripts/validate_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>`.
16. Continue only when the device-smoke validator returns `"status": "pass"`; any missing route, failed persistence step, loopback endpoint, digest mismatch, placeholder, or declared blocker stops distribution.
17. Generate the privacy-safe approval summary with `python scripts/summarize_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>`. Post only this redacted summary to the public coordination record.
18. Distribute the APK to the 3–5 person pilot only after the exact-package smoke test passes and artifact verification, device-smoke validation, and the redacted approval summary all pass.

A changing local IP address invalidates the configured APK. Repeat endpoint selection, preflight, workflow dispatch, artifact verification, installation, and smoke validation whenever the tester-facing API URL changes.

## Tester setup

Use only the installation link or package supplied by the facilitator. Record the build version and commit SHA before beginning.

For a development-hosted Android session:

1. Install Expo Go on the test phone.
2. Keep the phone and development computer on the same trusted network.
3. The facilitator runs `python scripts/start_dev.py` from the repository root.
4. Scan the provided Expo QR code.
5. Do not expose the local API to the public internet.

For an installed APK session:

1. Install only the checksum-verified APK supplied by the facilitator.
2. Keep the phone on the network specified by the facilitator.
3. Confirm that the build identifier shown or supplied matches the recorded commit.
4. Stop and report `Connection unavailable` rather than changing network or endpoint settings independently.

## Guided test route

Complete the route in order. Stop and report a blocker when a required step cannot be completed.

1. Launch the application and confirm the Technical Alpha disclosure is visible or supplied with the build.
2. Confirm eight fictional franchises are available.
3. Select a franchise and record its name.
4. Review the dashboard, roster, standings, next matchup, and recent results.
5. Advance at least ten calendar days and confirm games produce final scores without ties.
6. Filter the roster by forwards, defense, and goaltenders.
7. Open Trade Center, choose a trade partner, and submit one likely accepted and one likely rejected proposal.
8. Confirm both proposals appear in Trade History.
9. Close the application and restart the API/application using the facilitator's instructions.
10. Confirm the selected franchise, current day, results, standings, and trade history persist.
11. Generate the debug report.
12. Use New Game / Reset Save and confirm the game returns to Day 1 only after the confirmation step.

## Test feedback prompts

After the route, answer:

- What did you believe your next action should be at each step?
- Which screen was hardest to understand?
- Did any label, disabled control, or status appear misleading?
- Did the franchise identity make the game world understandable without becoming distracting?
- Which action felt most satisfying?
- What single change would most improve a second session?

## Stop conditions

Stop testing and report immediately when any of these occurs:

- the application or API repeatedly crashes;
- a save cannot be reopened;
- the controlled franchise, game day, standings, results, or trade history changes unexpectedly after restart;
- reset occurs without an explicit confirmation;
- a trade creates missing or duplicated players;
- the application exposes a local file path, secret, token, database content, or another tester's information;
- the device becomes unusually hot, unstable, or consumes abnormal battery during ordinary navigation.

## Bug report format

Include:

- short title;
- severity: blocker, major, minor, or visual;
- build version and commit SHA;
- exact reproduction steps;
- expected result and actual result;
- phone model, Android version, and whether the session used Expo Go or an installed package;
- current game day and controlled franchise;
- screenshot or screen recording when possible;
- JSON from `/api/v1/debug-report`, after checking that it contains no personal information.

Do not post the SQLite database, authentication data, local network address, device identifier, or personal information in a public issue. Share save-level evidence only through the private channel designated by the facilitator.

## Pilot exit criteria

The pilot may expand beyond five testers only after:

- every blocker has a documented disposition;
- save/reload succeeds across all completed test sessions;
- installation succeeds on the supported device set;
- the exact distributed package is reproducible from the recorded commit;
- known limitations match the behavior testers actually observed;
- Kyle explicitly approves the next testing stage.
