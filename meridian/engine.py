"""Single-owner core adapter; canonical event log is the replay boundary."""

import hashlib
import json

from meridian._fusion import Fusion


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class Engine:
    def __init__(self, streams: int = 3, max_age: float = 0.15) -> None:
        self.core = Fusion(streams, 128, max_age, 0.3)

    def apply(self, event: dict) -> dict | None:
        match event["kind"]:
            case "calibrate":
                self.core.calibrate(
                    event["stream"], event["sensor"], event["reference"], event["variance"]
                )
            case "sample":
                if not self.core.ingest(event["stream"], event["time"], event["value"]):
                    return {"rejected": "late"}
            case "tick":
                frame = self.core.tick(event["time"])
                return {
                    "time": frame.time,
                    "estimate": frame.estimate,
                    "variance": frame.variance,
                    "measurement": frame.measurement,
                    "active": frame.active,
                    "initialized": frame.initialized,
                    "ages": frame.ages,
                    "truth": event.get("truth"),
                    "health": list(self.core.health()),
                }
            case _:
                raise ValueError("unknown event")
        return None


def digest(frames: list[dict]) -> str:
    return hashlib.sha256(canonical(frames).encode()).hexdigest()
