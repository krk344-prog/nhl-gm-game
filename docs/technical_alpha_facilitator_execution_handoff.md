# Technical Alpha Facilitator Execution Handoff

This is the authoritative, fail-closed order for producing evidence for the controlled 3–5 person Technical Alpha from draft PR #13.

It does not authorize a pilot or merge. Kyle must explicitly approve each separately.

## Scope and identity

- Integration lane: `agent/alpha-rules-integration-v1`
- Pull request: #13
- Android package: `com.krk344.nhlgmgame`
- Application path: `python scripts/start_dev.py`
- Test environment: eight fictional franchises and an 82-game test schedule; not official NHL schedule or licensed league data
- Evidence rule: endpoint qualification, APK metadata, installed package, route record, and Stage 3 captures must reconcile to the same commit and APK SHA-256.

## Stop conditions

Stop immediately and classify the run as `NO-GO` when any of the following occurs:

1. The checked-out branch is not `agent/alpha-rules-integration-v1`.
2. The working tree is not clean before the configured build.
3. The selected endpoint is loopback, unreachable from the test device, or fails season-context validation.
4. The endpoint cannot complete the required continuity qualification.
5. Artifact verification reports a commit, checksum, package, build-type, or endpoint mismatch.
6. Installation or launch resolves to a package other than `com.krk344.nhlgmgame`.
7. Any required gameplay route step fails: new game, franchise selection, advance day, roster, standings, trade, save, reload, or reset.
8. Persistence does not reconcile after close/reload or interruption recovery.
9. A Blocker or unresolved Major defect affects the required route.
10. Stage 3 evidence fails privacy, accessibility, exact-package, or completeness validation.

A failed step may be retried only after the cause and recovery action are recorded. Rebuilding the APK invalidates evidence from the prior APK.

## Ordered execution

### 1. Freeze source identity

Record:

- PR #13 head commit;
- branch name;
- clean working-tree result;
- local date/time;
- facilitator name.

Do not continue if source identity is ambiguous.

### 2. Start and validate the authoritative application

Launch with:

```bash
python scripts/start_dev.py
```

Confirm the health route and season-context route succeed before selecting an Android endpoint.

### 3. Select and qualify one tester-reachable endpoint

Use the repository endpoint-selection and backend-preflight tools. Then run the continuity qualifier for the full required observation window.

The endpoint is qualified only when:

- it is non-loopback and reachable from the intended device network;
- every health and season-context check passes;
- no restart or continuity failure occurs during the observation window;
- the endpoint class and season are recorded without exposing the private address publicly.

### 4. Produce the configured release APK

Run the branch-local configured build path only after endpoint qualification. The build must regenerate the native Android project cleanly and embed the qualified API route.

Record:

- commit SHA;
- APK SHA-256;
- package name;
- build type;
- endpoint class;
- artifact creation time.

### 5. Verify the artifact before installation

Run the artifact verifier against the exact APK and its metadata. A warning is not a pass. Any mismatch requires a rebuild or corrected evidence before installation.

### 6. Preflight the authorized Android device

Confirm one supported, authorized device is available. Keep serial numbers, private network details, and raw device diagnostics out of public issue comments.

### 7. Install and launch the exact verified APK

Use the guarded installer and launcher. Confirm that `com.krk344.nhlgmgame` is installed and its process remains active.

Do not substitute a development client, Expo Go session, older APK, or differently configured package.

### 8. Complete the guided gameplay route

Use one continuous route record and mark each checkpoint `Pass`, `Fail`, or `Not run`:

1. connection and season context;
2. new game;
3. franchise selection;
4. advance day;
5. roster;
6. standings;
7. trade;
8. save;
9. close and reload;
10. persistence reconciliation;
11. reset with explicit acknowledgment;
12. Day 1 and expected franchise-state verification after reset.

If interrupted, record the last confirmed checkpoint and reconcile build identity, backend identity, franchise, and game day before resuming.

### 9. Capture Stage 3 evidence from the same session/package

Capture the required implemented states:

- connection;
- franchise selection;
- dashboard;
- roster;
- standings;
- trade;
- reload/persistence;
- reset/Day 1;
- one non-ideal or recovery state.

Every capture remains `UI Review Pending` until Kyle approves it. Preserve the approved Stage 2 direction and document deliberate deviations.

### 10. Validate and reconcile all evidence

Run the device-smoke validator, privacy-safe summarizer, Stage 3 validator, and final pilot-readiness reconciler.

The final reconciler must confirm identical commit SHA, APK SHA-256, package, and release build type across all records.

### 11. Prepare the decision record

Mark only one state:

- `NO-GO — Blocked`: any required evidence is missing, mismatched, failed, or affected by a Blocker/Major defect.
- `READY FOR KYLE APPROVAL`: every technical gate is evidenced and a tester-accessible package or URL exists.

`READY FOR KYLE APPROVAL` is not permission to begin the pilot and is not permission to merge.

## Public/private evidence boundary

Public issue reporting may include:

- commit SHA;
- APK checksum;
- package and build type;
- endpoint class, not address;
- route checkpoint outcomes;
- redacted defect summaries;
- privacy-reviewed Stage 3 images;
- final ready/blocked state.

Keep private:

- endpoint addresses;
- device serials and identifiers;
- credentials or tokens;
- saves and databases;
- unreviewed logs and local paths;
- screenshots containing personal or network information.

## Final authorization boundary

After all validators pass, post the reconciled evidence to issue #6 and request Kyle's explicit pilot decision. Keep PR #13 draft and unmerged until Kyle separately approves merge.
