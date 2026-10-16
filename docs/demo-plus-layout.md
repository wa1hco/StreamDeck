# Stream Deck+ demo layout

Carry-forward rules (toast timing, fonts, Plus grid): [lessons-learned.md](lessons-learned.md).

## Hardware map (Companion)

| Row | Hardware |
|-----|----------|
| 0–1 | **8 LCD keys** (2×4) |
| 2 | **Touch strip** (4 tap regions) |
| 3 | **4 encoders** |

## LCD keys

| | 0 | 1 | 2 | 3 |
|---|----|----|----|----|
| **0** | MODE (cycle SSB/FM) | ANT (cycle UPR/LWR/BOTH) | WORK | HALT |
| **1** | POINT | STOP | PARK | WIMS |

Labels are short single-line words. Font sizing is documented in
[button-font-sizing.md](button-font-sizing.md): LCD **42%** of key height with
**shrink-to-fit on** (Plus keys are 120×120 px; fits `POINT`).

## Touch strip

- **Idle:** `$(custom:demo_status)` e.g. `SSB | LWR`
- **On MODE/ANT press:** toast shows the **next** value for ~**3 s**, then status
- Hold uses `time_unix` expiry — not Companion `wait` (wait aborts on key release)

## Knobs

Dial 0 = **Upper Az**, dial 1 = **Lower Az** (rotate sets target, press points). Dials 2–3 unassigned. Strip regions above dials 0/1 show Az except while a MODE/ANT toast holds the strip. See [button-map-v0.md](button-map-v0.md).

## Apply

```bash
./scratch/venv/bin/python scripts/demo_paint_buttons.py
kill "$(cat scratch/companion.pid)"
scripts/run-companion-headless.sh
```
