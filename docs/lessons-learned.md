# Lessons learned (carry forward)

Hard-won facts from the Stream Deck+ / Companion demo. Use these before
changing panel UX, fonts, or toast behaviour.

Related docs: [architecture.md](architecture.md), [panel-runtime.md](panel-runtime.md),
[config-planes.md](config-planes.md), [button-font-sizing.md](button-font-sizing.md),
[demo-plus-layout.md](demo-plus-layout.md).

---

## 1. Product split

| Layer | Owns | Does not own |
|-------|------|--------------|
| **Companion** | Surfaces, pages, macros, feedback draw | Radio serial, Yaesu, relays, inhibit |
| **WIMS / seat agent** | Work/Halt, rotator, antenna, KEY inhibit | Deck USB |
| **Panel runtime** | AI-authored panel program and allow-listed verbs. See [panel-runtime.md](panel-runtime.md). | Raw shell, serial bytes, raw UDP |

- Prefer **Companion** over OpenDeck when deck **brand may change**.
- Do **not** clone Companion source for station work. Binary + connection module is enough.
- One app owns Stream Deck USB. Do not run Elgato software and Companion together.

---

## 2. Stream Deck+ is not 16 LCD keys

Companion reports a **4×4 grid**. Physical hardware is:

| Companion row | Hardware |
|---------------|----------|
| 0–1 | **8 LCD keys** (2×4), 120×120 px each |
| 2 | **Touch strip** (4 tap regions; strip canvas 800×100) |
| 3 | **4 encoders** |

Paint and UX must treat rows 0–1 as primary actions. Row 2 is strip feedback.
Row 3 is knobs.

Official Companion note: strip taps fire down+up with a short delay; strip is a
poor place for long-press critical actions.

---

## 3. Font size is % of element height

```text
font_px ≈ fontsize% × element_height_px / 100 / 1.2
```

- Plus LCD key: **120×120 px**.
- UI range roughly 3–200. Historical “auto” ≈ **100**.
- **Shrink to fit** must stay **on** for multi-letter labels.
- Shrink **off** + large `%` ⇒ truncation / only a couple of glyphs visible.

Practical demo defaults: LCD **42%** (fits `POINT` on one line), strip **70%**,
knobs **50%**, shrink **on**. At 58%+, `WORK` / `POINT` still wrapped on 120 px keys.

Details: [button-font-sizing.md](button-font-sizing.md).

---

## 4. Companion `wait` aborts on key release

Internal action `wait` uses the button’s **abortDelayed** signal.

- Finger up ⇒ wait cancelled.
- Toast that “wait 1500 ms then clear” only lasts for the press (~hundreds of ms).

**Do not** use `wait` for strip takeover timing.

**Do** use a clock expiry the strip expression can read:

1. On press: set `demo_toast` = next value.
2. Set `demo_toast_until` = `$(internal:time_unix) + N` (expression).
3. Strip text:
   `$(internal:time_unix) < $(custom:demo_toast_until) ? $(custom:demo_toast) : $(custom:demo_status)`
4. No clear-on-wait in the press chain. Clock tick redraws the strip.

Demo hold: **N = 3** seconds (adjust as needed).

---

## 5. `$(this:step)` is **1-based**

Companion sets `stepCurrent = getActiveStepIndex() + 1`.

| Step id in DB | `$(this:step)` |
|---------------|----------------|
| `"0"` | **1** |
| `"1"` | **2** |
| `"2"` | **3** |

Face expressions must use 1, 2, 3 — not 0, 1, 2.

Wrong ANT expression (`== 0 ? UPR : == 1 ? LWR : BOTH`) produced **LWR / BOTH / BOTH**
and never UPR.

Correct:

```text
$(this:step) == 1 ? 'UPR' : $(this:step) == 2 ? 'LWR' : 'BOTH'
$(this:step) == 1 ? 'SSB' : 'FM'
```

## 6. Cycle toast must show the **next** value

MODE/ANT are multi-step keys. Down actions run on the step you are **on** when
you press (before advance).

| Face now | Press should toast |
|----------|--------------------|
| SSB | **FM** |
| FM | **SSB** |
| UPR | **LWR** |
| LWR | **BOTH** |
| BOTH | **UPR** |

Toast = what you are selecting, not the old face value.

Prefer strip toast over reading the LCD under the finger. Prefer strip over a
PC popup for contest seats.

---

## 7. Style / button creation APIs

- Create regular keys as **`button-layered`** (`controls.resetControl` + `newType`).
- HTTP `/api/location/.../style` returns **204** until a real control exists.
- Layered buttons need **`canModifyStyleInApis: true`** or remote style changes are ignored.
- Default layer ids: **`box0`** (background), **`text0`** (label).
- Wait option is an **expression in ms**. Prefer time_unix hold anyway (lesson 4).

---

## 8. Config planes (stability)

| Plane | Content | Change rate |
|-------|---------|-------------|
| **A** Hardware inventory | USB serial ids, Stamp IP, relay maps | Rare |
| **B** Station topology | band→rotator, stack→antenna | Seasonal |
| **C** Operator panel | Companion pages / future DSL | Often |

- Bind devices by **stable id** (USB serial, fixed IP), not bare `COM5` / `ttyUSB0`.
- Never store plane A only inside Companion banks.
- Seat agent boots last-known-good A/B after reboot.

---

## 9. Linux USB

- Install Companion-generated udev rules (desktop rules + `uaccess`).
- Stream Deck+ product id includes **0fd9:0084**.
- After rules: unplug/replug or rescan; Companion log should show
  `Surface panel ready: streamdeck:…`.

---

## 10. Safety (unchanged)

- Inhibit / KEY path stays off the deck.
- Work/Halt only via WIMS API, not raw WSJT-X UDP from the profile.
- CW is not a mode cycle option; KEY owns CW.
- Fail-safe boot: known antenna state; no spontaneous TX.

---

## 11. Demo apply path

```bash
./scratch/venv/bin/python scripts/demo_paint_buttons.py
kill "$(cat scratch/companion.pid)"
scripts/run-companion-headless.sh
```

Admin UI: http://127.0.0.1:8000/

When changing toast/cycle behaviour, update **both** the live Companion DB wiring
and `scripts/demo_paint_buttons.py` so a re-paint does not regress lessons 4–5.

---

## 12. Companion expressions: `+` never joins strings

`'UPR ' + $(custom:upper_az)` evaluates to **`NaN`** in Companion 5 (the `+`
operator is numeric-only). The rotator strips showed no usable text on the deck
(only background color changes) until the text was rebuilt with template
strings: `` `UPR ${$(custom:upper_az)}` `` (or `concat()`). The same bug sat in
the MODE/ANT `demo_status` actions. Numeric `+` (target step, `time_unix + 5`)
is fine.

Verify without the deck: `scratch/venv/bin/python scripts/preview_button.py ROW COL out.png`
saves Companion's rendered PNG (trpc `preview.graphics.location`) — `NaN` in the
image means a bad expression.

Also: `demo_paint_buttons.py` repaints **all four** strip regions, so run
`wire_rotator_knobs.py` *after* it. The rotator sim now compares against
Companion's live variable values each tick, so re-wiring or a Companion restart
no longer leaves `*_moving` / `*_dir` stale.

---

## 13. Knob acceleration: use `unixNow()` (ms), not `time_unix`

`$(internal:time_unix)` is 1 s resolution — useless for detent timing. Companion expressions
have `unixNow()` (Unix **ms**), so no helper process is needed. Companion ignores the encoder's
own velocity (bitfocus/companion #2511, #3179), and the community "wait + set step" workaround
(steps 1/2/4/8/16 with Waits) is clumsy; instead each rotate action set stores the previous
detent's `unixNow()` and direction in custom vars and derives the step from the interval
(`wire_rotator_knobs.py`, `step_expr`).

- Actions in one set run **in order**, so `step` (reads old `last_ms`) → `tgt` (reads new
  `step`) → `last_ms`/`last_dir` (written last) is safe. Verified via HTTP rotate at 25–300 ms.
- Interval measured at action execution, not USB event time: expect ~10 ms jitter (+ HTTP latency
  when scripted: a nominal 25 ms test gap measures ~35–45 ms, which lands in the 10° tier, not 15°).
- Multi-statement expressions (`dt = ...;` newline `...`) work in action value fields.
- `tools/dev/test_knob_accel.py` drives `/api/location/1/3/<col>/rotate-left|right` and prints
  tgt/step per detent (slow, brisk, fast, decay, pause reset, reversal, wrap).

### 13a. Repeated flicks: the first detent after a pause has no velocity (grace memory)

Feel-test on the real deck: "turning fast repeatedly does not accelerate the same way at the
first turn after a pause." Measured with `tools/dev/test_knob_accel.py <dial> bursts`
(burst, 400 ms, burst, 1 s, burst, 400 ms, burst, 150 ms, burst):

- Cause: a hard reset at 250 ms. A pause of 150–250 ms carried the old step (burst 5 started at
  7°), a pause of 250 ms+ started at 1°. Two flicks 300–800 ms apart (the normal rhythm of
  repeated flicks) therefore felt different from continuous spinning. The timing itself was
  fine (`last_ms` is written after `step`, `unixNow()` is ms, `edit_until`/`time_unix` don't
  interfere), and the second detent of a burst already jumped to its tier with no lag.
- A detent's interval is only known once a *second* detent arrives, so the first one can't be
  accelerated from its own velocity. Fix is memory, not lookahead: remember the gesture's peak
  step (`<rot>_peak`) and start the first detent after a pause at `peak × fade ÷ 2`
  (fade 1 → 0 over 200–800 ms). One-shot (a pause or reversal consumes the peak) so slowing
  down to land on the target still gives 1° clicks; a pure 300 ms click train stays at 1°.
- Direction reversal no longer hard-resets to 1°: it drops decay/grace memory but keeps the
  live velocity tier (a bounce at the end of a flick isn't punished).
- Honest limit: the effect is small (+1…+6° on one detent). Raising `GRACE_DIV` toward 1 makes
  repeat flicks start hotter but also makes the first fine click after a flick jump.
- Test helper convention: dev/test helpers live in `tools/dev/`, deck/runtime scripts in `scripts/`.
