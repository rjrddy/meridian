"""Deliberately feed a stale packet. Unsafe acceptance must exit unsuccessfully."""

import argparse

from meridian._fusion import Fusion

parser = argparse.ArgumentParser()
parser.add_argument("--unsafe", action="store_true")
args = parser.parse_args()
f = Fusion(1)
f.calibrate(0, 0, 0, 0.01)
f.ingest(0, 1, 10)
f.tick(1)
accepted = True if args.unsafe else f.ingest(0, 0.5, 999)
print({"late_packet_accepted": accepted, "health": list(f.health())})
assert not accepted, "GATE FAILED: baseline admitted an event behind the committed watermark"
print("GATE PASSED: stale sample rejected before state mutation")
