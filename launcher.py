"""Portable local application entry by Jason Stys; main contract: docs/CODE_INDEX.md."""

import sys

from sensorlab.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["serve"]))
