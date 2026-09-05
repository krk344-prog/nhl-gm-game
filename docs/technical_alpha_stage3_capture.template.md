# Technical Alpha Stage 3 Capture Record

Use this record only for screenshots captured from the exact configured Technical Alpha package that completed the controlled device route. This record supports UI review; it does not authorize the pilot or merge.

## Build and session identity

- Commit SHA:
- APK file name:
- APK SHA-256:
- Application package: `com.krk344.nhlgmgame`
- Build type:
- Endpoint class: private LAN / approved hosted test endpoint
- Anonymous tester ID:
- Device class and Android version (private record only):
- Route-result record reference:
- Capture date and time:

## Required preconditions

Mark each item `PASS`, `FAIL`, or `NOT RUN`.

- [ ] Artifact identity matches the installed package.
- [ ] Backend qualification passed for the same endpoint class.
- [ ] Guided route passed through new game, franchise selection, advance day, roster, standings, trade, save, reload, and reset.
- [ ] Save/reload restored the expected franchise and game-day state.
- [ ] Reset was intentionally executed and returned the fictional Alpha save to Day 1.
- [ ] No unresolved Blocker or Major affects the captured flow.
- [ ] Private device-smoke evidence exists and has a privacy-safe public summary.

A failed or not-run precondition makes the Stage 3 set incomplete.

## Mandatory screenshots

Capture readable, uncropped screenshots from the running package. Do not substitute mockups, emulator design previews, or screenshots from a different commit.

| ID | Screen/state | Required evidence | Result | Private file reference |
|---|---|---|---|---|
| S3-01 | Launch or connection state | App identity and explicit text-backed backend state |  |  |
| S3-02 | New Game / franchise selection | Fictional-team disclosure and selected-franchise state |  |  |
| S3-03 | Dashboard after advance day | Current game day, recent result or next action, and non-color status cues |  |  |
| S3-04 | Roster | Readable player grouping/filter state and controlled-franchise identity |  |  |
| S3-05 | Standings | Eight fictional teams, current records, and test-season context |  |  |
| S3-06 | Trade | Selected partner/assets, decision feedback, and recoverable error handling |  |  |
| S3-07 | Reloaded save | Reconciled franchise and game-day state after close/relaunch |  |  |
| S3-08 | Reset confirmation/result | Irreversible-reset warning and verified Day 1 result |  |  |
| S3-09 | Non-ideal state | Offline, backend interruption, validation error, or blocked action with recovery guidance |  |  |

## UI/UX review criteria

For each captured state, record `PASS`, `FAIL`, or `NOT ASSESSED`.

- [ ] One clear primary action is visible.
- [ ] Status and severity do not rely on color alone.
- [ ] Text remains readable without clipping at the tested viewport.
- [ ] Touch targets are distinct and do not overlap.
- [ ] Loading, disabled, error, and recovery states are explicit.
- [ ] The user can identify the controlled franchise and current game day.
- [ ] Dense roster, standings, and trade information remains scannable.
- [ ] The eight-team, 82-game fictional Alpha limitation is not presented as official NHL data.
- [ ] No official NHL marks, licensed player imagery, credentials, endpoint addresses, device identifiers, or raw private logs appear.

## Clean-room usability requirement

Early management-game testing must preserve orientation after every major action. Each captured post-action state must show or make immediately reachable: (1) what changed, (2) the current franchise/day context, and (3) the next valid action. This is an original test requirement and must not copy proprietary layouts, text, or assets from competing games.

## Deviations from approved Stage 2 direction

List each deliberate deviation from an approved Stage 2 artifact. Use `None` only after direct comparison.

| Screen | Approved artifact/reference | Deviation | Reason | Severity | Owner |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Accessibility and responsive observations

- Tested viewport/orientation:
- Text scaling or zoom used:
- Keyboard/switch-access observations, when applicable:
- Screen-reader label observations, when applicable:
- Contrast or focus concerns:
- Touch-target concerns:
- Clipping, overflow, or horizontal-scroll concerns:

## Privacy-safe public summary

Public reporting may include:

- exact commit SHA and redacted artifact identity;
- screenshot IDs and pass/fail status;
- UI defects and severity;
- whether the route, persistence, reset, and recovery states passed;
- whether the set matches the approved Stage 2 direction.

Keep private:

- endpoint addresses;
- device serials and unique identifiers;
- local paths, credentials, saves, databases, and raw logs;
- screenshots containing notifications or unrelated personal information.

## Stage 3 decision

Select exactly one:

- [ ] `COMPLETE — UI Review Pending`: all preconditions and mandatory captures passed; submit to Kyle for review.
- [ ] `INCOMPLETE — RECAPTURE REQUIRED`: one or more required captures or checks failed.
- [ ] `NO-GO — BLOCKER/MAJOR`: a route, privacy, package-identity, or usability defect prevents submission.

This record never constitutes Stage 4 approval. The screen remains `UI Review Pending` until Kyle explicitly approves the implemented evidence. Pilot start and merge remain separately prohibited without Kyle's explicit approval.

## Sign-off

- Capture owner:
- UI/UX reviewer:
- Testing reviewer:
- Privacy reviewer:
- Release reviewer:
- Open defects and links:
