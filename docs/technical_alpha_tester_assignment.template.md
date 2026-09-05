# Technical Alpha Tester Assignment Template

Use this private facilitator record for one controlled 3–5 person Technical Alpha session. Do not publish tester names, emails, device identifiers, local endpoint addresses, save files, database paths, credentials, or raw logs.

## Exact package identity

- PR: `#13`
- Commit SHA: `<40-character SHA>`
- APK SHA-256: `<64-character SHA-256>`
- Android package: `com.krk344.nhlgmgame`
- Build type: `release`
- Endpoint class: `<private-lan | approved-hosted>`
- Endpoint qualification: `<pass | fail>`
- Qualification duration: `<minutes; minimum 15 uninterrupted>`
- Installed and launched: `<yes | no>`

Any package rebuild, endpoint change, commit change, or checksum change invalidates this record and requires a new session assignment.

## Alpha disclosure acknowledgement

Each tester must acknowledge before starting:

- the Alpha uses eight fictional franchises and an 82-game test schedule;
- it is not an official NHL roster, schedule, branding, or rules representation;
- reset intentionally returns the current test save to Day 1;
- unfinished systems may be visible but disabled or labeled as limited;
- all feedback should describe observed behavior, not assumed official NHL behavior.

Record acknowledgement using anonymous tester codes only.

## Roles and route ownership

| Tester code | Primary route | Secondary focus | Device class | Disclosure acknowledged | Started | Completed |
|---|---|---|---|---|---|---|
| T01 | New game → franchise selection → advance day | Onboarding clarity | `<class>` | `<yes/no>` | `<time>` | `<time>` |
| T02 | Roster → standings → trade | Information hierarchy | `<class>` | `<yes/no>` | `<time>` | `<time>` |
| T03 | Save → app close/relaunch → reload | Persistence confidence | `<class>` | `<yes/no>` | `<time>` | `<time>` |
| T04 | Reset → Day 1 reconciliation | Recovery and destructive-action clarity | `<class>` | `<yes/no>` | `<time>` | `<time>` |
| T05 | Full route observer | Accessibility and defect reproduction | `<class>` | `<yes/no>` | `<time>` | `<time>` |

Use three rows for a three-person session, four for a four-person session, or all five for a five-person session. Every required route step must have one named anonymous owner and one backup observer.

## Required route evidence

Mark each step only after the assigned tester completes it on the exact installed package.

| Step | Primary tester | Backup observer | Result | Evidence reference | Defect reference |
|---|---|---|---|---|---|
| Application launch | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| New game | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Franchise selection | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Advance day | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Roster | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Standings | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Trade | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Save and close | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Reload and reconcile | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |
| Reset to Day 1 | `<code>` | `<code>` | `<pass/fail>` | `<private ref>` | `<ID or none>` |

## Test-facing usability observations

For each tester, record exactly one highest-friction moment and one clearest confidence-building moment.

| Tester code | Highest-friction moment | Severity | Clearest confidence-building moment | Suggested reversible improvement |
|---|---|---|---|---|
| T01 | `<observation>` | `<minor/major/blocker>` | `<observation>` | `<suggestion>` |
| T02 | `<observation>` | `<minor/major/blocker>` | `<observation>` | `<suggestion>` |
| T03 | `<observation>` | `<minor/major/blocker>` | `<observation>` | `<suggestion>` |
| T04 | `<observation>` | `<minor/major/blocker>` | `<observation>` | `<suggestion>` |
| T05 | `<observation>` | `<minor/major/blocker>` | `<observation>` | `<suggestion>` |

A facilitator must not coach around unclear product states before recording the tester's first interpretation. Assistance may be provided afterward and must be noted.

## UI Preview / Approval evidence

Stage 2 approvals remain preserved. Actual implemented screens remain `UI Review Pending` until Kyle approves Stage 3 and Stage 4 evidence.

Required Stage 3 captures from the exact package:

1. connection or launch state;
2. franchise selection;
3. dashboard after advance day;
4. roster;
5. standings;
6. trade flow;
7. reload confirmation;
8. reset confirmation and Day 1 state;
9. one non-ideal recovery state.

Each capture must have readable text, no private endpoint or device data, non-color status cues, unclipped content, and a clear next action.

## Defect and no-go rules

- Any Blocker stops the session.
- Any unresolved Major affecting launch, the required route, persistence, reset, package identity, privacy, or accessibility blocks pilot readiness.
- Evidence from different commits, APK checksums, packages, endpoints, or sessions cannot be combined.
- A route step without an assigned tester, backup observer, result, and evidence reference is incomplete.
- Kyle approval must remain unrecorded until he explicitly grants it.

## Facilitator closeout

- Required route complete: `<yes/no>`
- Save/reload reconciled: `<yes/no>`
- Reset reconciled to Day 1: `<yes/no>`
- Nine Stage 3 captures complete: `<yes/no>`
- Privacy review passed: `<yes/no>`
- Accessibility review passed: `<yes/no>`
- Open Blockers: `<count>`
- Open Majors: `<count>`
- Public redacted summary prepared: `<yes/no>`
- Recommendation: `<no-go | ready-for-Kyle-approval>`
- Kyle pilot approval: `not granted`
- Kyle merge approval: `not granted`
