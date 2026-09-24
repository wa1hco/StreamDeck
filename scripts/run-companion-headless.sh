#!/usr/bin/env bash
# Start Bitfocus Companion headless (admin UI on :8000 by default).
set -euo pipefail

COMPANION_HOME="${COMPANION_HOME:-$HOME/.local/share/companion}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRATCH="${ROOT}/scratch"
mkdir -p "$SCRATCH"

if [[ ! -x "$COMPANION_HOME/resources/node-runtimes/main/bin/node" ]]; then
  echo "Companion not found at $COMPANION_HOME" >&2
  echo "See docs/companion-install.md" >&2
  exit 1
fi

if [[ -f "$SCRATCH/companion.pid" ]] && kill -0 "$(cat "$SCRATCH/companion.pid")" 2>/dev/null; then
  echo "Companion already running (pid $(cat "$SCRATCH/companion.pid"))"
  echo "Admin UI: http://127.0.0.1:8000/"
  exit 0
fi

cd "$COMPANION_HOME/resources"
./node-runtimes/main/bin/node main.js "$@" \
  >"$SCRATCH/companion-headless.log" 2>&1 &
echo $! >"$SCRATCH/companion.pid"
echo "Started Companion pid $(cat "$SCRATCH/companion.pid")"
echo "Log: $SCRATCH/companion-headless.log"
echo "Admin UI: http://127.0.0.1:8000/"
