import time

import pytest
from fastapi.testclient import TestClient

from meridian.api import create_app
from meridian.store import Store


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "db.sqlite"), "synthetic-test-password")
    with TestClient(app) as c:
        yield c


def sign_in(client):
    result = client.post("/api/login", json={"password": "synthetic-test-password"})
    assert result.status_code == 200
    client.headers["x-csrf-token"] = result.json()["csrf"]


def test_auth_csrf_validation_and_limit(client):
    assert client.get("/api/runs").status_code == 401
    sign_in(client)
    csrf = client.headers.pop("x-csrf-token")
    assert client.post("/api/runs", json={}).status_code == 403
    client.headers["x-csrf-token"] = csrf
    assert client.post("/api/runs", json={"dropout": 1.1}).status_code == 422
    for _ in range(10):
        response = client.post("/api/login", json={"password": "incorrect-password"})
    assert response.status_code == 429


def test_live_persistence_replay_and_station(client):
    sign_in(client)
    with client.websocket_connect("/ws") as ws:
        ws.send_text(client.headers["x-csrf-token"])
        run = client.post("/api/runs", json={"ticks": 10}).json()["id"]
        packet = ws.receive_json()
        assert packet["run"] == run and packet["frame"]["active"] >= 1
        assert client.post("/api/runs", json={}).status_code == 409
        time.sleep(0.3)
    result = client.get(f"/api/runs/{run}/replay").json()
    assert result["identical"] and result["frames"] == 10
    assert result["recorded_sha256"] == result["replay_sha256"]
    station = client.post("/api/station").json()
    assert station["units"] == 1000 and station["statuses"]["timeout"] > 0
    assert client.get("/api/metrics").json()["frames_total"] == 10


def test_crash_recovery_and_transaction_uniqueness(tmp_path):
    path = str(tmp_path / "db.sqlite")
    store = Store(path)
    store.create("crashed", {"streams": 3}, 0)
    store.append("crashed", 0, [], {})
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        store.append("crashed", 0, [], {})
    restarted = Store(path)
    assert restarted.runs()[0]["status"] == "interrupted"
    assert len(restarted.batches("crashed")) == 1


def test_unauthenticated_websocket_denied(client):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws"):
        pass


def test_old_history_replay_survives_recent_list_limit(client):
    from meridian.engine import Engine
    from meridian.simulation import events

    sign_in(client)
    store = client.app.state.runtime.store
    store.create("old", {"streams": 3}, 0)
    recorded = list(events(ticks=1))
    engine = Engine()
    for event in recorded:
        frame = engine.apply(event)
    store.append("old", 0, recorded, frame)
    store.finish("old", "complete")
    with store.connect() as db:
        db.executemany(
            "INSERT INTO runs VALUES (?,?,?,?)",
            [(str(i), '{"streams":3}', "complete", i + 1) for i in range(101)],
        )
    assert "old" not in {r["id"] for r in store.runs()}
    result = client.get("/api/runs/old/replay")
    assert result.status_code == 200 and result.json()["identical"]
    assert result.json()["frames"] == 1
