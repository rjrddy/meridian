import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
type Frame = {
  time: number;
  estimate: number;
  truth: number;
  variance: number;
  active: number;
  ages: number[];
  health: {
    buffered: number;
    late: number;
    overflow: number;
    offset: number;
  }[];
};
type Packet = { seq: number; frame: Frame; commit_ms: number; skipped: number };
type Run = {
  id: string;
  status: string;
  config: { dropout: number; ticks: number; streams: number };
};
type Station = {
  units: number;
  statuses: Record<string, number>;
  yield_percent: number;
  timeout_attempts: number;
};
function App() {
  const [csrf, setCsrf] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState("");
  const [history, setHistory] = useState<Packet[]>([]),
    [runs, setRuns] = useState<Run[]>([]),
    [dropout, setDropout] = useState(0.1),
    [live, setLive] = useState(false),
    [station, setStation] = useState<Station | null>(null),
    [replay, setReplay] = useState(""),
    [busy, setBusy] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const call = async (path: string, method = "GET", body?: object) => {
    const r = await fetch("/api/" + path, {
      method,
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) {
      const d = await r.json();
      throw Error(
        typeof d.detail === "string" ? d.detail : "Check the supplied values",
      );
    }
    return r.json();
  };
  const refresh = async () => {
    setRuns(await call("runs"));
    setStation(await call("station"));
  };
  const action = async (f: () => Promise<void>) => {
    setError("");
    setBusy(true);
    try {
      await f();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    fetch("/api/session")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setCsrf(d.csrf));
  }, []);
  useEffect(() => {
    if (!csrf) return;
    refresh().catch((e) => setError(String(e)));
    const socket = new WebSocket(
      `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
    );
    ws.current = socket;
    socket.onopen = () => socket.send(csrf);
    socket.onmessage = (e) => {
      const p = JSON.parse(e.data);
      if (!p.heartbeat) {
        setHistory((h) => [...h.slice(-149), p]);
        setLive(true);
      }
    };
    socket.onclose = () => setLive(false);
    const timer = setInterval(() => refresh().catch(() => {}), 2000);
    return () => {
      clearInterval(timer);
      socket.close();
    };
  }, [csrf]);
  const current = history.at(-1),
    frame = current?.frame;
  const values = history.map((p) => p.commit_ms).sort((a, b) => a - b),
    p99 = values.length ? values[Math.ceil(values.length * 0.99) - 1] : null;
  const line = (key: "estimate" | "truth") =>
    history
      .map((p, i) => `${(i / 149) * 960},${115 - p.frame[key] * 65}`)
      .join(" ");
  if (!csrf)
    return (
      <div className="login instrument-access">
        <div className="access-grid" aria-hidden="true">
          <span>+ ALIGN</span>
          <span>+ RECORD</span>
          <span>+ REPLAY</span>
        </div>
        <div className="brand">
          <span className="mark">M</span> MERIDIAN
        </div>
        <p className="eyebrow">SENSOR TELEMETRY WORKBENCH</p>
        <h1>
          Make sense
          <br />
          of every signal.
        </h1>
        <p>
          Calibrated sensor fusion. Recorded decisions.
          <br />A replay you can verify.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            action(async () => {
              const r = await call("login", "POST", { password });
              setCsrf(r.csrf);
              setPassword("");
            });
          }}
        >
          <label htmlFor="password">Operator password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
          <button disabled={busy}>Open console ↗</button>
        </form>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <small>Synthetic sensor data · Single-operator workspace</small>
      </div>
    );
  return (
    <div className="shell">
      <aside aria-label="Workbench navigation">
        <div className="brand">
          <span className="mark">M</span> MERIDIAN
        </div>
        <p className="eyebrow">TELEMETRY / LOCAL</p>
        <a href="#overview" className="selected">
          ◈ &nbsp; Signal overview
        </a>
        <a href="#history">↺ &nbsp; Recorder & replay</a>
        <a href="#station">▤ &nbsp; Test station</a>
        <div className="aside-bottom">
          <span className="dot" /> Persistence enabled
          <br />
          <small>SQLite WAL · single writer</small>
          <button
            className="subtle"
            onClick={() =>
              action(async () => {
                await call("logout", "POST");
                setCsrf("");
              })
            }
          >
            Sign out
          </button>
        </div>
      </aside>
      <main id="overview">
        <header>
          <span>
            OPERATIONS <b>/</b> SENSOR FUSION
          </span>
          <span className="badge">SYNTHETIC ENVIRONMENT</span>
        </header>
        <section className="title">
          <div>
            <p className="eyebrow">M / SENSOR FUSION WORKBENCH</p>
            <h1>
              Signal overview<span>.</span>
            </h1>
            <p>Observe the signal. Inspect the gaps. Replay the record.</p>
          </div>
          <div className="status">
            <span className={live ? "dot" : "dot dim"} />
            {live ? "Receiving frames" : "Ready for a run"}
          </div>
        </section>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <section className="controls">
          <div>
            <label htmlFor="dropout">Packet dropout</label>
            <select
              id="dropout"
              value={dropout}
              onChange={(e) => setDropout(Number(e.target.value))}
            >
              <option value={0}>0% · nominal</option>
              <option value={0.1}>10% · degraded</option>
              <option value={0.3}>30% · stress</option>
            </select>
          </div>
          <p>
            Calibrated clocks · seeded noise
            <br />
            <small>3 sources / 50 ticks per second</small>
          </p>
          <button
            disabled={busy}
            onClick={() =>
              action(async () => {
                setHistory([]);
                await call("runs", "POST", {
                  dropout,
                  ticks: 600,
                  streams: 3,
                  seed: 42,
                });
                setReplay("");
                await refresh();
              })
            }
          >
            ▶ Start live run
          </button>
          <button
            className="secondary"
            onClick={() =>
              action(async () => {
                await call("stop", "POST");
                setLive(false);
                await refresh();
              })
            }
          >
            Stop
          </button>
        </section>
        <section className="stats">
          <article>
            <label>ACTIVE SOURCES</label>
            <strong>
              {frame?.active ?? "—"}
              <small> / 3</small>
            </strong>
            <p>Within freshness window</p>
          </article>
          <article>
            <label>COMMIT LATENCY / P99</label>
            <strong>
              {p99?.toFixed(2) ?? "—"}
              <small> ms</small>
            </strong>
            <p>Tick compute + durable commit</p>
          </article>
          <article>
            <label>STATE UNCERTAINTY</label>
            <strong>{frame?.variance.toFixed(5) ?? "—"}</strong>
            <p>Kalman posterior variance</p>
          </article>
          <article>
            <label>VIEWER FRAMES SKIPPED</label>
            <strong>{current?.skipped ?? "—"}</strong>
            <p>Bounded delivery queue</p>
          </article>
        </section>
        <section className="panel chart" aria-label="Signal instrument">
          <div className="panel-title">
            <h2>Aligned signal timeline</h2>
            <div className="legend">
              <span>● Fused estimate</span>
              <span>● Ground truth</span>
            </div>
          </div>
          {history.length ? (
            <svg
              viewBox="0 0 960 230"
              role="img"
              aria-label="Live fused estimate and synthetic ground truth"
            >
              <path d="M0 50H960 M0 115H960 M0 180H960" stroke="#e3e9ec" />
              <polyline
                points={line("truth")}
                fill="none"
                stroke="#abbac5"
                strokeWidth="2"
                strokeDasharray="6 5"
              />
              <polyline
                points={line("estimate")}
                fill="none"
                stroke="#087f78"
                strokeWidth="3"
              />
            </svg>
          ) : (
            <div className="empty">
              Your next signal starts here.
              <small>
                Start a run to watch calibrated samples become a fused estimate.
              </small>
            </div>
          )}
          <div className="chart-footer">
            <span>CAUSAL ZERO-ORDER HOLD · NO FUTURE SAMPLES</span>
            <span>
              {frame ? `t = ${frame.time.toFixed(2)} s` : "Awaiting telemetry"}
            </span>
          </div>
        </section>
        <div className="two-col">
          <section className="panel">
            <div className="panel-title">
              <h2>Source health</h2>
              <span className="eyebrow">LIVE</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Age</th>
                  <th>Late / overflow</th>
                </tr>
              </thead>
              <tbody>
                {[0, 1, 2].map((i) => (
                  <tr key={i}>
                    <td>
                      <span className="source-dot" /> Sensor 0{i + 1}
                    </td>
                    <td>
                      {frame?.ages[i] !== undefined
                        ? frame.ages[i] < 0
                          ? "No sample"
                          : `${(frame.ages[i] * 1000).toFixed(0)} ms`
                        : "—"}
                    </td>
                    <td>
                      {frame?.health[i]
                        ? `${frame.health[i].late} / ${frame.health[i].overflow}`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="panel">
            <div className="panel-title">
              <h2>Commit latency distribution</h2>
              <span className="eyebrow">THIS VIEW</span>
            </div>
            <div className="histogram">
              {[1, 2, 5, 10, 25, 100, Infinity].map((v, i, all) => {
                const count = history.filter(
                  (p) => p.commit_ms <= v && p.commit_ms > (all[i - 1] ?? 0),
                ).length;
                return (
                  <div key={i}>
                    <i
                      style={{
                        height: `${Math.max(2, (count / Math.max(1, history.length)) * 110)}px`,
                      }}
                    />
                    <small>{v === Infinity ? ">100" : `≤${v}`}</small>
                  </div>
                );
              })}
            </div>
            <p className="footnote">
              Milliseconds; excludes browser transit and rendering.
            </p>
          </section>
        </div>
        <section className="panel" id="history">
          <div className="panel-title">
            <h2>Recorder & replay</h2>
            <span className="eyebrow">PERSISTED HISTORY</span>
          </div>
          {runs.length ? (
            <table>
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Dropout</th>
                  <th>Status</th>
                  <th>Verification</th>
                </tr>
              </thead>
              <tbody>
                {runs.slice(0, 8).map((r) => (
                  <tr key={r.id}>
                    <td className="mono">{r.id.slice(0, 8)}</td>
                    <td>{r.config.dropout * 100}%</td>
                    <td>
                      <span className="pill">{r.status}</span>
                    </td>
                    <td>
                      <button
                        className="link"
                        onClick={() =>
                          action(async () => {
                            const d = await call(`runs/${r.id}/replay`);
                            setReplay(
                              `${r.id.slice(0, 8)}: ${d.identical ? "Bit-identical" : "MISMATCH"} · ${d.frames} frames · SHA256 ${d.replay_sha256}`,
                            );
                          })
                        }
                      >
                        Verify replay ↗
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="footnote">No recorded runs yet.</p>
          )}
          {replay && (
            <p role="status" className="replay">
              {replay}
            </p>
          )}
        </section>
        <section className="panel" id="station">
          <div className="panel-title">
            <h2>Test-station yield</h2>
            <button
              className="secondary"
              disabled={busy}
              onClick={() =>
                action(async () => setStation(await call("station", "POST")))
              }
            >
              Measure synthetic batch
            </button>
          </div>
          {station?.units ? (
            <div className="station">
              <strong>
                {station.yield_percent.toFixed(1)}%<small>yield</small>
              </strong>
              <p>
                {station.units} units · {station.statuses.pass ?? 0} passed ·{" "}
                {station.statuses["out-of-spec"] ?? 0} out of spec ·{" "}
                {station.statuses.timeout ?? 0} timed out
                <br />
                <small>
                  {station.timeout_attempts} timeout attempts, bounded retries
                  recorded in SQLite.
                </small>
              </p>
            </div>
          ) : (
            <p className="footnote">
              Run a seeded synthetic instrument batch to inspect yield and retry
              outcomes.
            </p>
          )}
        </section>
        <footer>
          MERIDIAN / CALIBRATED BY DESIGN
          <span>Original engineering · Public & synthetic data only</span>
        </footer>
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
