# Seat I/O config schema (draft)

Illustrative YAML for planes A and B. Not loaded by software yet.
Stable names here are what Companion buttons and WIMS should call.

```yaml
config_version: 1

seat:
  seat_id: trailer-144
  report_to: "http://wims-site:8787/api/agents/report"

radio:
  # Voice mode buttons (SSB/FM) — CAT
  cat:
    kind: hamlib_rigctld
    host: 127.0.0.1
    port: 4532
  # Live band/freq for WIMS — N1MM path stays with N1MM agent
  n1mm_agent: true

rotators:
  rot-144:
    bind:
      kind: serial
      by: usb_serial
      id: "REPLACE_WITH_USB_SERIAL"
      # fallback only: path: /dev/serial/by-id/usb-...
    protocol: yaesu_gs232
    soft_az: [0, 360]
    park_az: 0
    poll_ms: 500

antenna_stacks:
  stack-144:
    driver: ethernet_stamp   # or: usb_relay
    endpoint:
      host: 192.168.10.40
      port: 10000
    selects:
      upper: { contacts: [1] }
      lower: { contacts: [2] }
      both:  { contacts: [1, 2] }
    boot: lower              # fail-safe known state
    # refuse_change_while_tx: true   # station rule — decide before wiring

sensors:
  pa-voltage:
    bind:
      driver: stamp_adc
      channel: 3
    scale:
      v_per_count: 0.012
    warn_below_v: 12.0
    stale_after_s: 5

topology:
  # Plane B — logical maps
  instances:
    TRAILER-144-FT8:
      rotator: rot-144
      antenna_stack: stack-144
```

## Logical verbs (seat / WIMS)

| Verb | Args | Owner |
|------|------|--------|
| `antenna.select` | `stack_id`, `select` ∈ upper\|lower\|both | Seat agent |
| `rotator.point` | `rotator_id`, `az` **or** WIMS `row_id` | WIMS → seat |
| `rotator.stop` | `rotator_id` | WIMS → seat |
| `rotator.park` | `rotator_id` | Seat (uses `park_az`) |
| `sensor.read` | `sensor_id` | Seat (report upward) |
| `tx.work` / `tx.halt` | WIMS API | WIMS site |
| `mode.set` | `SSB` \| `FM` | hamlib |

## Drivers to implement

1. `yaesu_gs232` — reuse WIMS helpers (`Mxxx`, `A`/`S`, `C`/`C2`).
2. `ethernet_stamp` — contact closures over TCP (protocol TBD per board).
3. `usb_relay` — HID/serial relay board (bind by USB serial).
4. `stamp_adc` / generic ADC — scaled volts to named sensors.

## Persistence

- Path (proposed): `/etc/wims-seat/seat.yaml` or `$XDG_CONFIG_HOME/wims-seat/seat.yaml`
- Atomic replace + `.bak` last-known-good
- Agent refuses start if schema version unsupported without migrate
