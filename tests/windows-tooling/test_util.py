"""Unit tests for utility functions (SHA-256, ANSI stripping, formatting)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

# Add tools/windows to sys.path
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.util import compute_sha256, strip_ansi


class TestUtil(unittest.TestCase):
    def test_sha256_computation(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"Malrynth operating system byte reproducibility test")
            temp_path = Path(f.name)
        try:
            digest = compute_sha256(temp_path)
            expected = "ceac7e8234dae12ce31fc60056722e3fc8d0cbd66364e7e130e411fa4d14e8d6"
            self.assertEqual(digest, expected)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_strip_ansi(self) -> None:
        raw = "\x1b[31mFAIL\x1b[0m \x1b[1m==>\x1b[0m text\x1b[=1h"
        cleaned = strip_ansi(raw)
        self.assertEqual(cleaned, "FAIL ==> text")


if __name__ == "__main__":
    unittest.main()
