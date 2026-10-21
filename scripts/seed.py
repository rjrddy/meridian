"""Seed a persisted synthetic run and instrument batch without a running HTTP service."""

import os
import time

from meridian.engine import Engine
from meridian.simulation import events
from meridian.station import measure
from meridian.store import Store

store = Store(os.environ.get("MERIDIAN_DB", "data/meridian.sqlite"))
if not store.runs():
    store.create(
        "seed-synthetic", {"streams": 3, "ticks": 300, "seed": 42, "dropout": 0.1}, time.time()
    )
    engine, batch, seq = Engine(), [], 0
    for event in events(dropout=0.1):
        batch.append(event)
        frame = engine.apply(event)
        if event["kind"] == "tick":
            store.append("seed-synthetic", seq, batch, frame)
            batch, seq = [], seq + 1
    store.finish("seed-synthetic", "complete")
    print({"seeded_run": "seed-synthetic", "frames": seq})
print(measure(store))
