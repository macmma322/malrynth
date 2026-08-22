#!/usr/bin/env python3
"""Malrynth Developer CLI for Windows (Experimental)."""

import sys
from pathlib import Path

# Ensure malrynth_tooling package is importable
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from malrynth_tooling.cli import main

if __name__ == "__main__":
    sys.exit(main())
