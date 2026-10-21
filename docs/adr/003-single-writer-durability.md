# One writer and transactional replay

Context: a portfolio deployment needs durable history and a defensible failure boundary.
Options: memory only, SQLite WAL, Postgres plus a distributed queue.
Decision: one application process, SQLite WAL transactions containing input batches and the corresponding output frame, broadcast after commit. Mark unfinished runs interrupted on process startup. Persisted canonical events drive replay.
Tradeoffs: no distributed coordination and straightforward crash recovery. One process only; do not run multiple Uvicorn workers. SQLite stores grow with run history and need operational retention/backup. Replay hash equivalence is limited to the same numerical build; no cross-platform floating-point guarantee. Free hosting with ephemeral disks cannot promise history across redeployments.
