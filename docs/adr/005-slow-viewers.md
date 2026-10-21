# Bounded viewer queues

Context: acquisition should not stop because a browser is slow.
Options: block producer, unbounded queues, disconnect immediately, drop oldest view frames.
Decision: bounded per-viewer queue, drop oldest at capacity, report cumulative skipped frames. Persist all generated frames before any delivery. A send timeout disconnects stalled viewers.
Tradeoffs: live delivery is lossy; durable replay is authoritative. WebSocket transport buffers still exist, so queue bounds are not an absolute end-to-end network-memory guarantee. Viewer count and send timeout limit exposure.
