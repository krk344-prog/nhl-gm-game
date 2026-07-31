# NHL GM Technical Alpha — Tester Launch Card

> Complete every bracketed field before distribution. Keep this card beside the exact APK or browser link supplied to testers.

## Build identity

- **Commit:** `[FULL_COMMIT_SHA]`
- **Package or URL:** `[APK_FILENAME_OR_BROWSER_URL]`
- **Package checksum (APK only):** `[SHA256]`
- **Test window:** `[START_DATE_TIME]` to `[END_DATE_TIME]`
- **Anonymous tester ID:** `[TESTER_ID]`

## Connection status

- **Backend:** `[Ready | Unavailable | Maintenance]`
- **Supported network:** `[NETWORK_REQUIREMENT]`
- **Stop instruction:** Do not begin or continue when the backend is not **Ready**. Do not change endpoint or network settings independently.

## Start Test

Record the route start time, then complete this route in order:

1. New Game
2. Select one of the eight fictional franchises
3. Advance at least ten calendar days
4. Review roster and standings
5. Submit one likely accepted and one likely rejected trade
6. Confirm both appear in Trade History
7. Save, close, and reload
8. Generate the debug report
9. Reset the save and confirm return to Day 1
10. Record the route end time and final game day

- **Route started:** `[DATE_TIME]`
- **Route ended:** `[DATE_TIME]`
- **Final game day before reset:** `[GAME_DAY]`

## Required disclosure

This Technical Alpha uses eight original fictional franchises and an 82-game test schedule. It is not official NHL data or a representation of the current NHL league structure or schedule. Major front-office systems remain incomplete, and test saves may be reset or invalidated by later builds.

**Most important known limitation:** `[ONE_SENTENCE_LIMITATION]`

## Report a problem privately

- **Destination:** `[PRIVATE_BUG_REPORT_DESTINATION]`
- Include: title, severity, anonymous tester ID, commit, route timestamp, steps, expected result, actual result, phone model, Android version, game day, franchise, and a screenshot when possible.
- Severity: **Blocker** cannot continue the required route; **Major** route can continue only with a workaround or data is wrong; **Minor** cosmetic, wording, or low-impact usability issue.
- Do **not** post a device identifier, local-network address, SQLite database, authentication data, personal information, or unreviewed save/debug files publicly.

## Facilitator release check

- [ ] Build identity matches the distributed package or URL.
- [ ] Backend is Ready from the tester device/network.
- [ ] Exact-package clean install and launch passed.
- [ ] Guided route and save/reload/reset passed on the exact package.
- [ ] Known limitation is current.
- [ ] Private bug-report destination is active.
- [ ] Stage 3 running screenshots are captured from the exact configured package.
- [ ] Kyle has explicitly approved starting the pilot.

**UI status:** `UI Review Pending` until Kyle approves Stage 3 implemented evidence.