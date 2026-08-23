"""Tests for Windows panic-path output validation."""

from __future__ import annotations

import sys
import unittest
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from unittest.mock import patch
from pathlib import Path

_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.panic import check_panic_path, evaluate_panic_output
from malrynth_tooling.runner import BootRunnerResult


VALID_PANIC = """KERNEL PANIC
  at core/kernel/src/main.rs:244:9
panic-test: this panic is intentional
backtrace:
  #0  0x0000000010001234
  #1  0x0000000010001000
MALRYNTH_M0_BOOT_FAIL
"""


class TestPanicOutput(unittest.TestCase):
    def test_complete_panic_contract_passes(self) -> None:
        result = evaluate_panic_output(VALID_PANIC)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.frame_count, 2)

    def test_missing_panic_and_timeout_output_fail(self) -> None:
        self.assertFalse(evaluate_panic_output("MALRYNTH_M0_BOOT_FAIL\n").is_valid)
        self.assertFalse(evaluate_panic_output("").is_valid)

    def test_normal_success_marker_is_rejected(self) -> None:
        self.assertFalse(evaluate_panic_output(VALID_PANIC + "MALRYNTH_M0_BOOT_OK\n").is_valid)

    def test_validator_rejects_timeout(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            boot = BootRunnerResult("timeout", run_dir / "serial.log", "", 1.0, run_dir)
            with patch("malrynth_tooling.panic.build_image", return_value=0), \
                 patch("malrynth_tooling.panic.run_qemu_boot", return_value=boot), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 1, "", "")):
                self.assertEqual(check_panic_path(Path(temp_dir), timeout=0.1), 1)

    def test_validator_rejects_missing_panic_diagnostics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            boot = BootRunnerResult(
                "fail-marker", run_dir / "serial.log", "MALRYNTH_M0_BOOT_FAIL\n", 0.1, run_dir
            )
            with patch("malrynth_tooling.panic.build_image", return_value=0), \
                 patch("malrynth_tooling.panic.run_qemu_boot", return_value=boot), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 1, "", "")):
                self.assertEqual(check_panic_path(Path(temp_dir)), 1)


if __name__ == "__main__":
    unittest.main()
