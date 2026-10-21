"""Capture command output with command, exit and environment, without shell interpolation."""

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

out = Path("docs/results")
out.mkdir(exist_ok=True, parents=True)
started = time.time()
r = subprocess.run(
    ["make", "lint", "test", "bench"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
(out / "checks.log").write_text(r.stdout)
(out / "checks.json").write_text(
    json.dumps(
        {
            "command": "make lint test bench",
            "exit_code": r.returncode,
            "started_unix": started,
            "elapsed_seconds": time.time() - started,
            "platform": platform.platform(),
            "python": sys.version,
        },
        indent=2,
    )
    + "\n"
)
print(r.stdout)
sys.exit(r.returncode)
