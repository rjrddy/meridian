"""Synthetic calibrated clocks and loss; no employer or personal data."""

import math
import random
from collections.abc import Iterator


def events(
    seed: int = 42, dropout: float = 0, ticks: int = 300, streams: int = 3
) -> Iterator[dict]:
    rng = random.Random(seed)
    for i in range(streams):
        yield {
            "kind": "calibrate",
            "stream": i,
            "sensor": 10 + i * 0.137,
            "reference": 10,
            "variance": (0.08 + i * 0.04) ** 2,
        }
    for n in range(ticks):
        t = n * 0.02
        for i in range(streams):
            if rng.random() >= dropout:
                yield {
                    "kind": "sample",
                    "stream": i,
                    "time": t + i * 0.137,
                    "value": math.sin(t) + rng.gauss(0, 0.08 + i * 0.04),
                }
        yield {"kind": "tick", "time": t, "truth": math.sin(t)}
