# Config planes

Keep three planes separate. Mixing them makes reboot and updates unsafe.

## Plane A — Hardware inventory

Rarely changes. Survives PC reboot and Companion updates.

Examples:

- Rotator USB serial number or fixed TCP endpoint
- Yaesu dialect (GS-232 subset / K3NG build notes)
- Antenna driver: Ethernet Stamp host/port **or** USB relay board id
- Contact map: upper / lower / both → contact set
- ADC channel → scale → named sensor
- Boot defaults and fail-safe states

Store: versioned files on the seat (or site config package pulled by the seat).
Load: seat agent at service start. Keep last-known-good.

Bind by stable identity (USB serial, MAC, fixed IP). Do not rely on bare
`COM5` or `/dev/ttyUSB0` alone.

## Plane B — Station topology

Changes per season or contest layout.

Examples:

- Band or instance → rotator id
- Stack id → physical antenna plant
- Soft az limits per mast
- Which radio path (hamlib vs N1MM-only) for voice mode buttons

Store: same durable store as A, separate section, `config_version` field.

## Plane C — Operator panel

Changes often. Safe for AI-assisted edits later.

Examples:

- Companion pages and button labels
- Macros and delays
- Which logical verb each button fires

Store: a panel program. See [panel-runtime.md](panel-runtime.md).
Companion displays faces and reports events.
The program uses plane A/B names (`rot-144`, `stack-144`). It contains no COM ports.

## Update and reboot rules

| Event | Expected behaviour |
|-------|--------------------|
| PC reboot | Seat agent starts; reloads last-known-good A/B; applies boot antenna state |
| Companion update | Surfaces and plane C may reset; A/B unchanged |
| Bad A/B edit | Validator rejects; previous good file stays active; Overview shows fault |
| Lost Stamp / serial | Agent reports RED/stale; no silent “pointed” or “selected” assumption |

## What AI may write (later)

- Plane C after schema validate and an operator dry-run confirm. See [panel-runtime.md](panel-runtime.md).
- Plane B only with human confirm.
- Plane A only as a proposal + dry-run; engineer applies.
