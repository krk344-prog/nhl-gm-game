# Technical Alpha Packaged-Build Evidence Contract

This contract defines the minimum evidence required to claim that a Technical Alpha Android package completed an equivalent packaged-build smoke test. It supplements, but does not replace, the physical-device procedure in `docs/technical_alpha_pilot_guide.md`.

## Package identity

Evidence is valid only when all artifacts come from the same workflow run and exact PR #13 head commit. The record must include:

- release APK artifact name and commit SHA;
- APK or artifact digest;
- emulator-smoke artifact name and matching commit SHA;
- configured API base URL/build identity record;
- confirmation that `assets/index.android.bundle` exists and is non-empty.

A screenshot from a different commit, debug build, Expo development client, or previously installed package is not acceptable.

## Equivalent-device smoke requirements

The independent Android emulator job must:

1. download the exact release APK produced by the build job;
2. install that APK successfully on a supported Android API level;
3. launch package `com.krk344.nhlgmgame` through its launcher intent;
4. confirm the application process remains alive after launch;
5. capture a non-empty screenshot from the running packaged application;
6. upload the screenshot and launch diagnostics even when later validation fails.

The build and emulator jobs must remain separate so emulator instability cannot suppress a verified distributable APK.

## Tester-facing launch requirement

Before a human tester begins franchise setup, the facilitator must show or supply one concise session card containing:

- build commit;
- supported device/Android requirement;
- backend reachability status;
- fictional-league and 82-game test-schedule disclosure;
- ordered smoke route;
- stop/report instruction when connection, persistence, roster integrity, standings, trade history, or reset behavior fails.

This is an original early-test usability requirement: the tester should be able to identify the build, understand the simulation boundary, and know the next required action without consulting developer tooling.

## Approval boundary

A green equivalent-device smoke proves package production, installation, launch, process survival, and screenshot capture. It does not prove that a tester can reach a facilitator-hosted backend, complete the guided gameplay route, or preserve a save on a physical device.

The Technical Alpha gate therefore remains pending until the exact configured APK completes the physical-device procedure, private route record, redacted public summary, and Stage 3 running-screen capture. Implemented screens remain `UI Review Pending` until Kyle approves them.
