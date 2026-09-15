# Technical Alpha launch-stability disclosure

This note is authoritative for the physical-device launch step until the pilot guide is consolidated.

A successful Android launch is not established by a single process observation. `scripts/launch_alpha_app.py` must report `status: pass`, `installation_confirmed: true`, `launch_confirmed: true`, and `launch_stability_confirmed: true` for the same application process after the configured three-second stability window before the guided gameplay smoke may begin.

If the process exits, restarts with a different PID, or otherwise fails the stability check, treat the launch as blocked. Do not begin gameplay smoke, do not capture Stage 3 evidence, and do not distribute that candidate. Correct the defect and repeat the exact-package install/launch path.

This is facilitator-facing release evidence only; it does not add tester-facing UI or change the approved Stage 2 Team-Branded Command Center direction. Implemented screens remain `UI Review Pending` until Kyle approves Stage 3 evidence from the exact pilot candidate.
