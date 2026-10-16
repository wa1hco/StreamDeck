# Button map v0 (Stream Deck+)

See [demo-plus-layout.md](demo-plus-layout.md) for the painted demo.

Each LCD key is a **logical verb** (or cycle). No COM ports in button settings.

## LCD (2×4)

| Button | Behaviour | Backend (next) |
|--------|-----------|----------------|
| MODE | Cycle SSB ↔ FM; strip toast | hamlib `mode.set` |
| ANT | Cycle UPR → LWR → BOTH; strip toast | seat `antenna.select` |
| WORK | Work top roster | WIMS `/api/tx/work` |
| HALT | Halt | WIMS `/api/tx/halt` |
| POINT | Point top Az DX | WIMS `/api/rotator/point` |
| STOP | Rotator stop | WIMS `/api/rotator/stop` |
| PARK | Rotator park | seat `rotator.park` |
| WIMS | Open console | URL `:8787` |

No CW mode button. KEY path is separate.

## Knobs

| Dial | Role | Rotate | Press |
|------|------|--------|-------|
| 0 (left) | **Upper Az** | Adjust `custom:upper_az_target` (wrap 0–359) | Point upper rotator to target |
| 1 | **Lower Az** | Adjust `custom:lower_az_target` (wrap 0–359) | Point lower rotator to target |
| 2 | (unassigned) | — | — |
| 3 | (unassigned) | — | — |

- Rotating only sets a target; nothing moves until press.
- Step size: 1° per detent (coarse 10° step TBD).
- Backend: WIMS rotator point with explicit rotator + az (API shape to confirm with WIMS).
- **Interim backend (now):** `scripts/rotator_sim.py` on `http://127.0.0.1:8790` (6°/s). It pushes `upper_az/_moving/_dir` and `lower_*` into Companion custom vars and points when a dial press bumps `<rot>_point_seq` (with `<rot>_point_az`). Wiring: `scripts/wire_rotator_knobs.py`.

## Touch strip (per dial region)

- Regions 0/1 idle: that rotator's **current** Az, e.g. `UPR 245`.
- First knob turn seeds the target from current Az; the strip then shows the **new target** as the knob changes it (e.g. `UPR →270`).
- Press points to the target; strip goes back to tracking current Az.
- **Timeout:** if no press within ~5 s of the last turn, the target is dropped and the strip reverts to current Az.

### Strip colors (regions 0/1)

| State | Text | Background |
|-------|------|------------|
| Current Az, rotator stopped | white | black |
| Current Az, rotator turning | white | dark green, with direction arrow (`↻` CW / `↺` CCW after the Az, e.g. `UPR 245 ↻`) |
| New target (knob being turned, not yet pressed) | amber | black |

Editing text is `UPR →270`. Colors are proposals; tune on hardware. Turning/stopped state comes from the rotator sim for now (WIMS API TBD).
- A MODE/ANT cycle toast takes over the strip (text = toast, white on `#111111`); Az display returns when the toast expires.
- Strip text/colors are Companion **expressions**; build text with template strings (`` `UPR ${$(custom:upper_az)}` ``), never `+` (numeric only; `'a' + 'b'` is `NaN`). See lesson 12 in [lessons-learned.md](lessons-learned.md).

## Companion wiring (interim)

Until the panel runtime exists ([panel-runtime.md](panel-runtime.md)):

1. Use Companion **HTTP** (or generic web request) actions toward WIMS.
2. Use **internal** / shell only for opening the console URL if needed.
3. Prefer a small local proxy later so Companion never embeds raw `row_id` logic.

## Explicit non-goals for v0

- Auto-point on every Work (keep Point and Work separate).
- Deck-owned inhibit.
- AI layout editor (design saved in [panel-runtime.md](panel-runtime.md); not built).
