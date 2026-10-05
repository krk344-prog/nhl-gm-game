# Technical Alpha Endpoint Failure Triage

Use this record only when `scripts/qualify_alpha_endpoint.py` or the exact-package route detects a tester-reachability failure. Keep completed records private when they contain endpoint, device, network, save, database, or raw-log details.

## Build and session identity

- UTC date/time:
- Facilitator initials:
- PR head commit:
- Package SHA-256:
- Endpoint class: `private-lan` / `approved-hosted` / `other-approved`
- Qualification attempt number:
- Last confirmed route checkpoint:

## Failure classification

Select exactly one primary classification.

- [ ] `STARTUP` — authoritative backend did not become healthy.
- [ ] `REACHABILITY` — backend was healthy locally but unavailable from the tester device.
- [ ] `CONTINUITY` — endpoint failed during the qualification observation window.
- [ ] `SEASON_CONTEXT` — health passed but the configured season context was missing, invalid, or mismatched.
- [ ] `PACKAGE_IDENTITY` — installed package, commit, checksum, or embedded endpoint did not match the approved build record.
- [ ] `RECOVERY` — service returned, but franchise, game day, save, or route state did not reconcile.
- [ ] `PRIVACY_EVIDENCE` — required evidence could not be shared or stored safely.
- [ ] `UNKNOWN` — cause is not yet bounded; stop the session and escalate.

## Reproduction boundary

- First failing command or route step:
- Expected result:
- Privacy-safe observed result:
- Failure timestamp:
- Previous successful check timestamp:
- Reproduced once after a clean retry: `yes` / `no` / `not attempted`
- Raw evidence location (private reference only):

## Recovery action

Select one bounded action before retrying.

- [ ] Restart the authoritative launcher without changing the endpoint.
- [ ] Re-run endpoint selection and qualification; do not reuse the previous configured package.
- [ ] Rebuild the APK because endpoint or source identity changed.
- [ ] Reinstall and relaunch the exact verified APK.
- [ ] Restore the last confirmed save checkpoint and reconcile franchise plus game day.
- [ ] Stop testing and escalate; no safe bounded recovery is available.

Owner:
Target completion time:

## Retry decision

A retry is permitted only when all applicable identity and continuity checks can be repeated.

- [ ] Authoritative backend health passes.
- [ ] Season context matches the approved Alpha configuration.
- [ ] Endpoint completes the required continuity observation.
- [ ] Package commit, checksum, build type, and embedded endpoint match.
- [ ] Tester device reaches the same qualified backend.
- [ ] Franchise and game-day state reconcile with the last confirmed checkpoint.
- [ ] No unresolved Blocker or Major affects the required route.

Decision: `RETRY AUTHORIZED` / `NO-GO`
Decision owner:
Decision timestamp:

## Public issue summary

Post only this redacted summary to issue #6 when useful:

- Failure classification:
- Affected gate item:
- Recovery outcome: `recovered` / `still blocked`
- Build identity remained valid: `yes` / `no`
- Next owner and bounded action:

Do not post endpoint addresses, device identifiers, authentication material, saves, databases, private file paths, or unreviewed raw logs.
