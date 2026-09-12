# Technical Alpha Pilot Evidence Index

This index is the single facilitator-facing map for the exact package proposed for the controlled 3–5 person Technical Alpha. It does not replace the underlying validators or private evidence records. It prevents evidence from different commits, endpoints, packages, devices, or sessions from being combined into a false pass.

## Package identity

- PR: `#13`
- Branch: `agent/alpha-rules-integration-v1`
- Commit SHA: `<40-character SHA>`
- CI run: `<run ID and URL>`
- Build type: `standalone-release-apk` or approved browser package
- APK filename or browser deployment identifier: `<value>`
- SHA-256: `<value>`
- Android package: `com.krk344.nhlgmgame`
- Endpoint class: `<private LAN / approved hosted test endpoint>`
- Endpoint qualification record: `<private record reference>`
- Test-session identifier: `<anonymous session code>`

Any change to the commit, endpoint, package, checksum, build type, or deployment invalidates all downstream entries and requires a new index.

## Readiness evidence

| Gate | Required evidence | Status | Evidence reference | Owner |
|---|---|---|---|---|
| Authoritative launch path | `python scripts/start_dev.py` or recorded approved browser launch path | Pending |  | Backend Hosting |
| Green current-head CI | Successful Alpha validation for the exact commit | Pending |  | CI/Automation |
| Endpoint qualification | Minimum 15-minute uninterrupted health and API observation | Pending |  | Backend Hosting |
| Configured package | Exact endpoint embedded and artifact verified | Pending |  | Release Engineering |
| Installation | Exact APK installed on one supported Android device | Pending |  | Android Packaging |
| Application launch | Package process confirmed and first actionable screen visible | Pending |  | Device Readiness |
| New game | New session created without legacy-save contamination | Pending |  | Testing |
| Franchise selection | Selected franchise persists across route transitions | Pending |  | Testing |
| Advance day | Day advances and scheduled simulation resolves | Pending |  | Testing |
| Roster | Controlled-team roster loads and filters/actions remain usable | Pending |  | Testing |
| Standings | Standings reconcile after day advancement | Pending |  | Testing |
| Trade | One bounded accepted/rejected/blocked trade path recorded | Pending |  | Testing |
| Save and reload | State survives application/backend restart | Pending |  | Testing |
| Reset | Reset intentionally returns the fictional Alpha to Day 1 | Pending |  | Testing |
| Debug output | Reproducible privacy-reviewed debug report generated | Pending |  | Defect Triage |
| Stage 3 captures | Nine exact-package implemented-state captures complete | Pending |  | UI/UX |
| Accessibility | Keyboard/focus, readable type, touch target, zoom, non-color status review | Pending |  | Accessibility |
| Privacy review | Public summary contains no endpoint, identity, serial, credential, save, DB, or raw-log data | Pending |  | Security/Privacy |
| Defect gate | Zero open Blockers and zero relevant unresolved Major defects | Pending |  | Defect Triage |
| Kyle Alpha approval | Explicit approval recorded after all evidence passes | Blocked |  | Kyle |
| Pilot start approval | Separate explicit approval recorded | Blocked |  | Kyle |
| PR merge approval | Separate explicit approval recorded | Blocked |  | Kyle |

Allowed status values are `Pass`, `Pending`, and `Blocked`. A failed validation remains `Blocked` until corrected and rerun against a new or unchanged exact package as appropriate.

## NHL Operations disclosure

The Technical Alpha uses eight fictional franchises and an 82-game test schedule. It is not the official NHL schedule or licensed production data. The reset scenario intentionally returns the save to Day 1. Testers must see and acknowledge these limitations before beginning the controlled route.

## Competing-games usability requirement

Before any coaching, the facilitator records the tester's first interpretation, first attempted action, whether the next step was independently discoverable, and the highest-friction moment. Installation or launch alone is not successful onboarding; the tester must reach a stable actionable state and understand the next permitted action.

## UI Preview / Approval

The approved Stage 2 team-branded direction remains preserved. All implemented screens and all nine Stage 3 captures remain **UI Review Pending** until Kyle explicitly approves the implemented state. Captures must come from the exact package and session identified above; mockups, emulator images, and screenshots from another build cannot satisfy this gate.

Required Stage 3 states:

1. launch / initial actionable state;
2. new game;
3. franchise selection;
4. game center after advancing a day;
5. roster;
6. standings;
7. trade result;
8. save/reload confirmation;
9. reset / Day 1 confirmation.

## Go/no-go rule

The gate may be marked **Ready for Kyle Approval** only when every non-approval row is `Pass`, the evidence reconciles to this exact package/session, and the privacy-safe public summary is complete. Do not begin the pilot and do not merge PR #13 without Kyle's separate explicit approvals.
