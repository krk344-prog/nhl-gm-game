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

1. The exact package has a version identifier and commit SHA.
2. The API and application use the supported integrated launch path.
3. A clean-install smoke test has passed on the same package testers will receive.
4. New Game, franchise selection, advance day, roster, standings, trade, save, reload, debug report, and reset have passed.
5. Known limitations and issue-report instructions are included with the build.
6. A private channel exists for save files or personally identifying device information.

## Configured APK release procedure

Use this sequence for every physical-device pilot build. Do not distribute an APK built with `127.0.0.1`, `localhost`, or another endpoint the tester device cannot reach.

1. Check out `agent/alpha-rules-integration-v1` and confirm the working tree is clean.
2. Connect the facilitator computer and supported Android device to the same trusted network.
2a. Connect the Android device by USB, enable USB debugging, and run `python scripts/check_alpha_android_device.py`. Continue only when it returns `"status": "ready"`. When more than one authorized device is attached, rerun with `--serial <ADB_SERIAL>`. Keep the serial private; the command's public-ready output intentionally omits it.
3. Start the integrated backend from the repository root with `python scripts/start_dev.py`.
4. From a second terminal at the repository root, run `python scripts/prepare_alpha_build.py --season-id 2026-27`.
5. Continue only when the command returns JSON with `"ready": true`, a non-loopback `api_base_url`, the expected season context, `"ref": "agent/alpha-rules-integration-v1"`, and a `build_command` targeting `scripts/build_alpha_apk_local.py`.
6. Run the returned `build_command` exactly as emitted. Do not edit the endpoint or branch. The command has already selected a tester-reachable endpoint and completed backend preflight.
7. For a previously approved endpoint, run `python scripts/prepare_alpha_build.py --api-base-url <URL> --season-id 2026-27` and apply the same criteria.
8. Stop when the command returns `"ready": false`; do not guess an address or manually assemble a build command.
9. The local builder must produce `dist/technical-alpha/nhl-gm-technical-alpha.apk`, `nhl-gm-technical-alpha.apk.sha256`, `nhl-gm-android-export.tar.gz`, `nhl-gm-android-export.sha256`, and `technical-alpha-build.txt` from the exact PR #13 commit.
10. Run `python scripts/verify_alpha_artifact.py dist/technical-alpha --expected-commit <COMMIT_SHA> --expected-api-base-url <URL>`.
11. Continue only when the verifier returns JSON with `"status": "pass"`; it validates both portable checksum files, the exact commit, exact endpoint, and expected `debug-apk` build type.
12. Install and confirm that exact artifact with `python scripts/install_alpha_apk.py dist/technical-alpha --expected-commit <COMMIT_SHA> --expected-api-base-url <URL>`. Add `--serial <ADB_SERIAL>` only when the device preflight required it.
13. Continue only when the installer returns `"status": "pass"`, `"installation_confirmed": true`, and `"android_package": "com.krk344.nhlgmgame"`. It re-runs artifact verification, uses the same authorized device selection rules, installs with `adb install -r`, and confirms the expected package through Android's package manager. Do not substitute an earlier APK or switch devices without repeating preflight and evidence capture.
14. Run `python scripts/launch_alpha_app.py`. Add `--serial <ADB_SERIAL>` only when the device preflight required it.
15. Continue only when the launcher returns `"status": "pass"`, `"installation_confirmed": true`, and `"launch_confirmed": true`. It confirms the installed package, starts the launcher activity, and verifies the application process on the same authorized device without publishing the device serial.
16. Confirm health, season context, franchise selection, day advancement, save/reload, trade history, debug report, and reset.
17. Copy `docs/technical_alpha_device_smoke_record.template.json` to a private working location. Replace every placeholder and set checks to `true` only after direct observation.
18. Record the device model, Android version, commit, exact APK SHA-256, approved API base URL, timestamp, installation and route results, and blockers. Do not commit a completed device record containing local network or device details.
19. Validate it with `python scripts/validate_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>`.
20. Continue only when the device-smoke validator returns `"status": "pass"`.
21. Generate the privacy-safe summary with `python scripts/summarize_alpha_device_smoke.py <DEVICE_SMOKE_RECORD.json>`. Post only this redacted summary publicly.
22. Distribute the APK only after the exact-package smoke test passes and all verification steps pass.

A changing local IP address invalidates the configured APK. Repeat preparation, local build, verification, installation, launch confirmation, and smoke validation whenever the tester-facing URL changes.

## Tester setup

Use only the installation package supplied by the facilitator. Record its commit SHA before beginning. Keep the phone on the facilitator-approved network. Stop and report `Connection unavailable` rather than changing endpoint settings independently.

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
9. Close the application and restart the API/application.
10. Confirm the selected franchise, current day, results, standings, and trade history persist.
11. Generate the debug report.
12. Use New Game / Reset Save and confirm the game returns to Day 1 only after confirmation.

## Test feedback prompts

- What did you believe your next action should be?
- Which screen was hardest to understand?
- Did any label, disabled control, or status appear misleading?
- Did franchise identity make the game understandable without becoming distracting?
- Which action felt most satisfying?
- What single change would most improve a second session?

## Stop conditions

Stop and report when the application repeatedly crashes; a save cannot reopen; franchise, day, standings, results, or trade history changes unexpectedly; reset occurs without confirmation; a trade duplicates or loses players; private data is exposed; or the device becomes unusually hot or unstable.

## Bug report format

Include a short title; severity; commit SHA; reproduction steps; expected and actual result; phone model and Android version; current game day and franchise; screenshot when possible; and privacy-reviewed JSON from `/api/v1/debug-report`.

Do not post the SQLite database, authentication data, local network address, device identifier, or personal information in a public issue. Share save-level evidence only through the private facilitator channel.

## Pilot exit criteria

The pilot may expand beyond five testers only after every blocker has a disposition, save/reload succeeds across completed sessions, installation succeeds on the supported device set, the exact package is reproducible from the recorded commit, known limitations match observed behavior, and Kyle explicitly approves the next testing stage.
