#!/usr/bin/env python3
"""Interim rotator simulator (stands in for WIMS). Stdlib only.

Two rotators, 'upper' and 'lower', turning 6 deg/s (360 deg/min) along the
shortest path. HTTP on 127.0.0.1:8790:
  GET  /rotators                    JSON for both
  GET  /rotator/<name>              JSON for one
  GET  /rotator/<name>/az           plain integer az
  POST /rotator/<name>/point {"az":N}  or GET /rotator/<name>/point?az=N
  POST|GET /rotator/<name>/stop

Companion bridge (--companion, default http://127.0.0.1:8000; '' disables):
  pushes custom vars <name>_az, <name>_moving (0/1), <name>_dir (CW/CCW/'')
  polls custom vars <name>_point_seq / <name>_point_az; a new seq => point.
"""
from __future__ import annotations
import argparse, json, threading, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RATE = 6.0
LOCK = threading.Lock()
ROT = {n: {"az": 0.0, "target": None} for n in ("upper", "lower")}


def tick(dt):
    with LOCK:
        for r in ROT.values():
            t = r["target"]
            if t is None:
                continue
            diff = (t - r["az"] + 540) % 360 - 180
            step = RATE * dt
            if abs(diff) <= step:
                r["az"], r["target"], r["dir"] = float(t), None, ""
            else:
                r["dir"] = "CW" if diff > 0 else "CCW"
                r["az"] = (r["az"] + (step if diff > 0 else -step)) % 360


def view(n):
    r = ROT[n]
    t = r["target"]
    return {"name": n, "az": int(round(r["az"])) % 360, "target": t,
            "moving": t is not None, "direction": r.get("dir", "") if t is not None else ""}


def point(n, az):
    with LOCK:
        ROT[n]["target"] = int(az) % 360
    print(f"point {n} -> {int(az) % 360}", flush=True)


def stop(n):
    with LOCK:
        ROT[n]["target"] = None
    print(f"stop {n}", flush=True)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        b = (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def route(self, body=None):
        u = urllib.parse.urlparse(self.path)
        parts = [p for p in u.path.split("/") if p]
        q = urllib.parse.parse_qs(u.query)
        if parts == ["rotators"]:
            with LOCK:
                return self.send(200, {n: view(n) for n in ROT})
        if len(parts) >= 2 and parts[0] == "rotator" and parts[1] in ROT:
            n = parts[1]
            act = parts[2] if len(parts) > 2 else ""
            if act == "":
                with LOCK:
                    return self.send(200, view(n))
            if act == "az":
                with LOCK:
                    return self.send(200, str(view(n)["az"]), "text/plain")
            if act == "point":
                az = (body or {}).get("az", q.get("az", [None])[0])
                try:
                    point(n, int(float(az)))
                except (TypeError, ValueError):
                    return self.send(400, {"error": "az required"})
                with LOCK:
                    return self.send(200, view(n))
            if act == "stop":
                stop(n)
                with LOCK:
                    return self.send(200, view(n))
        self.send(404, {"error": "not found"})

    def do_GET(self):
        self.route()

    def do_POST(self):
        ln = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(ln) if ln else b""
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            body = dict(urllib.parse.parse_qsl(raw.decode()))
        self.route(body)


def bridge(base):
    def get(name):
        with urllib.request.urlopen(f"{base}/api/custom-variable/{name}/value", timeout=2) as r:
            return r.read().decode().strip()

    def put(name, val):
        req = urllib.request.Request(
            f"{base}/api/custom-variable/{name}/value?value={urllib.parse.quote(str(val))}",
            method="POST")
        urllib.request.urlopen(req, timeout=2).read()

    last_seq, pushed = {}, {}
    while True:
        try:
            for n in ROT:
                seq = get(f"{n}_point_seq")
                if n not in last_seq:
                    last_seq[n] = seq  # ignore stale request at startup
                elif seq != last_seq[n]:
                    last_seq[n] = seq
                    try:
                        point(n, int(float(get(f"{n}_point_az"))))
                    except ValueError:
                        pass
                with LOCK:
                    v = view(n)
                for k, val in ((f"{n}_az", v["az"]), (f"{n}_moving", int(v["moving"])),
                               (f"{n}_dir", v["direction"])):
                    if pushed.get(k) != val:
                        put(k, val)
                        pushed[k] = val
        except Exception as e:  # Companion down/restarting
            pushed.clear()
            last_seq.clear()
            print(f"bridge: {e}", flush=True)
            time.sleep(2)
        time.sleep(0.25)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--companion", default="http://127.0.0.1:8000")
    a = ap.parse_args()

    def mover():
        last = time.monotonic()
        while True:
            time.sleep(0.1)
            now = time.monotonic()
            tick(now - last)
            last = now
    threading.Thread(target=mover, daemon=True).start()
    if a.companion:
        threading.Thread(target=bridge, args=(a.companion.rstrip("/"),), daemon=True).start()
    print(f"rotator sim on 127.0.0.1:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
