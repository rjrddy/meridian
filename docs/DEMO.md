# Record the demo

Start with `cp .env.example .env`, replace the example password locally, then `docker compose up --build`. Open http://localhost:8000. Use an existing screen recorder; no third-party account is required.

Suggested ninety-second recording:

- Sign in with the local operator password. Explain that source clocks are calibrated and all data in the live simulator is synthetic.
- Start a nominal run. Point to the fused-vs-truth timeline, active source count and durable commit latency histogram. Clarify that the histogram excludes browser delivery.
- Stop the run; choose thirty percent packet dropout; start another run. Show sample ages, continuous estimates and increasing uncertainty if all sources disappear.
- Stop, then choose Verify replay on the newest persisted run. Show the identical canonical-output hashes and frame count.
- Run the synthetic test-station batch. Explain pass/out-of-spec/timeout categories, bounded retries and SQL persistence.
- Finish with the saved benchmark results and caught stale-packet failure. State the unresolved limits listed in README.

The redesigned console recording is saved in [ui-redesign/demo.webm](results/ui-redesign/demo.webm), with its actual duration in [demo-probe.json](results/ui-redesign/demo-probe.json). It demonstrates the real local console; live deployment remains outstanding. The capture leaves extra wall-clock margin and checks encoded duration rather than assuming the timer equals video length.
