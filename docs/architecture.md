# Architecture

Demo pitfalls and carry-forward rules: [lessons-learned.md](lessons-learned.md).
Panel program and AI author path: [panel-runtime.md](panel-runtime.md).

## Intent

Give operators physical buttons for station control. Keep contest and RF safety
in WIMS and seat agents. Treat Companion as a surface adapter only.

## Layers

```
Control surfaces (Stream Deck, Loupedeck, tablet, …)
        │
        ▼
Bitfocus Companion          ← deck USB; posts control id + event; paints faces
        │
        ▼
Panel runtime               ← panel program; allow-listed verbs only
        │
        ├──────────────────┬────────────────────┐
        ▼                  ▼                    ▼
   WIMS site :8787    Seat I/O agent      hamlib / flrig
   Work / Halt        Yaesu serial        Mode SSB / FM
   rotator point      antenna relays
   roster geometry    sensors (ADC)
```

## Ownership rules

| Resource | Sole owner |
|----------|------------|
| Stream Deck USB (or other surface) | Companion (or Satellite → Companion) |
| Yaesu rotator serial | Seat I/O agent |
| Antenna contact closures | Seat I/O agent |
| WSJT-X Work / Halt | WIMS site API only |
| N1MM log / RadioInfo | N1MM + WIMS N1MM agent |
| CAT for voice mode buttons | hamlib/flrig (or agreed bridge) |

Do not open the same serial port from Companion and from the seat agent.

## Data flow (examples)

Target path: Companion reports the press. The panel runtime runs the verb.
Until that runtime exists, the v0 map still uses Companion HTTP. See [button-map-v0.md](button-map-v0.md).

**Work top roster row**

1. Button press in Companion. Companion posts the control id to the panel runtime.
2. The runtime calls `wims.work_top`.
3. WIMS sends WSJT-X Reply under interlock and claims.

**Point to Az DX of top row**

1. Button → runtime `wims.point_top`.
2. WIMS resolves Az DX and commands the seat rotator path.
3. Seat agent sends Yaesu `Mxxx` / polls position; reports Az ant upward.

**Antenna Upper / Lower / Both**

1. Button → runtime `antenna.select(stack, select)`.
2. Seat agent drives Stamp Ethernet or USB relay contacts from the plane-A map.
3. Agent reports selected state to WIMS Overview.

**Mode SSB / FM**

1. Button → runtime `mode.set` on the hamlib path.
2. CW is not a mode button. KEY / KEY agent owns CW path.

## Safety

- Inhibit (KEY → type-18) stays peer-to-peer on the radio host. Not on the deck.
- Fail-safe boot: known antenna state; no rotator motion; no spontaneous TX.
- Soft az limits live in seat/WIMS config, not in Companion banks.
- The AI authors a panel program only. The author prompt lives in the panel runtime. The AI gets no shell, serial, or raw UDP. See [panel-runtime.md](panel-runtime.md).

## Why Companion (not OpenDeck alone)

- First-class multi-surface support (Elgato and others).
- Linux and Windows.
- Built-in delays, stacked actions, feedback, Satellite.
- Station verbs still live in WIMS / seat agent. The panel runtime calls them. Companion is not the source of truth.

## Relation to WIMS

WIMS already exposes:

- `POST /api/tx/work` — needs `row_id`
- `POST /api/tx/halt`
- `POST /api/rotator/point` — `row_id` or `rotator_id` + `az`
- `POST /api/rotator/stop`

Gaps for deck convenience (to add in WIMS or a thin proxy):

- `work_top` / `point_top` so buttons need no browser `row_id`
- Antenna select API on the seat agent
- Live Yaesu seat serial behind existing rotator API
