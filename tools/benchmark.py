"""Reviewed calibration contracts and measured resource use by Jason Stys. Index: docs/CODE_INDEX.md.

Function main; variables: cases, timing, traced Python allocation. Native process RSS is not measured.
"""

import argparse
import json
import time
import tracemalloc
from pathlib import Path

from sensorlab.engine import build_run
from sensorlab.model import CASES, Settings


def main() -> None:
    """Verify six deterministic case-summary contracts; regeneration requires deliberate numerical review."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    start = time.perf_counter()
    tracemalloc.start()
    cases = {}
    for name in CASES:
        run = build_run(Settings(scenario=name))
        cases[name] = {"gate": run["gate"], "fit": run["fit"], "summary": run["summary"]}
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    path = Path(__file__).resolve().parents[1] / "docs/reports/benchmark.json"
    if args.write:
        path.write_text(json.dumps(cases, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif json.loads(path.read_bytes()) != cases:
        raise SystemExit("Case contract drift: review before regeneration")
    print(
        f"6 native/reference case contracts passed; {time.perf_counter() - start:.3f}s; Python traced peak {peak} bytes (not native/total RSS)"
    )


if __name__ == "__main__":
    main()
