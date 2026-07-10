# NHL GM Alpha 0.2 Closed Testing Guide

## Start the game

1. Install Python 3.11+ and Node.js 20+ on the development computer.
2. Install Expo Go on the Android test phone.
3. From the repository root, run `python scripts/start_dev.py`.
4. Scan the Expo QR code while the phone and computer are on the same network.

If the phone cannot connect, rerun with the computer's LAN address:

```bash
python scripts/start_dev.py --lan-ip 192.168.1.10
```

## Core test pass

1. Confirm eight franchises appear on the Dashboard.
2. Select a different franchise and restart the mobile client; the selection should persist.
3. Advance through at least ten calendar days.
4. Confirm scheduled games produce final scores without ties.
5. Open Game Center and verify the latest result, recent results, and standings agree.
6. Filter the roster by forwards, defense, and goalies.
7. Open Trade Center, change the trade partner, cycle both player cards, and submit one likely accepted and one likely rejected offer.
8. Confirm both proposals appear in Trade History.
9. Restart the API and mobile client; the season day, results, team selection, and trade history should persist.
10. Use Front Office → New Game / Reset Save and confirm the season returns to Day 1.

## Longer simulation pass

- Advance through a full season and confirm every team finishes with 82 games.
- Confirm no team finishes with more than 164 standings points.
- Confirm the calendar stops cleanly at Day 186.

## Bug report format

Include:

- Short title and severity: blocker, major, minor, or visual.
- Exact steps that caused the problem.
- Expected result and actual result.
- Phone model and Android version.
- Current game day and controlled franchise.
- Screenshot or screen recording when possible.
- The JSON shown at `http://localhost:8000/api/v1/debug-report` from the development computer.

Do not include the SQLite database in a public issue. Share it privately when save-level reproduction is required.
