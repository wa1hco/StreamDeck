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

## Touch strip

Idle status `mode | ant`. Brief toast after MODE/ANT cycle (~1.5 s).

## Knobs (demo labels only)

VFO · PWR · AZ · VOL — rotary enabled; not wired to station yet.

## Companion wiring (interim)

Until the panel runtime exists ([panel-runtime.md](panel-runtime.md)):

1. Use Companion **HTTP** (or generic web request) actions toward WIMS.
2. Use **internal** / shell only for opening the console URL if needed.
3. Prefer a small local proxy later so Companion never embeds raw `row_id` logic.

## Explicit non-goals for v0

- Auto-point on every Work (keep Point and Work separate).
- Deck-owned inhibit.
- AI layout editor (design saved in [panel-runtime.md](panel-runtime.md); not built).
