"""Replay public Intel Lab temperature records; no ground-truth accuracy claim."""

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path

from meridian.engine import Engine, canonical, digest

parser = argparse.ArgumentParser()
parser.add_argument("archive", type=Path, help="MIT data.txt.gz, downloaded separately")
args = parser.parse_args()
rows = []
with gzip.open(args.archive, "rt") as data:
    for line in data:
        fields = line.split()
        if len(fields) != 8:
            continue
        try:
            sensor = int(fields[3])
            timestamp = dt.datetime.fromisoformat(fields[0] + "T" + fields[1]).timestamp()
            value = float(fields[4])
        except ValueError:
            continue
        if sensor in (1, 2, 3) and math.isfinite(value) and -10 <= value <= 60:
            rows.append({"stream": sensor - 1, "time": timestamp, "value": value})
        if len(rows) == 900:
            break
rows.sort(key=lambda r: (r["time"], r["stream"]))
origin = rows[0]["time"]
engine = Engine(3, max_age=60.0)
events, frames = [], []
for i in range(3):
    e = {"kind": "calibrate", "stream": i, "sensor": 0.0, "reference": 0.0, "variance": 0.25}
    events.append(e)
    engine.apply(e)
for n, row in enumerate(rows):
    e = {"kind": "sample", **row, "time": row["time"] - origin}
    events.append(e)
    engine.apply(e)
    if n == len(rows) - 1 or rows[n + 1]["time"] != row["time"]:
        e = {"kind": "tick", "time": row["time"] - origin}
        events.append(e)
        frames.append(engine.apply(e))
replay = Engine(3, max_age=60.0)
replayed = [replay.apply(e) for e in events]
replayed = [f for f in replayed if f is not None and "estimate" in f]
assert canonical(frames) == canonical(replayed)
result = {
    "source": "https://db.csail.mit.edu/labdata/data.txt.gz",
    "description": "https://db.lcs.mit.edu/labdata/labdata.html",
    "source_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
    "records": len(rows),
    "streams": 3,
    "frames": len(frames),
    "bit_identical": True,
    "frame_sha256": digest(frames),
    "accuracy": "not measured: no shared ground truth",
    "limits": "Temperatures at different lab locations are not identical physical signals. Replay compatibility only. Clock timestamps treated as a common reference, no drift estimation.",
    "redistribution": "Original archive not bundled; download from MIT. No explicit reuse license identified on source page.",
}
Path("docs/results/public-replay.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
