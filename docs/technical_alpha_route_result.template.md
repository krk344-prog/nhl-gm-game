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
- [ ] Backend health check time and result were recorded below.
- [ ] Clean install or clean browser session completed.
- [ ] Tester understands reset returns the save permanently to Day 1.
- [ ] Private bug-report destination is available.

## Backend continuity evidence

Record the same tester-visible endpoint before the route and immediately after save/reload. Do not copy a private LAN address into the public issue report.

| Checkpoint | Time | Result | Private evidence or defect ID |
|---|---|---|---|
| Before New Game | `[DATE_TIME]` | `[PASS | FAIL]` | `[EVIDENCE]` |
| After save, close, and reload | `[DATE_TIME]` | `[PASS | FAIL]` | `[EVIDENCE]` |

A changed endpoint, failed post-reload health check, or backend restart that loses required state makes the session **FAIL** and must reference a private defect ID.

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

## Interruption and recovery evidence

Use this section whenever the tester loses connectivity, backgrounds the app, closes the browser, or the facilitator must restart the backend. Do not silently resume a disrupted route.

- **Interruption occurred:** `[YES | NO]`
- **Interruption time:** `[DATE_TIME_OR_NA]`
- **Last confirmed completed route step:** `[STEP_OR_NA]`
- **Tester-visible message or state:** `[PRIVATE_SUMMARY_OR_NA]`
- **Recovery action:** `[RECONNECT | RELAUNCH | RELOAD_SAVE | RESTART_ROUTE | NOT_APPLICABLE]`
- **Recovery result:** `[PASS | FAIL | NOT_APPLICABLE]`
- **Private evidence or defect ID:** `[EVIDENCE_OR_NA]`

A session with an interruption may pass only when the exact build remains installed, backend identity is unchanged, the saved franchise and game day reconcile after recovery, and the remaining guided route completes without an unresolved Major or Blocker. Otherwise mark the route **FAIL** or **INCOMPLETE** rather than restarting evidence mid-session.

## Outcome

- **Overall route result:** `[PASS | FAIL | INCOMPLETE]`
- **Highest severity found:** `[NONE | MINOR | MAJOR | BLOCKER]`
- **Private defect IDs:** `[IDS_OR_NONE]`
- **Tester-accessible build confirmed:** `[YES | NO]`

A session is **PASS** only when both backend-continuity checkpoints and every guided route row are Pass, build identity is exact, any interruption satisfies the recovery contract, and no Blocker or unresolved Major defect affects the required route.

## Public-safe summary fields

Only these fields may be copied into issue #6 without additional review:

- commit;
- anonymous tester ID;
- route start and end time;
- overall route result;
- highest severity;
- final game day;
- redacted defect IDs;
- confirmation that the backend passed both continuity checkpoints;
- confirmation that exact-package install, launch, save/reload, and reset were exercised;
- whether an interruption occurred and whether recovery passed, without private device or network details.

Do not publish device identifiers, local-network addresses, authentication data, databases, save files, or unreviewed debug output.

## UI evidence

- **Stage 3 screenshots captured from this exact package:** `[YES | NO]`
- **Screenshot references:** `[PRIVATE_OR_REDACTED_REFERENCES]`
- **UI status:** `UI Review Pending` until Kyle approves implemented evidence.
