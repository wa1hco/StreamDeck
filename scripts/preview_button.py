#!/usr/bin/env python3
"""Save Companion's rendered PNG of a grid location (what the deck draws).
Usage: preview_button.py ROW COL [out.png]   (page 1)
"""
from __future__ import annotations
import asyncio, base64, json, sys
import websockets

TRPC = "ws://127.0.0.1:8000/trpc"

async def grab(row, col, page=1):
    async with websockets.connect(TRPC, open_timeout=5) as ws:
        await ws.send(json.dumps({"id": 1, "method": "subscription", "params": {
            "path": "preview.graphics.location",
            "input": {"location": {"pageNumber": page, "row": row, "column": col}}}}))
        for _ in range(10):
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
            if "error" in msg:
                raise RuntimeError(msg["error"])
            data = msg.get("result", {}).get("data")
            if isinstance(data, dict) and "image" in data:
                await ws.send(json.dumps({"id": 1, "method": "subscription.stop"}))
                img = data["image"]
                return base64.b64decode(img.split(",", 1)[-1]) if isinstance(img, str) else img
    raise RuntimeError("no image")

if __name__ == "__main__":
    r, c = int(sys.argv[1]), int(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 else f"scratch/preview_{r}_{c}.png"
    open(out, "wb").write(asyncio.run(grab(r, c)))
    print(out)
