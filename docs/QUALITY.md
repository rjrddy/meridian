# Meridian quality checkpoint

Status: **partial**, because the flagship's live deployment and completed demo recording are outstanding. No account or live deployment was created. All old repositories remain intact; no archive/tag/deletion phase has been executed.

| Required check | Result | Evidence |
|---|---|---|
| Hard core written and explained | PASS | core/fusion.cpp; docs/DESIGN.md |
| One-command run from fresh clone | PASS on Linux CI | docs/results/ci-final-code.log: clean clone, Compose build, healthy container, authenticated smoke |
| UI shows live behavior | PASS locally | docs/results/browser.json and screenshots; container asset/WebSocket smoke |
| Unit, integration, property and chaos tests | PASS | docs/results/checks.log; tests/test_core.py, test_api.py, test_chaos.py |
| Benchmark numbers saved | PASS | docs/results/benchmark.json, raw event/frame/timing files |
| Demonstrated caught failure | PASS | failure-unsafe.log vs failure-guarded.log; pre-fix dependency and CI failure logs |
| ADRs | PASS | docs/adr/ |
| INTERVIEW.md and DRILL.md | PASS | repository root and docs/DRILL.md |
| CI green | PASS for recorded code revision | docs/results/ci-final-code.json; GitHub run URL below |
| No unmeasured result claims | PASS on manual review | README generated from saved results; timing boundaries and unmeasured public-data accuracy explicit |
| Required live demo and completed recording | FAIL / outstanding | deploy/render.yaml and docs/DEMO.md are preparation, not deployment or video proof |

Recorded code verification: https://github.com/rjrddy/meridian/actions/runs/39538201336 at source commit 17c38e36928554368bc509575845565754d6d3fb. Later evidence/documentation commits do not change this code. The workspace FLAGSHIP_VERIFICATION.json records the eventual final pushed revision and its CI result separately, avoiding self-referential evidence commits.

Local Docker was unavailable. The real Docker check ran on a GitHub-hosted Linux runner and its raw log is saved; it is not inferred from native tests. The local independent clone also installed its own dependencies, built and passed tests; see fresh-clone.json/log. A dependency deprecation warning remains in the test output and is not suppressed.

Known architectural limits are documented rather than treated as hidden guarantees: single-process owner, one scalar common coordinate, trusted reference offset calibration without drift estimation, no hardware deadline certification, lossy live viewers with durable authoritative replay, model covariance without empirical coverage calibration, no automated disk retention/backup. Public temperatures are a replay compatibility exercise only. Optional dispatch and video/pose modules are not claimed.

Stop here for review before Relay. Deployment needs a chosen host and persistence policy; the free-tier configuration has ephemeral storage. Exact demo recording steps are in docs/DEMO.md.
