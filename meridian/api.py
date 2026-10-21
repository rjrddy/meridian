"""Authenticated single-process control plane with durable-before-broadcast ordering."""

import asyncio
import hashlib
import hmac
import logging
import os
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from meridian.engine import Engine, canonical, digest
from meridian.simulation import events
from meridian.station import measure, report
from meridian.store import Store

log = logging.getLogger("meridian")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
log.setLevel(logging.INFO)
log.propagate = False


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=256)


class Run(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    seed: int = Field(default=42, ge=0, le=2147483647)
    dropout: float = Field(default=0, ge=0, le=0.9, allow_inf_nan=False)
    ticks: int = Field(default=300, ge=1, le=3000)
    streams: int = Field(default=3, ge=1, le=16)


class Runtime:
    def __init__(self, path: str, password: str) -> None:
        self.store = Store(path)
        self.salt = secrets.token_bytes(16)
        self.password_hash = self.hash(password)
        self.sessions: dict[str, tuple[float, str]] = {}
        self.budgets: dict[str, deque] = {}
        self.subscribers: dict[asyncio.Queue, int] = {}
        self.task: asyncio.Task | None = None
        self.metrics = defaultdict(int)

    def hash(self, password: str) -> bytes:
        return hashlib.scrypt(password.encode(), salt=self.salt, n=16384, r=8, p=1)

    def limit(self, key: str, maximum: int) -> None:
        now = time.monotonic()
        # Bound attacker-controlled client-key memory; expiry uses monotonic time.
        for k in list(self.budgets):
            if not self.budgets[k] or now - self.budgets[k][-1] > 60:
                del self.budgets[k]
        if key not in self.budgets and len(self.budgets) >= 2048:
            raise HTTPException(429, "rate limit capacity")
        q = self.budgets.setdefault(key, deque())
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= maximum:
            raise HTTPException(429, "rate limited")
        q.append(now)

    def session(self, token: str | None) -> tuple[float, str]:
        session = self.sessions.get(token or "")
        if not session or session[0] < time.monotonic():
            self.sessions.pop(token or "", None)
            raise HTTPException(401, "sign in required")
        return session

    async def produce(self, run_id: str, config: Run) -> None:
        engine = Engine(config.streams)
        batch, seq, sample_count = [], 0, 0
        status = "complete"
        try:
            for event in events(**config.model_dump()):
                if not batch:
                    started = time.perf_counter_ns()
                    capture_wall = time.time()
                batch.append(event)
                if event["kind"] == "sample":
                    sample_count += 1
                frame = engine.apply(event)
                if event["kind"] != "tick":
                    continue
                assert frame is not None
                await asyncio.to_thread(self.store.append, run_id, seq, batch, frame)
                commit_ms = (time.perf_counter_ns() - started) / 1e6
                packet = dict(
                    run=run_id,
                    seq=seq,
                    frame=frame,
                    commit_ms=commit_ms,
                    sent_at=time.time(),
                    captured_at=capture_wall,
                    samples_total=sample_count,
                    trace_id=run_id,
                )
                self.metrics["frames_total"] += 1
                for queue in list(self.subscribers):
                    if queue.full():
                        queue.get_nowait()
                        self.subscribers[queue] += 1
                        self.metrics["viewer_drops_total"] += 1
                    queue.put_nowait(dict(packet, skipped=self.subscribers[queue]))
                seq += 1
                batch = []
                await asyncio.sleep(0.02)
        except asyncio.CancelledError:
            status = "cancelled"
            raise
        except Exception:
            status = "failed"
            log.exception(canonical(dict(event="run_failed", run=run_id)))
        finally:
            self.store.finish(run_id, status)
            log.info(canonical(dict(event="run_finished", run=run_id, status=status, frames=seq)))


def create_app(path: str | None = None, password: str | None = None) -> FastAPI:
    secret = password or os.environ.get("MERIDIAN_PASSWORD", "")
    if len(secret) < 12:
        raise RuntimeError("Set MERIDIAN_PASSWORD to at least twelve characters")
    runtime = Runtime(path or os.environ.get("MERIDIAN_DB", "data/meridian.sqlite"), secret)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if runtime.task and not runtime.task.done():
            runtime.task.cancel()
            try:
                await runtime.task
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="Meridian", lifespan=lifespan)
    app.state.runtime = runtime

    def auth(request: Request) -> tuple[float, str]:
        session = runtime.session(request.cookies.get("session"))
        if request.method not in ("GET", "HEAD"):
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), session[1]):
                raise HTTPException(403, "CSRF token required")
            runtime.limit("write:" + str(request.client.host if request.client else "local"), 30)
        return session

    Secure = Annotated[tuple[float, str], Depends(auth)]

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 8192:
                    return Response(status_code=413)
            request._body = bytes(body)
        trace = secrets.token_hex(8)
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        log.info(
            canonical(
                dict(event="http", trace=trace, method=request.method, status=response.status_code)
            )
        )
        return response

    @app.post("/api/login")
    async def login(body: Login, request: Request, response: Response) -> dict:
        runtime.limit("login:" + str(request.client.host if request.client else "local"), 10)
        if not hmac.compare_digest(
            await asyncio.to_thread(runtime.hash, body.password), runtime.password_hash
        ):
            raise HTTPException(401, "invalid credentials")
        now = time.monotonic()
        runtime.sessions = {k: v for k, v in runtime.sessions.items() if v[0] > now}
        if len(runtime.sessions) >= 100:
            raise HTTPException(429, "session capacity")
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        runtime.sessions[token] = (now + 3600, csrf)
        response.set_cookie(
            "session",
            token,
            httponly=True,
            samesite="strict",
            max_age=3600,
            secure=os.environ.get("COOKIE_SECURE") == "1",
        )
        return dict(csrf=csrf)

    @app.get("/api/session")
    def session(authenticated: Secure) -> dict:
        return dict(csrf=authenticated[1])

    @app.post("/api/logout")
    def logout(request: Request, response: Response, authenticated: Secure) -> dict:
        runtime.sessions.pop(request.cookies.get("session", ""), None)
        response.delete_cookie("session")
        return dict(ok=True)

    @app.get("/health")
    def health() -> dict:
        with runtime.store.connect() as db:
            db.execute("SELECT 1")
        return dict(status="ok")

    @app.get("/api/runs")
    def runs(authenticated: Secure) -> list[dict]:
        return runtime.store.runs()

    @app.post("/api/runs")
    async def start(config: Run, authenticated: Secure) -> dict:
        if runtime.task and not runtime.task.done():
            raise HTTPException(409, "run already active")
        run_id = str(uuid4())
        runtime.store.create(run_id, config.model_dump(), time.time())
        runtime.task = asyncio.create_task(runtime.produce(run_id, config))
        return dict(id=run_id)

    @app.post("/api/stop")
    async def stop(authenticated: Secure) -> dict:
        if runtime.task and not runtime.task.done():
            runtime.task.cancel()
            try:
                await runtime.task
            except asyncio.CancelledError:
                pass
        return dict(ok=True)

    @app.get("/api/runs/{run_id}/replay")
    def replay(run_id: str, authenticated: Secure) -> dict:
        configs = {r["id"]: r for r in runtime.store.runs()}
        if run_id not in configs:
            raise HTTPException(404, "unknown run")
        rows = runtime.store.batches(run_id)
        engine = Engine(configs[run_id]["config"]["streams"])
        original, reproduced = [], []
        for row in rows:
            frame = None
            for event in row["events"]:
                frame = engine.apply(event)
            original.append(row["frame"])
            reproduced.append(frame)
        return dict(
            frames=len(original),
            identical=canonical(original) == canonical(reproduced),
            recorded_sha256=digest(original),
            replay_sha256=digest(reproduced),
        )

    @app.get("/api/station")
    def station_report(authenticated: Secure) -> dict:
        return report(runtime.store)

    @app.post("/api/station")
    def station(authenticated: Secure) -> dict:
        return measure(runtime.store)

    @app.get("/api/metrics")
    def metrics(authenticated: Secure) -> dict:
        return dict(runtime.metrics)

    @app.get("/metrics", response_class=PlainTextResponse)
    def prometheus(authenticated: Secure) -> str:
        return "".join(f"meridian_{k} {v}\n" for k, v in runtime.metrics.items())

    @app.websocket("/ws")
    async def socket(ws: WebSocket) -> None:
        # Browser sends a session-bound CSRF proof, preventing cross-site WS hijacking.
        try:
            session = runtime.session(ws.cookies.get("session"))
            runtime.limit("ws:" + str(ws.client.host if ws.client else "local"), 30)
            if len(runtime.subscribers) >= 16:
                raise HTTPException(429, "viewer capacity")
        except HTTPException:
            await ws.close(code=1008)
            return
        await ws.accept()
        queue: asyncio.Queue = asyncio.Queue(maxsize=8)
        try:
            proof = await asyncio.wait_for(ws.receive_text(), timeout=5)
            if not hmac.compare_digest(proof, session[1]):
                await ws.close(code=1008)
                return
            runtime.subscribers[queue] = 0
            while time.monotonic() < session[0]:
                try:
                    packet = await asyncio.wait_for(queue.get(), timeout=1)
                    await asyncio.wait_for(ws.send_text(canonical(packet)), timeout=5)
                except TimeoutError:
                    await ws.send_json(dict(heartbeat=True))
        except (TimeoutError, WebSocketDisconnect, RuntimeError):
            pass
        finally:
            runtime.subscribers.pop(queue, None)
            try:
                await ws.close()
            except RuntimeError:
                pass

    web = Path(__file__).resolve().parent.parent / "apps/web/dist"
    if web.exists():
        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(web / "index.html")

    return app
