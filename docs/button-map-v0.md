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
| 0 (left) | **Upper Az** | Adjust `custom:upper_tgt` (wrap 0–359, accelerated) | Point upper rotator to target |
| 1 | **Lower Az** | Adjust `custom:lower_tgt` (wrap 0–359, accelerated) | Point lower rotator to target |
| 2 | (unassigned) | — | — |
| 3 | (unassigned) | — | — |

- Rotating only sets a target; nothing moves until press.
- Step size: **velocity-accelerated** (see below); 1° per detent when turned deliberately.
- Backend: WIMS rotator point with explicit rotator + az (API shape to confirm with WIMS).
- **Interim backend (now):** `scripts/rotator_sim.py` on `http://127.0.0.1:8790` (6°/s). It pushes `upper_az/_moving/_dir` and `lower_*` into Companion custom vars and points when a dial press bumps `<rot>_point_seq` (with `<rot>_point_az`). Wiring: `scripts/wire_rotator_knobs.py`.

### Knob acceleration (dials 0/1)

Time-between-detents multiplier — the scheme used by mathertel/RotaryEncoder's
`AcceleratedRotator`, FlexControl/VFO knobs and libinput's tracker (velocity from
inter-event time, reset on direction change or pause). Companion ignores the
encoder's own velocity, so it is computed in expressions from `unixNow()` (ms).

| Interval since last detent | Step per detent |
|----------------------------|-----------------|
| ≥ 200 ms (deliberate) | 1° |
| < 200 ms | 2° |
| < 120 ms | 5° |
| < 70 ms | 10° |
| < 35 ms | 15° |

- **Attack is instant** (a fast interval jumps straight to its tier); **release decays**: while the
  spin continues (interval < 200 ms) and slows, step = max(new tier, previous step ÷ 2), so
  10 → 5 → 2 → 1 over a few detents.
- **Grace memory (repeated flicks):** the first detent after a pause (200–800 ms) has no velocity
  information, so it starts from the previous gesture's *peak* step, faded linearly to 0 at 800 ms,
  ÷ 2 (e.g. peak 15 after a 400 ms pause → 3°; peak 10 → 2°; a pause > 800 ms → 1°). One-shot:
  the first slow click consumes the memory, so later fine-adjust clicks are 1° again. The second
  detent of a burst still jumps straight to its tier, so bursts 2, 3… ramp like burst 1 (±2°).
  A pure deliberate click train (peak 1) is never boosted.
- **Direction reversal** drops carried decay/grace memory but still applies the live velocity tier
  (a fast reversal keeps its speed; a slow one is 1°). It no longer hard-resets to 1°.
- Per-dial state vars: `<rot>_last_ms`, `<rot>_last_dir` (±1), `<rot>_step`, `<rot>_peak`. Action
  order in each rotate set is fixed: `step` → `peak` → `tgt` → `edit_until` → `last_ms` → `last_dir`.
- Tune the constants at the top of `scripts/wire_rotator_knobs.py` (`ACCEL_TIERS`, `STEP_SLOW`,
  `DECAY_DIV`, `GRACE_MS`, `GRACE_DIV`) and re-run it (after `demo_paint_buttons.py`). Test without
  the deck: `python3 tools/dev/test_knob_accel.py [dial]` (all scenarios) or
  `python3 tools/dev/test_knob_accel.py [dial] bursts` (repeated-flick consistency).
- Edit window (5 s), wrap and strip behavior are unchanged.

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
