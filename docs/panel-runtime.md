# Panel runtime

Design agreed 2026-09-24. Not implemented.

Related: [architecture.md](architecture.md), [config-planes.md](config-planes.md),
[button-map-v0.md](button-map-v0.md), [seat-io-schema.md](seat-io-schema.md),
[lessons-learned.md](lessons-learned.md).

## Locked choices

1. The AI authors a panel program. The operator confirms a dry-run. Then the panel runtime loads it.
2. Companion owns the deck USB. Station verbs exist only in the panel runtime.

## Names

- **Panel program** — plane C document. Faces, slots, and verb steps.
- **Panel runtime** — local interpreter. This is the VM.
- **Author prompt** — fixed instructions for the AI. This ships inside the panel runtime.
- **Face spec** — label, palette colors, and optional icon for one control.
- **Verb** — one allow-listed action, such as `rotator.point`.
- **Capability** — a plane A/B name, such as `rot-144` or `stack-144`.
- **Catalog** — the verbs and capability names a program may use.
- **Dry-run** — a local list of each control and the verbs it will call. No device I/O.

## Trust boundary

The AI service returns text. It has no socket to this PC.
The operator reviews the dry-run on this PC.
The runtime loads a program only after that confirm.
If validation fails, the last-known-good program stays active.

A live session where the AI presses buttons during a contest is a later mode. Leave it off.

## Each AI turn

The runtime sends four parts:

1. The author prompt.
2. The catalog, the surface shape, and the capability names on this seat.
3. The current panel program, if one is loaded.
4. The operator's latest reply.

The call omits USB ids, device paths, and the WIMS credential.

The model returns two parts:

- A short reply to the operator.
- An optional proposed panel program.

The runtime checks the proposal. Then it shows the dry-run. The operator does not see YAML unless they ask.

## Author prompt

The author prompt is part of the panel runtime. The AI does not write it. The panel program contains no prompt text.

The prompt tells the AI to:

- Ask what the operator wants, in plain language.
- Use only verbs and capability names from the catalog.
- Propose a face spec for each control.
- Read the layout back as one sentence per control.
- Keep Work and Point separate. Leave Halt on its own key.
- Leave CW and inhibit out of the layout.
- Wait for an explicit yes before treating the proposal as final.
- Return the operator reply and the panel program as two separate parts.

A layout change cannot relax these rules.

## Panel program

The program is closed YAML or JSON. The runtime compiles it to a step list. The model never emits bytecode.

A program may:

- Place controls on a surface map (LCD keys, strip, knobs).
- Set a face spec.
- Run a sequence of verb calls.
- Cycle a value (`SSB` / `FM`, `upper` / `lower` / `both`).
- Repeat a block a bounded number of times.
- Wait on a host timer.
- Read a small state snapshot in a pure expression (`radio.mode`, `rot-144.az`).

The validator rejects unknown fields, unknown verbs, unknown capability names, and over-budget programs.

Budgets:

- A max step count per press.
- A max repeat count.
- A max total wait.
- The host timer owns delays. Key-up cancels a wait.

The language has no `while`, no recursion, and no import. It has no `serial.write`, no `open`, and no HTTP URL.

Expressions are pure. Side effects exist only in `call` steps.

```yaml
version: 1
controls:
  - id: work
    at: { row: 0, col: 2 }
    face:
      label: WORK
      bg: amber
      fg: white
      icon: none
    on_press:
      - call: wims.work_top
```

## Verbs

| Verb | Who performs it |
|------|-----------------|
| `mode.set` | hamlib path |
| `antenna.select` | Seat agent |
| `rotator.point`, `rotator.bump`, `rotator.stop`, `rotator.park` | Seat agent |
| `sensor.read` | Seat agent cache |
| `wims.work_top`, `wims.halt`, `wims.point_top` | WIMS client |
| `wims.open_console` | WIMS client. The URL lives in plane A. |

The program names a capability (`rot-144`, `stack-144`). Plane A and plane B map that name to a USB serial id, a Stamp endpoint, or the WIMS origin.

The WIMS client calls only the allow-listed paths on the configured origin. It attaches auth itself. It does not follow a redirect to another host.

A new accessory is a driver plus a capability name in plane A. After that verb exists, a panel program may use the name. The AI cannot declare a driver.

The seat agent is a separate process. It checks the type, the soft azimuth limits, and any TX interlock. Then it sends GS-232 or relay commands. The Arduino firmware enforces its own limits again.

## Face spec and Companion

```yaml
face:
  label: WORK
  bg: amber
  fg: white
  icon: none
```

`label` is a short word or a state field such as `radio.mode`. `bg` and `fg` are palette names. `icon` is a built-in icon name, or `none`.

Slot sizes:

- LCD key: 120×120 px.
- Touch strip: 800×100 px.
- Knob face: the size Companion reports for that slot.

The runtime draws the face to a PNG on this PC. It writes that PNG into the Companion control over the local admin API, `ws://127.0.0.1:8000/trpc`.

Companion 5.0 layered controls have an image element. The element type is `image`. The field is `base64Image`. Companion sends the bitmap to the deck. The runtime does not open the deck USB device.

The demo path is already proven and is narrower. `scripts/demo_paint_buttons.py` sets `box0` color and `text0` text with `controls.styles.updateOption`. Use that path until the PNG layer is wired. Draw text into the PNG once icons exist, so one place owns the font rule.

The AI does not send a URL, a file path, or PNG bytes. A custom picture is a local file the operator picks. The program stores an asset id. The runtime reads the file.

Keep LCD labels short. `POINT` is the long word that must fit a 120 px key. See [button-font-sizing.md](button-font-sizing.md). While the runtime still uses the Companion text layer, set LCD `fontsize` to 42 and leave shrink on.

## Install and AI authorization

A button is a face spec plus verbs. It is not a software install.

The seat package installs:

- The panel runtime.
- The seat agent.
- Companion, with one fixed page. That page only reports presses and turns.
- The verb catalog, the palette, and the icon set.

That stack is the only program allowed to call the AI service. The panel program cannot read the credential. Companion cannot read it.

Grant steps:

1. The package installs with no AI key.
2. First launch opens a page on this PC. The operator connects an AI account with a device-code login. A site admin may instead place a seat key in a local secret file.
3. The runtime stores the token on this PC. Outbound calls go only to the AI host and to the WIMS origin from plane A.
4. Each call sends the four parts under [Each AI turn](#each-ai-turn).
5. The service returns text. The runtime checks it. The operator confirms the dry-run. Then the runtime loads the program.
6. Remove the local token to stop new AI calls. The deck keeps the last loaded program.

The AI service has no inbound connection to this PC. A new layout is a new panel program. A new radio, rotator, or relay driver is a seat-agent install. That install does not receive the AI token.

## Operator conversation

The operator needs no manual. The author prompt is the manual.

The runtime already knows the deck shape, the verb list, the font limits, and the capability names. The operator fills only the gaps.

Fixed first reply:

> I can set up this button box. I need three things from you.
> Tell me what you want the buttons and knobs to do, in your own words.
> I will name the devices I found. Tell me which ones to use.
> I will read the layout back. Say yes before I load it.
> I already know the shape of this box and the actions it is allowed to perform. You can skip ports, addresses, and color codes.

The runtime then lists capabilities. For the v0 station that list is:

- Radio CAT for `mode.set` (`SSB` or `FM`).
- Antenna stack `stack-144` for `antenna.select` (`upper`, `lower`, `both`).
- Rotator `rot-144` for point, bump, stop, and park.
- WIMS for `wims.work_top`, `wims.halt`, `wims.point_top`, and `wims.open_console`.
- Sensors named in plane A, as read-only values.

The v0 knobs (VFO, power, azimuth, volume) have labels and no verbs yet. The model asks before it binds a knob. It also asks for the step size. Example question: "Each click of AZ bumps rot-144 by 2 degrees. Is that what you want?"

If a device is missing, the model says so. It offers only verbs that exist.

Starting face proposal, from [button-map-v0.md](button-map-v0.md):

| Slot | Label | Background | Verb |
|------|-------|------------|------|
| Top row | MODE, ANT, WORK, HALT | green, teal, amber, red | mode, antenna, work, halt |
| Bottom row | POINT, STOP, PARK, WIMS | purple, gray, gray, blue | point, stop, park, open console |
| Knobs | VFO, PWR, AZ, VOL | dark | none until assigned |
| Strip | mode and antenna | dark | status, then a short toast |

Icons stay off unless the operator asks for one.

Dry-run sentences:

- WORK tells WIMS to work the top roster row.
- HALT tells WIMS to halt.
- POINT turns rotator rot-144 to that row. It does not start a contact.
- STOP stops the rotator. PARK sends it to the stored park azimuth.
- MODE switches SSB and FM.
- ANT cycles upper, lower, and both on stack-144.
- The strip shows the new mode or antenna for about 3 seconds.

Safety readback before yes:

- Halt stays on its own key.
- Work and Point stay separate.
- This box does not send CW and does not own inhibit.
- Load happens only after yes.

After load, the model waits for a change request. The same dry-run gate applies.

## Companion page

Each Companion control posts `control id + event` to the panel runtime. The runtime paints the face. The AI does not edit Companion banks.

A shell action or a free URL inside Companion is an escape if a model can write it. The fixed page has neither.

Until this runtime exists, the v0 map may still use Companion HTTP toward WIMS. See [button-map-v0.md](button-map-v0.md).

## Plane rules

Same split as [config-planes.md](config-planes.md):

- Plane C after schema validate and an operator dry-run confirm.
- Plane B with human confirm.
- Plane A as a proposal plus a dry-run. An engineer applies it.

## Not built yet

- The panel runtime and the author prompt.
- The seat agent.
- PNG `base64Image` wiring. The field is present in Companion 5.0. The demo still sets text and color.
- Live AI tool-use during a contest.
