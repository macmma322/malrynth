"""Tests for truthful Python and build/boot readiness reporting."""

from __future__ import annotations

import sys
import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.doctor import python_version_supported, run_doctor


class TestReadiness(unittest.TestCase):
    def test_python_minimum_is_310(self) -> None:
        self.assertFalse(python_version_supported((3, 8, 18)))
        self.assertFalse(python_version_supported((3, 9, 19)))
        self.assertTrue(python_version_supported((3, 10, 0)))
        self.assertTrue(python_version_supported((3, 14, 7)))

    def test_doctor_reports_unsupported_old_python(self) -> None:
        output = io.StringIO()
        fake_version = SimpleNamespace(major=3, minor=9, micro=19)
        with patch("malrynth_tooling.doctor.sys.version_info", fake_version), \
             redirect_stdout(output), redirect_stderr(output):
            result = run_doctor()
        self.assertEqual(result, 1)
        self.assertIn("python", output.getvalue())
        self.assertIn("UNSUPPORTED", output.getvalue())
        self.assertIn("BUILD READY: NO", output.getvalue())


if __name__ == "__main__":
    unittest.main()
