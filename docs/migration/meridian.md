# Meridian salvage record

Original repositories remain in projects/ with their Git history intact. No archive, tag or remote deletion has occurred.

- P1 src/fuse.cpp and src/replay.py: adapted inverse-variance weighting, seeded noisy streams, truth scoring and replay comparison. Rewrote the batch executable as a C++20 pybind11 streaming engine with bounded deques, monotonic watermarks, age limits and a Kalman posterior. No sibling imports or subprocess-per-estimate architecture remains.
- R3 src/main.py: reused the desynchronization/dropout validation principle as late-packet, clock and source-loss fixtures. Did not copy video decoding into the required scalar core. Public egocentric video/pose evaluation remains absent; this flagship makes no such claim.
- R4 src/main.py: adapted synthetic unit generation, instrument timeout/retry rules, out-of-spec thresholds and SQL yield aggregation into meridian/station.py. Replaced the single-run file lifecycle with persistent API-triggered transactional batches.
- X6 src/main.py: inspected optional SimPy dispatch/load/failure ideas. Dispatch simulation is intentionally not included in Meridian's core and is not claimed as delivered. The old repo remains intact.

Original commit IDs are recorded in the workspace Phase 0 docs/migration/results/inventory.json. All new benchmark numbers must be generated from this repository, not copied from old evidence. MIT public sensor data is downloaded separately, checksum recorded, and not redistributed as a bundled dataset because an explicit reuse license was not identified.
