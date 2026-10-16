#!/usr/bin/env python3
"""Drive dial rotate via Companion's HTTP API at set rates; print tgt/step per detent.

Usage: test_knob_accel.py            (runs the built-in scenarios on dial 0, 'upper')
Needs Companion up and wire_rotator_knobs.py applied. Pacing is wall-clock (+HTTP latency).
"""
import sys, time, urllib.request
BASE = "http://127.0.0.1:8000"
PAGE, ROW = 1, 3
NAMES = {0: "upper", 1: "lower"}


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return r.read().decode().strip()


def var(n, k):
    return get(f"/api/custom-variable/{n}_{k}/value")


def rotate(col, direction):
    urllib.request.urlopen(urllib.request.Request(
        f"{BASE}/api/location/{PAGE}/{ROW}/{col}/rotate-{direction}", method="POST"), timeout=5).read()


def scenario(col, title, seq):
    """seq: list of (direction, gap_ms_before)."""
    n = NAMES[col]
    time.sleep(6)  # let edit window expire -> next turn seeds from current az
    print(f"\n== {title} (dial {col}/{n}) az={var(n,'az')}")
    prev = None
    for d, gap in seq:
        time.sleep(gap / 1000)
        t0 = time.monotonic()
        rotate(col, d)
        time.sleep(0.03)  # let action chain finish
        tgt = int(float(var(n, "tgt")))
        step = var(n, "step")
        delta = "" if prev is None else f"delta={(tgt - prev + 540) % 360 - 180:+d}"
        print(f"  {d:5s} gap={gap:4d}ms -> tgt={tgt:3d} step={step:>3s} {delta}")
        prev = tgt


if __name__ == "__main__":
    col = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    scenario(col, "slow deliberate 300ms x4 right", [("right", 0)] + [("right", 300)] * 3)
    scenario(col, "brisk 100ms x8 right", [("right", 0)] + [("right", 100)] * 7)
    scenario(col, "very fast 25ms x12 right", [("right", 0)] + [("right", 25)] * 11)
    scenario(col, "fast then slow-down (decay): 25ms x6, then 150ms x4, then 300ms x2",
             [("right", 0)] + [("right", 25)] * 5 + [("right", 150)] * 4 + [("right", 300)] * 2)
    scenario(col, "pause reset: 25ms x5, wait 600ms, 25ms x3",
             [("right", 0)] + [("right", 25)] * 4 + [("right", 600)] + [("right", 25)] * 2)
    scenario(col, "reversal: 25ms x5 right then 25ms x4 left",
             [("right", 0)] + [("right", 25)] * 4 + [("left", 25)] * 4)
    scenario(col, "wrap CCW across 0: 25ms x10 left", [("left", 0)] + [("left", 25)] * 9)
