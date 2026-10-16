#!/usr/bin/env bash
# Start/stop the interim rotator simulator. Usage: run-rotator-sim.sh [start|stop|restart]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/scratch"; mkdir -p "$S"
PID="$S/rotator-sim.pid"; LOG="$S/rotator-sim.log"
stop() { if [[ -f $PID ]] && kill -0 "$(cat $PID)" 2>/dev/null; then kill "$(cat $PID)"; echo "Stopped sim"; fi; rm -f "$PID"; }
start() {
  if [[ -f $PID ]] && kill -0 "$(cat $PID)" 2>/dev/null; then echo "Sim already running (pid $(cat $PID))"; return; fi
  nohup python3 "$ROOT/scripts/rotator_sim.py" "$@" >"$LOG" 2>&1 &
  echo $! >"$PID"; echo "Started sim pid $(cat $PID) on http://127.0.0.1:8790/rotators (log $LOG)"
}
case "${1:-start}" in
  start) shift || true; start "$@";; stop) stop;; restart) shift; stop; sleep 0.5; start "$@";;
  *) echo "usage: $0 [start|stop|restart]"; exit 1;;
esac
