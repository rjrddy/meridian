"""Transactional event/frame history. One connection per operation, one process writer."""

import json
import sqlite3
from pathlib import Path

from meridian.engine import canonical


class Store:
    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, config TEXT NOT NULL,
                status TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS batches(run TEXT NOT NULL REFERENCES runs(id),
                seq INTEGER NOT NULL, events TEXT NOT NULL, frame TEXT NOT NULL,
                PRIMARY KEY(run,seq));
            CREATE TABLE IF NOT EXISTS station(id INTEGER PRIMARY KEY, value REAL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts(unit INTEGER, attempt INTEGER, outcome TEXT,
                PRIMARY KEY(unit,attempt));
            UPDATE runs SET status='interrupted' WHERE status='running';
            """)

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def create(self, run: str, config: dict, now: float) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO runs VALUES (?,?,?,?)", (run, canonical(config), "running", now)
            )

    def append(self, run: str, seq: int, events: list[dict], frame: dict) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO batches VALUES (?,?,?,?)",
                (run, seq, canonical(events), canonical(frame)),
            )

    def finish(self, run: str, status: str) -> None:
        with self.connect() as db:
            db.execute("UPDATE runs SET status=? WHERE id=?", (status, run))

    def runs(self) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,config,status,created FROM runs ORDER BY created DESC LIMIT 100"
            ).fetchall()
        return [dict(id=r[0], config=json.loads(r[1]), status=r[2], created=r[3]) for r in rows]

    def get_run(self, run: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT config,status FROM runs WHERE id=?", (run,)).fetchone()
        return {"config": json.loads(row[0]), "status": row[1]} if row else None

    def batches(self, run: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT events,frame FROM batches WHERE run=? ORDER BY seq", (run,)
            ).fetchall()
        return [dict(events=json.loads(e), frame=json.loads(f)) for e, f in rows]
