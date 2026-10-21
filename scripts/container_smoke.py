"""Real HTTP and WebSocket acceptance check against a running Compose container."""

import http.cookiejar
import json
import os
import re
import time
import urllib.request

from websockets.sync.client import connect

jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
base = "http://127.0.0.1:8000"
csrf = ""


def request(path: str, payload: dict | None = None) -> dict | list:
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        base + path, data=body, headers={"Content-Type": "application/json", "X-CSRF-Token": csrf}
    )
    with client.open(req, timeout=10) as response:
        return json.load(response)


csrf = request("/api/login", {"password": os.environ["MERIDIAN_PASSWORD"]})["csrf"]
html = client.open(base).read().decode()
asset = re.search(r'src="([^\"]+\.js)"', html).group(1)
assert client.open(base + asset).status == 200
cookies = "; ".join(f"{c.name}={c.value}" for c in jar)
with connect(
    "ws://127.0.0.1:8000/ws", additional_headers={"Cookie": cookies}, open_timeout=10
) as ws:
    ws.send(csrf)
    run = request("/api/runs", {"ticks": 8})["id"]
    frames = []
    while len(frames) < 8:
        packet = json.loads(ws.recv(timeout=10))
        if "frame" in packet:
            assert packet["run"] == run
            frames.append(packet)
for _ in range(30):
    runs = request("/api/runs")
    if next(r for r in runs if r["id"] == run)["status"] == "complete":
        break
    time.sleep(0.1)
replay = request(f"/api/runs/{run}/replay")
assert replay["identical"] and replay["frames"] == 8
station = request("/api/station")
assert station["units"] == 1000
print(
    json.dumps(
        {
            "http_auth": True,
            "websocket_frames": len(frames),
            "static_asset": asset,
            "replay": replay,
            "seeded_units": station["units"],
        },
        indent=2,
    )
)
