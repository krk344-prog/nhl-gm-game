# Cycle 213 — Technical Alpha execution checkpoint

## Scope

Broad feature development remains frozen. Draft PR #13 (`agent/alpha-rules-integration-v1`) remains the sole authoritative Technical Alpha integration lane and must not be merged or used to start the pilot without Kyle's explicit approval.

## Required workstreams

- **NHL Operations:** Treat the Alpha trade flow as workflow/persistence validation only; it does not claim complete NHL contract, cap, waiver, retention, or CBA transaction realism.
- **Competing Games:** Early-test onboarding must preserve completed setup and present one authoritative next action when a readiness check fails.
- **Coding:** Add this reversible execution checkpoint only; do not change gameplay, persistence schema, architecture, packaging behavior, or production UI without an observed Alpha defect.
- **Testing:** Entering head `336dd506253403c619f75e497876b728b9c49be8` passed Alpha validation run `34096278328`.
- **UI/UX:** Preserve the approved Stage 2 Team-Branded Command Center. Implemented screens remain `UI Review Pending` until exact-candidate Stage 3 evidence is captured and Kyle approves it.

## Exit-gate execution order

1. qualify one stable tester-reachable endpoint;
2. build the exact endpoint-configured APK from PR #13;
3. verify package, commit, endpoint, build type, and checksums;
4. install and launch that exact APK on one supported physical Android device;
5. execute New Game → franchise selection → advance day → roster → standings → trade → save → reload → reset;
6. produce the private device-smoke record and privacy-safe public summary;
7. capture Stage 3 screenshots from that exact candidate;
8. present the completed gate to Kyle for approval.

Do not substitute pre-pilot tester-session evidence for steps that must be completed before Kyle authorizes the pilot.
