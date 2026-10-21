import asyncio
import os
import subprocess
import sys

import pytest

from meridian.api import Run, Runtime
from meridian.engine import Engine
from meridian.simulation import events
from meridian.store import Store


def test_real_process_crash_preserves_atomic_commits(tmp_path):
    path = str(tmp_path / "crash.sqlite")
    script = """import os
from meridian.store import Store
s=Store(os.environ['CRASH_DB'])
s.create('killed', {'streams':3}, 0)
s.append('killed', 0, [{'kind':'tick','time':0}], {'estimate':1})
with s.connect() as db:
 db.execute("INSERT INTO batches VALUES (?,?,?,?)", ('killed',1,'[]','{}'))
 os._exit(17)
"""
    child = subprocess.run([sys.executable, "-c", script], env={**os.environ, "CRASH_DB": path})
    assert child.returncode == 17
    s = Store(path)
    assert s.runs()[0]["status"] == "interrupted"
    assert len(s.batches("killed")) == 1


def test_slow_consumer_is_bounded_and_replay_survives(tmp_path):
    async def exercise():
        r = Runtime(str(tmp_path / "slow.sqlite"), "synthetic-test-password")
        q = asyncio.Queue(maxsize=2)
        r.subscribers[q] = 0
        config = Run(ticks=12)
        r.store.create("slow", config.model_dump(), 0)
        await r.produce("slow", config)
        assert q.qsize() == 2 and r.metrics["viewer_drops_total"] == 10
        assert len(r.store.batches("slow")) == 12
        assert q.get_nowait()["skipped"] == 9

    asyncio.run(exercise())


def test_invalid_clock_and_total_source_loss():
    e = Engine()
    for ev in events(ticks=4):
        e.apply(ev)
    before = e.core.tick(1.0)
    after = e.core.tick(2.0)
    assert before.active == 0 and after.active == 0
    assert after.variance > before.variance
    assert after.estimate == before.estimate
    with pytest.raises(ValueError):
        e.core.tick(0.5)
