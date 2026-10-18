#!/usr/bin/env python3
"""Drive dial rotate via Companion's HTTP API at set rates; print tgt/step per detent.

Usage: tools/dev/test_knob_accel.py [dial] [bursts]   (default: all scenarios on dial 0, 'upper';
       "bursts" runs only the repeated-flick consistency test)
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


def bursts_run(col, title, gaps, pauses, tail_clicks=()):
    """Repeated flicks on a fixed wall-clock grid. gaps = ms between detents inside one burst
    (len = detents-1); pauses = ms between bursts; tail_clicks = optional slow clicks appended to
    the LAST burst (ms gaps) to check landing/fine-adjust. Prints the step used per detent."""
    n = NAMES[col]
    time.sleep(6)
    print(f"\n== {title}: gaps={gaps} pauses={list(pauses)} (dial {col}/{n})")
    t = time.monotonic()
    out = []
    for b in range(len(pauses) + 1):
        if b:
            t += pauses[b - 1] / 1000
        g = list(gaps) + (list(tail_clicks) if b == len(pauses) else [])
        steps = []
        for i in range(len(g) + 1):
            if i:
                t += g[i - 1] / 1000
            w = t - time.monotonic()
            if w > 0:
                time.sleep(w)
            rotate(col, "right")
            steps.append(int(float(var(n, "step"))))  # POST returns after the actions ran
            t = max(t, time.monotonic() - 0.005)      # if we fell behind, don't catch up
        out.append(steps)
        print(f"  burst {b+1}: steps={steps} total={sum(steps)} deg first3={sum(steps[:3])}")
    return out


FLICK = [80, 60, 45, 35, 35, 50, 80, 130]   # human-ish flick: ramps up then slows down
FAST = [30] * 7


if __name__ == "__main__":
    col = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 0
    if "bursts" in sys.argv:
        bursts_run(col, "A: hard flicks @30ms", FAST, (400, 1000, 400, 150))
        bursts_run(col, "B: human flicks (ramp up/down)", FLICK, (400, 1000, 400, 150))
        bursts_run(col, "C: flick, 500ms pause, flick, 500ms pause, flick + 3 deliberate clicks @300ms",
                   FLICK, (500, 500), (300, 300, 300))
        bursts_run(col, "D: pure deliberate clicks @300ms (must stay 1)", [300] * 5, ())
        sys.exit(0)
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
