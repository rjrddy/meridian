import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from meridian._fusion import Fusion

from meridian.engine import Engine, canonical
from meridian.simulation import events


def test_replay_and_dropout():
    for dropout in (0, 0.1, 0.3):
        a, b = Engine(), Engine()
        recorded = list(events(dropout=dropout))
        assert canonical([a.apply(e) for e in recorded]) == canonical(
            [b.apply(e) for e in recorded]
        )


def test_late_overflow_and_no_future_leakage():
    f = Fusion(1, 2)
    f.calibrate(0, 1, 0, 0.01)
    for t in (1.0, 2.0, 3.0):
        assert f.ingest(0, t, t)
    assert f.health()[0]["overflow"] == 1
    assert not f.ingest(0, 2.0, 2.0)
    assert f.tick(0.5).active == 0
    assert f.tick(1.0).active == 1
    assert f.tick(2.0).active == 1
    frame = f.tick(3.0)
    assert frame.active == 0 and frame.initialized
    with pytest.raises(ValueError):
        f.tick(3.0)


def test_invalid_and_uncalibrated_fail_closed():
    f = Fusion(1)
    with pytest.raises(ValueError):
        f.ingest(0, 0, 0)
    f.calibrate(0, 0, 0, 0.01)
    for value in (math.nan, math.inf):
        with pytest.raises(ValueError):
            f.ingest(0, 1, value)
    with pytest.raises(ValueError):
        f.calibrate(0, 0, 0, 0.01)


@given(st.lists(st.floats(min_value=-1e4, max_value=1e4, allow_nan=False), min_size=1, max_size=50))
def test_bounded_memory_and_finite_prediction(values):
    f = Fusion(1, 4)
    f.calibrate(0, 0, 0, 0.1)
    for n, value in enumerate(values):
        f.ingest(0, float(n), value)
        assert f.health()[0]["buffered"] <= 4
        frame = f.tick(float(n))
        assert math.isfinite(frame.estimate) and frame.variance >= 0
