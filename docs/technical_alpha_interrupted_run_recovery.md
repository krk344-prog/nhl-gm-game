# Technical Alpha Interrupted-Run Recovery

Use this procedure when CI, packaging, endpoint qualification, installation, launch, route validation, persistence validation, reset validation, or Stage 3 capture is cancelled or interrupted.

The recovery rule is fail-closed: an interrupted step is not evidence of success, and evidence from different commits, APKs, endpoints, devices, or sessions must not be combined.

## Facilitator recovery sequence

1. **Stop the current evidence session.** Mark the interrupted step `incomplete`; do not infer pass/fail from partial output.
2. **Record the last trusted identity.** Capture the PR number, branch, commit SHA, CI run ID, APK SHA-256, package ID, build type, endpoint class, and anonymous device/tester code that were active before interruption.
3. **Classify the interruption.** Use exactly one category: `ci_cancelled`, `endpoint_unavailable`, `build_interrupted`, `artifact_verification_failed`, `install_interrupted`, `launch_interrupted`, `route_interrupted`, `persistence_interrupted`, `reset_interrupted`, or `capture_interrupted`.
4. **Invalidate dependent evidence.** Any step after the interruption becomes `not_run`. If commit, APK checksum, package, build type, or endpoint changes, invalidate the entire device and Stage 3 evidence package.
5. **Re-establish prerequisites.** Require green current-head CI, a qualified tester-reachable endpoint, a clean configured build, successful artifact verification, and exact-package install/launch before resuming gameplay evidence.
6. **Restart at the earliest invalid step.** Do not skip forward. Route validation must still cover new game, franchise selection, advance day, roster, standings, trade, save, reload, and reset.
7. **Preserve disclosure.** The Technical Alpha remains an eight-franchise fictional environment with an 82-game test schedule; it is not an official NHL schedule or licensed production data set. Reset is expected to reconcile the save to Day 1.
8. **Preserve UI approval state.** Stage 2 approvals remain unchanged. All implemented screenshots remain `UI Review Pending` until Kyle explicitly approves Stage 3/Stage 4 evidence.
9. **Protect private data.** Public evidence must not include endpoint addresses, device serials, tester identities, credentials, databases, save paths, or raw logs.
10. **Apply no-go rules.** Any unresolved Blocker, relevant Major defect, identity mismatch, incomplete required route, persistence mismatch, reset mismatch, or missing privacy review keeps the pilot blocked.

## Required recovery record

```text
interruption_category:
interrupted_step:
last_trusted_commit:
ci_run_id:
apk_sha256:
package_id: com.krk344.nhlgmgame
endpoint_class:
anonymous_device_code:
invalidated_steps:
restart_step:
privacy_reviewed: false
ui_status: UI Review Pending
pilot_authorized_by_kyle: false
merge_authorized_by_kyle: false
```

## Tester-facing usability requirement

After an interruption, the facilitator must give the tester one plain-language status message: what stopped, whether progress was saved, and the single next action. The message must not expose technical identifiers or imply that the interrupted session passed.

## Exit condition

Recovery is complete only when the exact current-head package has a continuous, privacy-reviewed evidence chain from endpoint qualification through install, launch, full gameplay route, save/reload, reset, and required Stage 3 captures. Pilot start and PR merge remain separate Kyle approval gates.
