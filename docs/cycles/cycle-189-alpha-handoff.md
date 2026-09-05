# Cycle 189 — Technical Alpha handoff checkpoint

## Scope
This checkpoint is documentation-only and does not change gameplay, save data, packaging architecture, or approved UI direction. PR #13 remains the sole Technical Alpha integration lane.

## NHL Operations disclosure
The controlled Alpha uses an eight-team fictional league and an 82-game test schedule. Testers must not treat its schedule structure, club identities, roster data, or results as a representation of the official 2026–27 NHL season.

## Early-test usability requirement — one visible next action
At every facilitator gate, present exactly one next executable action and preserve the evidence from already-passed gates. A failure must identify the failing subsystem without making successful prerequisite evidence disappear. This prevents a tester/facilitator from guessing whether to rebuild, reconnect a device, restart the backend, or rerun the entire sequence.

Acceptance criteria:
- readiness output identifies the next executable handoff action only after all prerequisites pass;
- a failed gate names the failed subsystem and directs the facilitator to rerun that gate/readiness rather than improvising;
- prior successful evidence remains available for diagnosis;
- no private ADB serial or tester-network detail is copied into public evidence.

## Physical-device execution checkpoint
Before the gate can be marked ready for Kyle approval, evidence must show this exact sequence on the pilot candidate:

1. stable tester-reachable API endpoint selected and backend preflight passed;
2. execution readiness passed for the clean PR #13 head;
3. exact configured standalone APK built and artifact verification passed;
4. certified supported Android device matched at handoff;
5. exact APK installed and launched;
6. guided new-game/franchise/advance-day/roster/standings/trade/save/reload/reset smoke passed;
7. privacy-safe public smoke summary produced;
8. Stage 3 screenshots captured from the exact candidate.

## UI/UX implemented-state specification
No production UI changes are authorized by this checkpoint. Preserve the approved Stage 2 Team-Branded Command Center. Until Stage 3 evidence is captured and Kyle approves it, implemented screens remain `UI Review Pending`.

For facilitator-facing readiness state, use a compact progression such as `Source Ready → Device Ready → Endpoint Ready → Build/Install → Smoke`, with text labels and not color alone. On failure, keep completed steps visible and place the single recovery action adjacent to the failed step.

## Validation note
Cycle 188 head CI is the baseline prerequisite for this checkpoint. The next execution cycle should prioritize the real endpoint/device chain over additional speculative validator hardening.
