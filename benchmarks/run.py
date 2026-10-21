"""Save raw inputs/frames/timings; no sleeps hidden in throughput measurements."""

import json
import math
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

from meridian.engine import Engine, canonical, digest
from meridian.simulation import events
from meridian.station import measure
from meridian.store import Store

out = Path("docs/results")
out.mkdir(parents=True, exist_ok=True)
summary = {"environment": {"python": sys.version, "platform": platform.platform()}, "dropout": []}
for dropout in (0.0, 0.1, 0.3):
    engine = Engine()
    recorded = list(events(dropout=dropout, ticks=3000))
    frames, times = [], []
    started = time.perf_counter_ns()
    for event in recorded:
        t = time.perf_counter_ns()
        result = engine.apply(event)
        times.append((time.perf_counter_ns() - t) / 1e6)
        if event["kind"] == "tick":
            frames.append(result)
    elapsed = (time.perf_counter_ns() - started) / 1e9
    replay = Engine()
    replayed = [replay.apply(e) for e in recorded if e["kind"] != "tick" or True]
    reproduced = [f for f in replayed if f is not None and "estimate" in f]
    assert canonical(frames) == canonical(reproduced)
    rmse = math.sqrt(statistics.mean((f["estimate"] - f["truth"]) ** 2 for f in frames))
    row = {
        "dropout": dropout,
        "ticks": len(frames),
        "input_events": len(recorded),
        "rmse": rmse,
        "event_p50_ms": float(np.quantile(times, 0.5)),
        "event_p99_ms": float(np.quantile(times, 0.99)),
        "events_per_second": len(recorded) / elapsed,
        "bit_identical": True,
        "sha256": digest(frames),
    }
    assert rmse < 0.15, "Declared synthetic accuracy budget exceeded"
    summary["dropout"].append(row)
    (out / f"dropout-{int(dropout * 100)}.json").write_text(
        canonical({"events": recorded, "frames": frames, "event_ms": times}) + "\n"
    )
with tempfile.TemporaryDirectory() as directory:
    store = Store(str(Path(directory) / "bench.sqlite"))
    engine = Engine()
    store.create("durable", {"streams": 3}, 0)
    batch, times, seq = [], [], 0
    for event in events(ticks=1000):
        # Start at the first source/calibration event in the batch, not just at tick.
        if not batch:
            started = time.perf_counter_ns()
        batch.append(event)
        frame = engine.apply(event)
        if event["kind"] == "tick":
            store.append("durable", seq, batch, frame)
            times.append((time.perf_counter_ns() - started) / 1e6)
            batch, seq = [], seq + 1
    summary["durable"] = {
        "ticks": seq,
        "batch_p50_ms": float(np.quantile(times, 0.5)),
        "batch_p99_ms": float(np.quantile(times, 0.99)),
        "boundary": "first batch input through SQLite commit; no network or browser",
    }
    (out / "durable-samples.json").write_text(canonical(times) + "\n")
    summary["station"] = measure(store)
(out / "benchmark.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
