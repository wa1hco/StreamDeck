#!/usr/bin/env python3
"""Wire Stream Deck+ dials 0/1 to the upper/lower rotators (interim: rotator sim).

Run AFTER demo_paint_buttons.py (reuses its helpers; does not reset MODE/ANT).
Data path (no Companion modules needed): scripts/rotator_sim.py pushes
<rot>_az/_moving/_dir into Companion custom vars and watches <rot>_point_seq.
Dial press bumps <rot>_point_seq with <rot>_point_az = target.
"""
from __future__ import annotations
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import demo_paint_buttons as d  # noqa: E402
from demo_paint_buttons import ev, mut, control_id_at, new_button  # noqa: E402

EDIT_S = 5

# ---- Knob acceleration (tune on the deck; re-run this script after editing) ----
# Velocity = time since the previous detent, from Companion's ms clock unixNow().
# Tiers are (max_interval_ms, step_deg): first row whose interval is BELOW max_interval_ms wins.
# Slower than the last row => STEP_SLOW. Attack is instant; release decays (see DECAY_DIV).
ACCEL_TIERS = (
    (35, 15),   # < 35 ms/detent  : very fast spin
    (70, 10),   # < 70 ms
    (120, 5),   # < 120 ms        : brisk
    (200, 2),   # < 200 ms        : a little quicker than deliberate
)
STEP_SLOW = 1        # deg/detent for deliberate turns (>= last tier threshold)
IDLE_RESET_MS = 250  # pause longer than this => step snaps back to STEP_SLOW
DECAY_DIV = 2        # when the knob slows, step falls to max(new tier, previous step // DECAY_DIV)
# Direction reversal always resets the step to STEP_SLOW (libinput/mouse-style tracker reset).
ROTS = ((0, "upper", "UPR"), (1, "lower", "LWR"))
AMBER, WHITE, BLACK, GREEN = 0xFFB000, 0xFFFFFF, 0x000000, 0x004400


async def var(name, default):
    try:
        await mut("customVariables.create", {"name": name, "defaultVal": default})
    except RuntimeError:
        pass
    await mut("customVariables.setCurrent", {"name": name, "value": default})


async def add_action(cid, set_id, name, value, expr=True):
    loc = {"stepId": "0", "setId": set_id}
    eid = await mut("controls.entities.add", {
        "controlId": cid, "entityLocation": loc, "ownerId": None,
        "connectionId": "internal", "entityType": "action",
        "entityDefinition": "custom_variable_set_value"})
    for k, v in (("name", ev(name)), ("value", ev(value, expr=expr))):
        await mut("controls.entities.setOption", {
            "controlId": cid, "entityLocation": loc, "entityId": eid, "key": k, "value": v})


async def opt(cid, el, key, value, expr=False):
    await mut("controls.styles.updateOption", {
        "controlId": cid, "elementId": el, "key": key, "value": ev(value, expr=expr)})


def step_expr(n, sign):
    """Companion expression: new step (deg/detent) for this detent. Reads <n>_last_ms,
    <n>_last_dir, <n>_step (all updated AFTER tgt by the later actions)."""
    tier = str(STEP_SLOW)
    for ms, st in reversed(ACCEL_TIERS):
        tier = f"dt < {ms} ? {st} : {tier}"
    return (
        f"dt = unixNow() - $(custom:{n}_last_ms);\n"
        f"tier = {tier};\n"
        f"prev = $(custom:{n}_step);\n"
        f"(dt > {IDLE_RESET_MS} || $(custom:{n}_last_dir) != {sign}) ? {STEP_SLOW}"
        f" : max(tier, floor(prev / {DECAY_DIV}))"
    )


async def main():
    for _, n, _ in ROTS:
        for suf, dv in (("az", "0"), ("moving", "0"), ("dir", ""), ("tgt", "0"),
                        ("edit_until", "0"), ("last_ms", "0"), ("last_dir", "0"),
                        ("step", str(STEP_SLOW)), ("point_az", "0"), ("point_seq", "0")):
            await var(f"{n}_{suf}", dv)

    for col, n, lbl in ROTS:
        editing = f"($(internal:time_unix) < $(custom:{n}_edit_until))"
        # --- encoder ---
        cid = await new_button(3, col)
        await mut("controls.setOptionsField", {"controlId": cid, "key": "rotaryActions", "value": True})
        await d.style_face(cid, text=f"{lbl} AZ", bgcolor=0x222222, fontsize=d.FONT_KNOB)
        for set_id, sign in (("rotate_left", -1), ("rotate_right", 1)):
            # ORDER MATTERS (actions in a set run sequentially): step -> tgt -> bookkeeping.
            await add_action(cid, set_id, f"{n}_step", step_expr(n, sign))
            # seed from current az when not editing; wrap 0-359; left = + (360 - step)
            adj = f"$(custom:{n}_step)" if sign > 0 else f"(360 - $(custom:{n}_step))"
            await add_action(cid, set_id, f"{n}_tgt",
                             f"(({editing} ? $(custom:{n}_tgt) : $(custom:{n}_az)) + {adj}) % 360")
            await add_action(cid, set_id, f"{n}_edit_until", f"$(internal:time_unix) + {EDIT_S}")
            await add_action(cid, set_id, f"{n}_last_ms", "unixNow()")
            await add_action(cid, set_id, f"{n}_last_dir", str(sign))
        await add_action(cid, "down", f"{n}_point_az",
                         f"{editing} ? $(custom:{n}_tgt) : $(custom:{n}_az)")
        await add_action(cid, "down", f"{n}_point_seq", f"$(custom:{n}_point_seq) + 1")
        await add_action(cid, "down", f"{n}_edit_until", "0")
        # --- strip region above ---
        sid = control_id_at(2, col)
        toast = "($(internal:time_unix) < $(custom:demo_toast_until))"
        # NOTE: Companion's `+` is numeric-only ('a' + 'b' == NaN) -> build text with
        # template strings. Arrows: ↻ CW, ↺ CCW (check they render in companion-sans).
        arrow = f"($(custom:{n}_dir) == 'CW' ? ' ↻' : $(custom:{n}_dir) == 'CCW' ? ' ↺' : '')"
        text = (f"{toast} ? $(custom:demo_toast) : {editing} ? `{lbl} →${{$(custom:{n}_tgt)}}`"
                f" : `{lbl} ${{$(custom:{n}_az)}}${{$(custom:{n}_moving) == 1 ? {arrow} : ''}}`")
        await opt(sid, "text0", "text", text, expr=True)
        await opt(sid, "text0", "fontsize", d.FONT_STRIP)
        await opt(sid, "text0", "fontsizeAllowShrink", True)
        await opt(sid, "text0", "color", f"(!{toast} && {editing}) ? {AMBER} : {WHITE}", expr=True)
        await opt(sid, "box0", "color",
                  f"{toast} ? {0x111111} : (!{editing} && $(custom:{n}_moving) == 1) ? {GREEN} : {BLACK}",
                  expr=True)
    print("Dials wired. Start sim: scripts/run-rotator-sim.sh")

if __name__ == "__main__":
    asyncio.run(main())
