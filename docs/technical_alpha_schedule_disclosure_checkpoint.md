# Technical Alpha Schedule Disclosure Checkpoint

## Purpose

Prevent a controlled tester from mistaking the Technical Alpha's fictional league structure for the current NHL schedule or rules implementation.

## Verified limitation

The Technical Alpha intentionally uses eight original fictional franchises and an 82-game test schedule. The official 2026–27 NHL regular season uses 32 clubs and 84 games per club, including 42 home and 42 road games. The Alpha schedule is therefore a gameplay-validation fixture, not a representation of the official 2026–27 NHL scheduling matrix.

Authoritative reference reviewed for this checkpoint:

- NHL schedule release dated July 16, 2026: `https://www.nhl.com/news/nhl-releases-2026-27-regular-season-schedule`

## Required facilitator action

Before `Start Test` is enabled or the guided route begins, the facilitator must confirm that the tester has received this plain-language disclosure:

> This Technical Alpha uses eight fictional franchises and an 82-game test schedule. The official 2026–27 NHL season uses 32 teams and 84 games per club. Schedule structure, ratings, contracts, identities, and outcomes in this build are test data and must not be treated as official NHL data.

Record only an anonymous tester code, acknowledgement status, package commit, APK checksum or browser deployment identifier, and session timestamp. Do not record a tester name, device serial, private endpoint, credentials, database path, save path, or raw log in the public coordination issue.

## Test-facing usability requirement

The disclosure must be visible before franchise selection and satisfy all of the following:

- use text rather than color alone;
- fit at a 360-pixel viewport without horizontal scrolling;
- keep the build identity and `Start Test` action visible;
- provide a short expandable explanation rather than a blocking wall of text;
- remain available from the Test Build information surface after acknowledgement;
- preserve the tester's first interpretation before facilitator coaching.

Implemented screens remain `UI Review Pending` until exact-package Stage 3 evidence is captured and Kyle approves the implementation.

## Pass / fail rule

**Pass:** the exact-package session record shows the disclosure was presented and acknowledged before franchise selection.

**Fail / no-go:** the acknowledgement is missing, occurred after franchise selection, references a different package/session, or the UI implies that the Alpha's eight-team 82-game league is the official 2026–27 NHL structure.

This checkpoint does not authorize the pilot, change the simulation schedule, approve implemented UI, or permit PR #13 to merge.