#!/usr/bin/env python3
"""Malrynth Developer CLI for Windows (Experimental)."""

import sys
from pathlib import Path

if sys.version_info < (3, 10):
    print(
        f"UNSUPPORTED: Malrynth Windows tooling requires Python >= 3.10; "
        f"found {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        file=sys.stderr,
    )
    raise SystemExit(2)

# Ensure malrynth_tooling package is importable
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from malrynth_tooling.cli import main

if __name__ == "__main__":
    sys.exit(main())
