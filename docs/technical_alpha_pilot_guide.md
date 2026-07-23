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

## Tester setup

Use only the installation link or package supplied by the facilitator. Record the build version and commit SHA before beginning.

For a development-hosted Android session:

1. Install Expo Go on the test phone.
2. Keep the phone and development computer on the same trusted network.
3. The facilitator runs `python scripts/start_dev.py` from the repository root.
4. Scan the provided Expo QR code.
5. Do not expose the local API to the public internet.

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
