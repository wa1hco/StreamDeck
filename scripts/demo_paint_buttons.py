#!/usr/bin/env python3
"""Paint a Stream Deck+ demo page in Companion.

Hardware map (Companion grid):
  rows 0–1  — 8 LCD keys (2×4)
  row 2     — touch strip (4 press regions)
  row 3     — 4 encoders

Demo behaviour:
  MODE (0,0) — multi-step SSB ↔ FM; brief strip toast
  ANT  (0,1) — multi-step UPR → LWR → BOTH; strip toast
  Strip      — toast text, else status line (mode | ant)
  Labels     — short single-line; fixed font (no wrap/shrink)

Requires Companion at http://127.0.0.1:8000/
Restart Companion after running so the deck redraws cleanly.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Need websockets: scratch/venv/bin/pip install websockets", file=sys.stderr)
    sys.exit(1)

TRPC = "ws://127.0.0.1:8000/trpc"
DB = Path.home() / ".config/companion-nodejs/v5.0/db.sqlite"
PAGE = 1

# Short LCD labels only — avoid wrap on 120px keys
LCD = {
    (0, 2): ("WORK", 0xFF9900),
    (0, 3): ("HALT", 0xCC0000),
    (1, 0): ("POINT", 0x9933CC),
    (1, 1): ("STOP", 0x555555),
    (1, 2): ("PARK", 0x777777),
    (1, 3): ("WIMS", 0x336699),
}

KNOBS = {
    (3, 0): ("VFO", 0x222222),
    (3, 1): ("PWR", 0x222222),
    (3, 2): ("AZ", 0x222222),
    (3, 3): ("VOL", 0x222222),
}

# fontsize = % of element height (Companion layered text); not pixels.
# Plus LCD keys are 120×120 px; font_px ≈ pct * height / 100 / 1.2
# Keep shrink ON so 4–5 letter labels are not truncated (see docs/button-font-sizing.md).
# Plus LCD 120px; ~42% fits 5-letter POINT on one line (see lessons-learned).
FONT_LCD = 42
FONT_STRIP = 70
FONT_KNOB = 50
FONT_SHRINK = True


def ev(value, *, expr: bool = False):
    return {"isExpression": expr, "value": value}


async def trpc(method: str, path: str, input_obj=None):
    async with websockets.connect(TRPC, open_timeout=5) as ws:
        params: dict = {"path": path}
        if input_obj is not None:
            params["input"] = input_obj
        await ws.send(json.dumps({"id": 1, "method": method, "params": params}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
        if "error" in msg:
            raise RuntimeError(f"{path}: {msg['error'].get('message')}")
        return msg.get("result", {}).get("data")


async def mut(path: str, input_obj):
    return await trpc("mutation", path, input_obj)


def grid_loc(row: int, col: int) -> dict:
    return {"pageNumber": PAGE, "row": row, "column": col}


def control_id_at(row: int, col: int) -> str:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA wal_checkpoint(PASSIVE)")
    page = json.loads(con.execute("select value from pages where id=1").fetchone()[0])
    con.close()
    return page["controls"][str(row)][str(col)]


TOAST_HOLD_S = 3  # strip takeover duration (seconds); not Companion wait (aborted on release)

async def ensure_vars():
    for name, default in (
        ("demo_toast", ""),
        ("demo_toast_until", "0"),
        ("demo_status", "SSB | LWR"),
        ("demo_mode_lbl", "SSB"),
        ("demo_ant_lbl", "LWR"),
    ):
        try:
            await mut("customVariables.create", {"name": name, "defaultVal": default})
        except RuntimeError:
            pass
        try:
            await mut("customVariables.setCurrent", {"name": name, "value": default})
        except RuntimeError:
            pass



async def style_face(
    control_id: str,
    *,
    text: str,
    bgcolor: int | str,
    fontsize: int,
    text_expr: bool = False,
    bg_expr: bool = False,
):
    # Default layered button ids from Companion 5.0
    box_id, text_id = "box0", "text0"
    await mut(
        "controls.styles.updateOption",
        {
            "controlId": control_id,
            "elementId": box_id,
            "key": "color",
            "value": ev(bgcolor, expr=bg_expr),
        },
    )
    for key, value in (
        ("text", ev(text, expr=text_expr)),
        ("fontsize", ev(fontsize)),
        ("fontsizeAllowShrink", ev(FONT_SHRINK)),
        ("color", ev(0xFFFFFF)),
    ):
        await mut(
            "controls.styles.updateOption",
            {
                "controlId": control_id,
                "elementId": text_id,
                "key": key,
                "value": value,
            },
        )

async def add_down_action(control_id: str, step_id: str, definition: str) -> str:
    entity_id = await mut(
        "controls.entities.add",
        {
            "controlId": control_id,
            "entityLocation": {"stepId": step_id, "setId": "down"},
            "ownerId": None,
            "connectionId": "internal",
            "entityType": "action",
            "entityDefinition": definition,
        },
    )
    if not entity_id:
        raise RuntimeError(f"add {definition} failed")
    return entity_id


async def set_action_opt(control_id: str, step_id: str, entity_id: str, key: str, value):
    await mut(
        "controls.entities.setOption",
        {
            "controlId": control_id,
            "entityLocation": {"stepId": step_id, "setId": "down"},
            "entityId": entity_id,
            "key": key,
            "value": value,
        },
    )


async def set_var_action(control_id: str, step_id: str, name: str, value: str, *, expr: bool = False):
    eid = await add_down_action(control_id, step_id, "custom_variable_set_value")
    await set_action_opt(control_id, step_id, eid, "name", ev(name))
    await set_action_opt(control_id, step_id, eid, "value", ev(value, expr=expr))


def steps_from_db(control_id: str) -> list[str]:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA wal_checkpoint(PASSIVE)")
    raw = con.execute("select value from controls where id=?", (control_id,)).fetchone()
    con.close()
    if not raw:
        return []
    val = json.loads(raw[0])
    return sorted(
        (val.get("steps") or {}).keys(),
        key=lambda s: int(s) if str(s).isdigit() else 0,
    )


async def ensure_steps(control_id: str, count: int) -> list[str]:
    steps = steps_from_db(control_id)
    while len(steps) < count:
        await mut("controls.steps.add", {"controlId": control_id})
        # Give Companion a moment to flush WAL
        await asyncio.sleep(0.05)
        new_steps = steps_from_db(control_id)
        if len(new_steps) <= len(steps):
            raise RuntimeError("steps.add failed")
        steps = new_steps
    return steps[:count]
async def new_button(row: int, col: int) -> str:
    await mut(
        "controls.resetControl",
        {"location": grid_loc(row, col), "newType": "button-layered"},
    )
    cid = control_id_at(row, col)
    try:
        await mut(
            "controls.setOptionsField",
            {"controlId": cid, "key": "canModifyStyleInApis", "value": True},
        )
    except RuntimeError:
        pass
    return cid


async def main():
    print("Custom variables…")
    await ensure_vars()

    print("Creating Plus grid controls…")
    for row in range(4):
        for col in range(4):
            await new_button(row, col)

    print("LCD keys…")
    for (row, col), (label, bg) in LCD.items():
        await style_face(control_id_at(row, col), text=label, bgcolor=bg, fontsize=FONT_LCD)

    # MODE / ANT: toast NEXT value. Hold via time_unix (Companion wait aborts on release).
    print("MODE cycle…")
    mode_id = await new_button(0, 0)
    mode_steps = await ensure_steps(mode_id, 2)
    # $(this:step) is 1-based (getActiveStepIndex()+1): step ids 0,1 → values 1,2
    await style_face(
        mode_id,
        text="$(this:step) == 1 ? 'SSB' : 'FM'",
        bgcolor="$(this:step) == 1 ? 26316 : 39168",
        fontsize=FONT_LCD,
        text_expr=True,
        bg_expr=True,
    )
    # Down actions run on the step you are ON (before advance) → toast NEXT
    for step_id, toast, mode_lbl in (
        (mode_steps[0], "FM", "FM"),
        (mode_steps[1], "SSB", "SSB"),
    ):
        await set_var_action(mode_id, step_id, "demo_toast", toast)
        await set_var_action(
            mode_id,
            step_id,
            "demo_toast_until",
            f"$(internal:time_unix) + {TOAST_HOLD_S}",
            expr=True,
        )
        await set_var_action(mode_id, step_id, "demo_mode_lbl", mode_lbl)
        await set_var_action(
            mode_id,
            step_id,
            "demo_status",
            f"'{mode_lbl} | ' + $(custom:demo_ant_lbl)",
            expr=True,
        )

    print("ANT cycle…")
    ant_id = await new_button(0, 1)
    ant_steps = await ensure_steps(ant_id, 3)
    # this:step values 1,2,3 for step ids 0,1,2
    await style_face(
        ant_id,
        text="$(this:step) == 1 ? 'UPR' : $(this:step) == 2 ? 'LWR' : 'BOTH'",
        bgcolor=0x008888,
        fontsize=FONT_LCD,
        text_expr=True,
    )
    for step_id, toast, ant_lbl in (
        (ant_steps[0], "LWR", "LWR"),
        (ant_steps[1], "BOTH", "BOTH"),
        (ant_steps[2], "UPR", "UPR"),
    ):
        await set_var_action(ant_id, step_id, "demo_toast", toast)
        await set_var_action(
            ant_id,
            step_id,
            "demo_toast_until",
            f"$(internal:time_unix) + {TOAST_HOLD_S}",
            expr=True,
        )
        await set_var_action(ant_id, step_id, "demo_ant_lbl", ant_lbl)
        await set_var_action(
            ant_id,
            step_id,
            "demo_status",
            f"$(custom:demo_mode_lbl) + ' | {ant_lbl}'",
            expr=True,
        )
    print("Touch strip…")
    strip_expr = (
        f"$(internal:time_unix) < $(custom:demo_toast_until) "
        f"? $(custom:demo_toast) : $(custom:demo_status)"
    )
    for col in range(4):
        await style_face(
            control_id_at(2, col),
            text=strip_expr,
            bgcolor=0x111111,
            fontsize=FONT_STRIP,
            text_expr=True,
        )
    print("Knobs…")
    for (row, col), (label, bg) in KNOBS.items():
        cid = control_id_at(row, col)
        await style_face(cid, text=label, bgcolor=bg, fontsize=FONT_KNOB)
        try:
            await mut(
                "controls.setOptionsField",
                {"controlId": cid, "key": "rotaryActions", "value": True},
            )
        except RuntimeError:
            pass

    await mut("customVariables.setCurrent", {"name": "demo_mode_lbl", "value": "SSB"})
    await mut("customVariables.setCurrent", {"name": "demo_ant_lbl", "value": "LWR"})
    await mut("customVariables.setCurrent", {"name": "demo_status", "value": "SSB | LWR"})
    await mut("customVariables.setCurrent", {"name": "demo_toast", "value": ""})
    await mut("customVariables.setCurrent", {"name": "demo_toast_until", "value": "0"})

    print("Done.")
    print('Restart: kill "$(cat scratch/companion.pid)"; scripts/run-companion-headless.sh')
    print(f"Press MODE or ANT — strip toasts NEXT value for ~{TOAST_HOLD_S}s.")

if __name__ == "__main__":
    asyncio.run(main())
