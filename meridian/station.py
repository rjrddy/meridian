"""Adapted R4 timeout/retry model; atomic persisted measurement batches."""

import random

from meridian.store import Store


def measure(store: Store, count: int = 1000) -> dict:
    rng = random.Random(42)
    with store.connect() as db:
        db.execute("DELETE FROM attempts")
        db.execute("DELETE FROM station")
        for unit in range(count):
            value, measured = rng.gauss(10, 0.5), None
            for attempt in range(1, 4):
                timeout = unit % 101 == 0 or (unit % 17 == 0 and attempt == 1)
                db.execute(
                    "INSERT INTO attempts VALUES (?,?,?)",
                    (unit, attempt, "timeout" if timeout else "ok"),
                )
                if not timeout:
                    measured = value
                    break
            status = (
                "timeout"
                if measured is None
                else ("pass" if 9 <= measured <= 11 else "out-of-spec")
            )
            db.execute("INSERT INTO station VALUES (?,?,?,?)", (unit, measured, status, attempt))
    return report(store)


def report(store: Store) -> dict:
    with store.connect() as db:
        counts = dict(db.execute("SELECT status,count(*) FROM station GROUP BY status"))
        attempts = db.execute('SELECT count(*) FROM attempts WHERE outcome="timeout"').fetchone()[0]
    total = sum(counts.values())
    return dict(
        units=total,
        statuses=counts,
        yield_percent=100 * counts.get("pass", 0) / total if total else 0,
        timeout_attempts=attempts,
    )
