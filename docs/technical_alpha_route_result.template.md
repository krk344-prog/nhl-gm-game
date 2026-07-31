# NHL GM Technical Alpha — Route Result Record

> Complete one copy per tester session. Keep the unredacted record private when it contains device, network, save, or debug details.

## Session identity

- **Commit:** `[FULL_COMMIT_SHA]`
- **Package or URL:** `[APK_FILENAME_OR_BROWSER_URL]`
- **Package checksum (APK only):** `[SHA256]`
- **Anonymous tester ID:** `[TESTER_ID]`
- **Facilitator:** `[INITIALS]`
- **Started:** `[DATE_TIME]`
- **Ended:** `[DATE_TIME]`

## Preconditions

- [ ] Exact package or URL matches the launch card.
- [ ] Backend is reachable from the tester device and network.
- [ ] Clean install or clean browser session completed.
- [ ] Tester understands reset returns the save permanently to Day 1.
- [ ] Private bug-report destination is available.

## Guided route evidence

Record **Pass**, **Fail**, or **Not run** for every step. A failed step must reference a private defect ID.

| Step | Result | Evidence or defect ID |
|---|---|---|
| New Game opens | `[RESULT]` | `[EVIDENCE]` |
| Fictional franchise selection persists | `[RESULT]` | `[EVIDENCE]` |
| Advance at least ten calendar days | `[RESULT]` | `[EVIDENCE]` |
| Roster loads for selected franchise | `[RESULT]` | `[EVIDENCE]` |
| Standings reconcile after advancement | `[RESULT]` | `[EVIDENCE]` |
| Likely accepted trade completes | `[RESULT]` | `[EVIDENCE]` |
| Likely rejected trade is rejected clearly | `[RESULT]` | `[EVIDENCE]` |
| Both attempts appear in Trade History | `[RESULT]` | `[EVIDENCE]` |
| Save, close, and reload preserves state | `[RESULT]` | `[EVIDENCE]` |
| Debug report generates | `[RESULT]` | `[EVIDENCE]` |
| Reset returns the save to Day 1 | `[RESULT]` | `[EVIDENCE]` |

- **Final game day before reset:** `[GAME_DAY]`
- **Post-reload franchise:** `[FRANCHISE]`
- **Post-reload game day:** `[GAME_DAY]`

## Outcome

- **Overall route result:** `[PASS | FAIL | INCOMPLETE]`
- **Highest severity found:** `[NONE | MINOR | MAJOR | BLOCKER]`
- **Private defect IDs:** `[IDS_OR_NONE]`
- **Tester-accessible build confirmed:** `[YES | NO]`

A session is **PASS** only when every guided route row is Pass, build identity is exact, and no Blocker or unresolved Major defect affects the required route.

## Public-safe summary fields

Only these fields may be copied into issue #6 without additional review:

- commit;
- anonymous tester ID;
- route start and end time;
- overall route result;
- highest severity;
- final game day;
- redacted defect IDs;
- confirmation that exact-package install, launch, save/reload, and reset were exercised.

Do not publish device identifiers, local-network addresses, authentication data, databases, save files, or unreviewed debug output.

## UI evidence

- **Stage 3 screenshots captured from this exact package:** `[YES | NO]`
- **Screenshot references:** `[PRIVATE_OR_REDACTED_REFERENCES]`
- **UI status:** `UI Review Pending` until Kyle approves implemented evidence.
