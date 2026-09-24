# Bitfocus Companion install (this host)

Target: Ubuntu 24.04 x86_64. Surface host for Stream Deck and other decks.

Official downloads: https://user.bitfocus.io/download  
Docs: https://companion.free/user-guide/v5.0/getting-started/Installation

## Chosen method: CompanionPi-style system service

Headless service under user `companion`, admin UI on port **8000**.
Good for reboot persistence. No tray icon required.

```bash
# From a root shell (or sudo)
curl -fsSL https://raw.githubusercontent.com/bitfocus/companion-pi/main/install.sh | sudo COMPANION_BUILD=stable bash
sudo systemctl enable --now companion
```

Non-interactive stable pick uses the Bitfocus package API
(`linux-tgz` → e.g. Companion **v5.0.5**).

### Useful commands

```bash
sudo systemctl status companion
sudo systemctl restart companion
# Official updater (interactive version menu unless args given)
sudo companion-update
```

### Admin UI

Open: http://127.0.0.1:8000

Satellite (remote surfaces): TCP **16622**, WebSocket **16623**.

### USB surfaces (udev)

Companion 4.3+ generates udev rules at runtime. On first surface use, follow
the in-UI prompt, or copy generated rules from the Companion config tree into
`/etc/udev/rules.d/` and reload:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Do **not** run Elgato Stream Deck software and Companion against the same
device at once.

## Alternate: desktop tarball (no system service)

```bash
# Example URI from api.bitfocus.io (version changes over time)
mkdir -p "$HOME/.local/share/companion"
curl -L -o /tmp/companion.tgz \
  'https://cf-pub.bitfocus.io/companion/companion/companion-linux-x64-5.0.5-9736-stable-0293f0d1ee.tar.gz'
tar -xzf /tmp/companion.tgz -C "$HOME/.local/share/companion" --strip-components=1
# Then run companion-launcher from the extract (see tarball README)
```

## Alternate: container (no USB)

USB passthrough is not supported by upstream Docker notes. Use for admin UI
experiments only; use Companion Satellite from a machine that has the deck.

```bash
podman run -d --name companion \
  -p 8000:8000 -p 16622:16622 -p 16623:16623 \
  -v companion-config:/companion \
  ghcr.io/bitfocus/companion/companion:latest
```

## Install record (this machine)

| Item | Value |
|------|--------|
| Method | Desktop **user** install (`./install.sh --user --force`) |
| Version | **5.0.5+9736-stable-0293f0d1ee** |
| Path | `/home/jeff/.local/share/companion` |
| Launcher | `/home/jeff/.local/share/companion/companion-launcher` |
| Headless | `/home/jeff/.local/share/companion/companion_headless.sh` |
| Menu entry | `~/.local/share/applications/companion.desktop` |
| Admin UI | http://127.0.0.1:8000 |
| Tarball cache | `vendor/companion-linux-x64-5.0.5.tar.gz` (gitignored) |

### Launch

```bash
# Desktop tray / GUI
~/.local/share/companion/companion-launcher
# or with GTK workaround if needed:
~/.local/share/companion/companion-launcher --gtk-version=3

# Headless (admin UI only)
~/.local/share/companion/companion_headless.sh
```

Project helper: `scripts/run-companion-headless.sh`

### USB Stream Deck on this host

**Done:** desktop udev rules installed to `/etc/udev/rules.d/50-companion.rules`
(via `pkexec`). Device `streamdeck:A00WA6111L5B9C` (**Stream Deck+**) opens.

If USB access breaks after a Companion surface-module change, re-copy:

```bash
sudo cp ~/.config/companion-nodejs/udev-rules/50-companion-desktop.rules \
  /etc/udev/rules.d/50-companion.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Demo page on the deck

```bash
# Companion must already be running
./scratch/venv/bin/python scripts/demo_paint_buttons.py
# then restart headless so the deck redraws
kill "$(cat scratch/companion.pid)"; scripts/run-companion-headless.sh
```

Admin UI: http://127.0.0.1:8000/

### Optional later

- CompanionPi **system** service (`sudo COMPANION_BUILD=stable bash …`) — not required
  for lab; user install is enough.
