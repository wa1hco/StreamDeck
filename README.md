# StreamDeck — ham station panel control

Cross-platform control surfaces (Elgato Stream Deck and other decks) for a
ham contest station. Surfaces talk to **Bitfocus Companion**. Station I/O and
contest logic stay outside the deck host.

Related: [WIMS](../wims/) (roster, Work/Halt, rotator API).

## Goals

- Buttons for antenna upper / lower / both, rotators (Yaesu GS-232), mode
  SSB/FM, point-to-roster azimuth, Work top roster row, Halt.
- Multiple deck brands on Linux and Windows.
- Natural-language layout config via a sandboxed panel program. Design: [docs/panel-runtime.md](docs/panel-runtime.md). Not built yet.
- Hardware bindings that survive PC reboot and deck-software updates.

## Stack (chosen)

| Layer | Choice | Role |
|-------|--------|------|
| Surfaces | Bitfocus Companion | Stream Deck and other decks; macros; feedback |
| Contest brain | WIMS site (`:8787`) | Roster, Work/Halt, rotator point/stop |
| Seat I/O | Seat agent (to build) | Yaesu serial, antenna relays, sensors |
| Radio CAT | hamlib / flrig and/or N1MM | Mode SSB/FM; RadioInfo for band |
| Panel config | Panel runtime | AI-authored panel program; allow-listed verbs only. Design only. |

OpenDeck remains an Elgato-only option. Companion is the surface host because
deck brand may change.

## Docs in this tree

| Doc | Content |
|-----|---------|
| [docs/lessons-learned.md](docs/lessons-learned.md) | **Carry-forward facts** from the Plus demo |
| [docs/architecture.md](docs/architecture.md) | Layers, data flow, safety rules |
| [docs/panel-runtime.md](docs/panel-runtime.md) | Panel program, author prompt, dry-run, AI grant |
| [docs/config-planes.md](docs/config-planes.md) | Hardware vs topology vs panel config |
| [docs/seat-io-schema.md](docs/seat-io-schema.md) | Draft seat inventory (rotator, antenna, sensors) |
| [docs/companion-install.md](docs/companion-install.md) | Install and launch Companion on this host |
| [docs/button-map-v0.md](docs/button-map-v0.md) | First button → verb map |
| [docs/demo-plus-layout.md](docs/demo-plus-layout.md) | Stream Deck+ demo (8 keys + strip + knobs) |
| [docs/button-font-sizing.md](docs/button-font-sizing.md) | Plus key px size and fontsize % mapping |

## Quick start

1. Read `docs/architecture.md`.
2. Install Companion — see `docs/companion-install.md`.
3. Open Companion admin UI (default `http://127.0.0.1:8000`).
4. Do **not** put COM ports or relay maps only in Companion banks.
   Put those in seat I/O config (plane A/B).

## Status

- Architecture written (`docs/`).
- Companion **5.0.5** installed for user at `~/.local/share/companion`.
- Headless admin UI verified at http://127.0.0.1:8000/ (when running).
- Stream Deck+ demo painted: MODE/ANT cycles, strip toast, fixed non-wrap fonts.
- Rotator dials wired (dial 1 = upper, dial 2 = lower) to an **interim rotator simulator** (`scripts/run-rotator-sim.sh`, :8790, 6°/s) instead of WIMS. Repaint order: `demo_paint_buttons.py`, then `wire_rotator_knobs.py`.
- Seat I/O agent and panel runtime: design only ([docs/panel-runtime.md](docs/panel-runtime.md)). Not started.
