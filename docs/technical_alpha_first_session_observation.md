# Technical Alpha First-Session Observation Record

Use this record for each controlled Technical Alpha tester. It measures whether a tester can understand and begin the game independently before facilitator coaching.

## Release identity

Record these values from the approved exact-package checkpoint before the session begins:

- PR: `#13`
- commit SHA:
- delivery path: Android APK / approved browser deployment
- package or deployment identity:
- APK SHA-256, when applicable:
- endpoint qualification record:
- anonymous tester code:
- session code:

Stop the session if any identity value differs from the active evidence package. Do not combine evidence from different commits, packages, endpoints, installations, or sessions.

## Required pre-test disclosure

Before franchise selection, show and acknowledge all of the following:

- this Technical Alpha contains eight fictional franchises;
- it uses an intentional 82-game test schedule rather than the official NHL schedule;
- generated players, teams, results, ratings, and contracts are simulation data rather than licensed NHL data;
- Reset intentionally returns the simulation to Day 1 and clears the active test save.

Record acknowledgement status without collecting the tester's real name.

## Uncoached onboarding observation

The facilitator must not explain navigation or the next action until the tester requests help or reaches the intervention threshold.

Record:

1. tester's first interpretation of the opening screen;
2. tester's first attempted action;
3. time from launch to a stable actionable screen;
4. time from actionable screen to successful franchise selection;
5. whether the tester independently identified how to advance the day;
6. first point of hesitation or incorrect navigation;
7. highest-friction moment;
8. first help request, if any;
9. facilitator intervention and reason;
10. whether progress remained saved after the intervention.

## Controlled route result

Mark each step `Pass`, `Fail`, or `Not reached` and attach only privacy-reviewed evidence:

- new game
- franchise selection
- advance day
- roster
- standings
- trade
- save
- reload
- reset to Day 1

A route failure, unexplained save-state change, or reset mismatch is a no-go until triaged.

## Test-facing usability acceptance criteria

The first-session experience passes only when:

- release identity is visible or readily available to the facilitator;
- the tester can distinguish the primary action from secondary navigation;
- progress, loading, offline, and error states use plain language and do not rely on color alone;
- a stopped or failed action explains what happened, whether progress was saved, and the next available action;
- required controls remain usable at a 360-pixel viewport and at 200% zoom;
- keyboard focus, screen-reader labels, and touch targets support the tested route;
- no private endpoint, device serial, tester identity, credentials, database, save path, or raw log appears in public evidence.

## UI approval status

All implemented screens remain `UI Review Pending` until Kyle approves Stage 3 evidence and separately grants Stage 4 final acceptance. This observation record does not approve a screen, start the pilot, or authorize a merge.

## Session decision

- route decision: Pass / No-go
- accessibility decision: Pass / No-go
- privacy review: Pass / No-go
- relevant Major defects:
- Blocker defects:
- facilitator initials or anonymous owner code:
- evidence index reference:

Any identity mismatch, Blocker, relevant unresolved Major defect, privacy failure, incomplete required route, persistence mismatch, or reset mismatch produces a no-go.
