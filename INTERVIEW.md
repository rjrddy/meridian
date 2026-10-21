# Meridian interview guide

## Two-minute pitch

Meridian asks when a noisy sensor sample is still allowed to affect an estimate. I wrote a C++20 streaming core with calibrated timestamps, bounded buffers and a monotonic watermark. Late data is rejected visibly rather than rewriting displayed history. Fresh measurements combine by inverse variance, then update a scalar Kalman state. Missing data increases uncertainty instead of blocking acquisition. The Python API commits inputs and outputs together before broadcasting to a React console. Replay rebuilds the core from the committed log and compares canonical output hashes. Benchmarks and their raw inputs live in docs/results; README reports their measured results and boundaries. This is a single-process scalar fusion demonstrator, not certified robot control or a distributed stream processor.

## Ten-minute architecture walkthrough

Walk through core/fusion.cpp from calibration to ingest to tick. Show how the source-order check differs from the global watermark, and why future data cannot enter an earlier estimate. Explain age inflation and the random-walk covariance update. Then trace meridian/api.py Runtime.produce: collect a batch, compute, commit in meridian/store.py, broadcast into bounded viewer queues. Show authentication, CSRF and request limits at the API boundary. Finally open the React live console, run replay, and inspect tests/test_chaos.py for an actual process exiting mid-transaction. Use docs/results/benchmark.json and browser.json only when discussing measured performance; absence of a result means not measured.

## Five tradeoffs

- Causal hold instead of interpolation: online availability without future leakage, at the cost of stale-sample bias.
- Scalar Kalman instead of EKF: a defendable common-coordinate model, without nonlinear multi-modal state estimation.
- Explicit calibration instead of inferred offsets: known reference semantics, but external probes and no drift tracking.
- SQLite single writer instead of distributed storage: atomic local history and simpler failure reasoning, but no horizontal write scaling.
- Lossy viewer queues instead of backpressure into acquisition: bounded application buffering, but live clients may skip frames; history remains replayable.

## Five failure modes

- Out-of-order packet: reject before mutation, increment late count; core tests exercise the watermark.
- All sources missing: hold initialized mean and increase variance; source-loss test checks the behavior.
- Viewer stalls: drop oldest queue frame, report skipped count, enforce viewer limits and send timeout.
- Process dies during commit: SQLite rolls back the incomplete batch; startup marks prior running jobs interrupted. A real child-process exit test demonstrates this.
- Unauthorized mutation: session plus CSRF gate rejects it; bounded login attempts and expiring sessions limit the local demo attack surface.

## Fifteen likely questions

1. Why is this hard? The causal commitment boundary ties timestamp order, bounded waiting, numerical state and persisted replay together. A late packet cannot silently revise an already committed frame.
2. What is the linearization point? SQLite transaction commit for persisted frame visibility. The C++ engine itself is single-owner, not concurrently linearizable across threads.
3. Why not a full EKF? The implemented task is scalar shared-coordinate observation; an EKF would require additional dynamics and Jacobians justified by a real physical model.
4. How do you handle clock drift? I do not estimate it. Reference calibration sets offset for the run; long-term drift is an explicit gap.
5. Is the reported variance calibrated? No. The model reuses held observations, so correlation can make posterior covariance optimistic. Empirical RMSE is reported separately.
6. Is replay bit-identical everywhere? Only demonstrated for the same build/runtime. Cross-platform floating-point identity is not promised.
7. Does WebSocket delivery provide exactly-once semantics? No. Frames carry sequence numbers and skipped counts. The durable history is authoritative.
8. What happens after a restart? SQLite preserves committed batches, unfinished runs become interrupted, and in-memory authentication sessions expire.
9. How would you scale writes? Partition independent runs and move metadata/event persistence to Postgres; preserve a single owner for each fusion state and define a fencing protocol.
10. How do you choose the watermark? The current driver ticks on a configured synthetic timeline. A real acquisition driver needs an explicit arrival/lateness policy, not accidental wall-clock assumptions.
11. Why a deque rather than a custom ring? It gives bounded logical storage and simple eviction with standard-library semantics. No lock-free performance claim is made.
12. What does latency measure? Core event timing, first-input-through-SQLite batch timing and local browser message-arrival timing are separate artifacts. None establishes hard real-time scheduling.
13. What does the public dataset prove? Parsing and replay compatibility on public lab temperatures. Different locations are not shared truth, so no public-data accuracy claim follows.
14. How do you secure the demo? Environment secret, scrypt verifier, HttpOnly cookie, session-bound CSRF on writes and socket setup, request limits and bounded memory. Hosted TLS and persistence are operational requirements.
15. What would you change first? Consume independent observations once or model measurement correlation, add calibrated drift probes and test hardware-clock latency under realistic load before optimizing kernels.

## Three more months

Add a physically justified multi-dimensional motion model, calibrated sensor-clock drift, independent-observation updates, recorded public datasets with explicit licenses, longer fault campaigns, disk retention/backup, persistent deployment, hardware timestamp instrumentation and a genuine end-to-end latency SLO. Keep the current scalar baseline so each extension has a reproducible comparison.
