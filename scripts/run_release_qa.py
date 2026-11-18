"""Run a deterministic local regression suite repeatedly on this host."""
from __future__ import annotations

import os
import subprocess
import sys

RUNS = int(os.environ.get("MUSICVAULT_QA_RUNS", "50"))
if RUNS < 1 or RUNS > 200:
    raise SystemExit("MUSICVAULT_QA_RUNS must be between 1 and 200.")

for run in range(1, RUNS + 1):
    print(f"MusicVault QA run {run}/{RUNS}", flush=True)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], check=False)
    if result.returncode:
        raise SystemExit(f"QA run {run}/{RUNS} failed with exit code {result.returncode}.")

print(f"PASS: {RUNS} consecutive runs completed on {sys.platform}.", flush=True)
