# Technical Alpha Endpoint Qualification Record

Use this record before building or distributing the configured Technical Alpha APK. The completed record may contain private network details and must remain in the approved private evidence location. Only the redacted outcome may be posted publicly.

## Build and session identity

- Qualification date/time:
- Facilitator:
- PR: `#13`
- Source commit:
- Package ID: `com.krk344.nhlgmgame`
- Planned tester cohort: 3–5 people
- Planned test window:

## Endpoint identity — private

- Endpoint class: private LAN / approved hosted HTTPS
- Exact API base URL ending in `/api/v1`:
- Backend source commit:
- Host device or service owner:
- Expected availability window:
- Restart/recovery owner:

Do not place endpoint addresses, credentials, device identifiers, database files, saves, or raw logs in public issue comments.

## Qualification checks

Record **Pass**, **Fail**, or **Not run**, with UTC or local timestamp and concise evidence reference.

| Check | Result | Time | Evidence / notes |
|---|---|---|---|
| Endpoint is non-loopback and reachable from the facilitator device |  |  |  |
| `GET /api/v1/health` succeeds from the facilitator network |  |  |  |
| Endpoint remains reachable for 15 uninterrupted minutes |  |  |  |
| Backend restart procedure is documented and rehearsed |  |  |  |
| Restart preserves or intentionally restores the expected test database |  |  |  |
| Exact source commit is recorded before APK build |  |  |  |
| Configured APK metadata matches endpoint and source commit |  |  |  |
| Exact APK reaches health before New Game |  |  |  |
| Exact APK reaches health after save, close, and reload |  |  |  |
| Endpoint remains reachable from the intended tester network class |  |  |  |
| No credentials or private identifiers appear in tester-facing UI |  |  |  |

## Stop conditions

Qualification is **NO-GO** when any of the following is true:

- the endpoint is loopback-only or cannot be reached by the intended device;
- health is intermittent or unavailable during the observation window;
- source commit, endpoint identity, or APK metadata cannot be reconciled;
- the backend cannot be recovered by the named owner;
- a restart silently changes or loses the expected save state;
- tester-facing output exposes credentials, device identifiers, or private network details.

## Outcome

- Qualification result: `GO FOR CONFIGURED BUILD` / `NO-GO`
- Residual risks:
- Mitigations:
- Release Engineering sign-off:
- Backend Hosting sign-off:
- Testing sign-off:

A `GO FOR CONFIGURED BUILD` result permits creation of the exact configured APK only. It does not authorize the 3–5 person pilot and does not authorize merging PR #13. Kyle’s explicit approvals remain separate gates.

## Public redacted summary

- Source commit:
- Endpoint class only: private LAN / approved hosted HTTPS
- Qualification result:
- Observation duration:
- Pre-build health: Pass / Fail
- Post-reload health: Pass / Fail
- Recovery rehearsal: Pass / Fail
- Privacy review: Pass / Fail
- Remaining blocker:
