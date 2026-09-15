# Technical Alpha Facilitator Start Card

Use this card only for the controlled 3–5 person Technical Alpha. It does not authorize the pilot, PR merge, or public distribution.

## Release identity

Before any tester receives access, record the following in the private evidence package and confirm every value matches the approved PR #13 package:

- PR: `#13`
- branch: `agent/alpha-rules-integration-v1`
- commit SHA
- application package: `com.krk344.nhlgmgame`
- build type
- APK SHA-256 or browser deployment identifier
- qualified endpoint class
- evidence-session identifier

Stop immediately if any identity value differs from the artifact, installed application, endpoint qualification record, or test-session record.

## Required preflight order

1. Confirm PR #13 remains draft, open, unmerged, and the sole Alpha integration lane.
2. Confirm the exact commit has a successful Alpha validation workflow run.
3. Select and qualify one tester-reachable endpoint for at least 15 uninterrupted minutes.
4. Build the configured package from a clean PR #13 working tree.
5. Verify the artifact metadata and checksum.
6. Install the exact artifact on one supported Android device, or open the approved browser deployment.
7. Confirm the application launches into a stable actionable state.
8. Create the private session record before gameplay validation begins.

Do not substitute evidence from another commit, endpoint, package, device session, or build.

## Controlled smoke route

Complete the route in this order and retain reproducible evidence for each state:

1. new game
2. franchise selection
3. advance day
4. roster
5. standings
6. trade
7. save
8. reload and continuity confirmation
9. reset and Day 1 reconciliation

A route step is not complete merely because the screen opens. Record the expected state, observed state, pass/fail result, and any defect identifier.

## Tester-observation rule

Before coaching, record for each anonymous tester:

- first interpretation of the screen;
- first attempted action;
- whether the next action was independently discoverable;
- highest-friction moment;
- interruption or recovery message encountered.

Installation alone is not successful onboarding. Success requires a stable, understandable, actionable first state.

## UI Preview / Approval evidence

Capture the nine implemented route states from the exact tested package. Preserve the approved Stage 2 direction and label every implemented screen:

`UI Review Pending`

Do not mark any implemented screen `UI Approved` until Kyle explicitly approves the Stage 3 evidence and grants Stage 4 acceptance.

Capture at least one realistic non-ideal state when available, such as offline, loading, validation error, or dense decision content. Screenshots must not expose endpoint addresses, tester identities, device serials, credentials, local save paths, databases, or raw logs.

## No-go conditions

Stop the session and record `NO-GO` when any of the following occurs:

- commit, checksum, package, endpoint, build type, or session identity mismatch;
- current-head CI is not successful;
- endpoint qualification is incomplete or interrupted;
- application installation or launch is unconfirmed;
- any required route step fails;
- save/reload continuity does not reconcile;
- reset does not return the save to Day 1 as disclosed;
- a Blocker defect is open;
- a relevant Major defect is unresolved;
- Stage 3 evidence comes from a different package or session;
- privacy review fails;
- pilot or merge approval is recorded without Kyle's explicit authorization.

## Alpha disclosure

Tell testers before the session:

- this Alpha uses eight fictional franchises;
- the 82-game test schedule is a simulation fixture, not the official NHL schedule;
- generated ratings, contracts, and identity placeholders are not official league data;
- reset intentionally returns the test save to Day 1;
- unfinished systems and known limitations are expected and should be reported, not inferred as final design decisions.

## Session closeout

At the end of the run:

1. reconcile the private device/session record with the redacted public summary;
2. confirm all evidence belongs to the same exact package and session;
3. list open defects by severity and owner;
4. complete privacy review;
5. leave the gate `Pending` unless every readiness item passes;
6. when every item passes and a tester-accessible build or URL exists, mark the gate `Ready for Kyle approval`;
7. do not start the pilot or merge PR #13 without Kyle's separate explicit approvals.
