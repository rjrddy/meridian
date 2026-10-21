# Causal watermark and calibrated clocks

Context: source clocks differ and late packets must not rewrite displayed history.
Options: wait for every source; interpolate with future data; advance a caller-owned watermark.
Decision: explicit reference calibration followed by monotonic per-source ingestion and ticks. Reject timestamps behind either source order or the committed watermark; count rejection.
Tradeoffs: deterministic bounded waiting and no future leakage, but lost late information and no automatic clock drift estimation. One scalar coordinate is assumed. Calibration must be repeated in a new run if clocks drift materially.
