"""Unit tests for QEMU process supervision, markers, timeouts, and process cleanup."""

from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add tools/windows to sys.path
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.runner import run_qemu_boot


class TestRunner(unittest.TestCase):
    def test_mock_success_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth test runner ") as temp_dir:
            temp_path = Path(temp_dir)
            serial_log = temp_path / "serial.log"

            # Create a mock child python script that writes the success marker
            mock_script = temp_path / "mock_success.py"
            mock_script.write_text(
                "import time, sys\n"
                f"log_path = r'{serial_log}'\n"
                "with open(log_path, 'a', encoding='utf-8') as f:\n"
                "    f.write('Booting Malrynth OS...\\n')\n"
                "    f.write('MALRYNTH_M0_BOOT_OK\\n')\n"
                "time.sleep(1.0)\n",
                encoding="utf-8",
            )

            res = run_qemu_boot(
                timeout=5.0,
                quiet=True,
                custom_command=[sys.executable, str(mock_script)],
                serial_log_override=serial_log,
            )

            self.assertTrue(res.is_success)
            self.assertEqual(res.status, "ok")
            self.assertIn("MALRYNTH_M0_BOOT_OK", res.cleaned_output)

    def test_mock_failure_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth test runner ") as temp_dir:
            temp_path = Path(temp_dir)
            serial_log = temp_path / "serial.log"

            mock_script = temp_path / "mock_fail.py"
            mock_script.write_text(
                "import time, sys\n"
                f"log_path = r'{serial_log}'\n"
                "with open(log_path, 'a', encoding='utf-8') as f:\n"
                "    f.write('KERNEL PANIC: intentional\\n')\n"
                "    f.write('MALRYNTH_M0_BOOT_FAIL\\n')\n"
                "time.sleep(1.0)\n",
                encoding="utf-8",
            )

            res = run_qemu_boot(
                timeout=5.0,
                quiet=True,
                custom_command=[sys.executable, str(mock_script)],
                serial_log_override=serial_log,
            )

            self.assertFalse(res.is_success)
            self.assertEqual(res.status, "fail-marker")

    def test_mock_silent_exit_without_marker_is_failure(self) -> None:
        """QEMU exiting cleanly (exit code 0) without a marker must NEVER pass."""
        with tempfile.TemporaryDirectory(prefix="malrynth test runner ") as temp_dir:
            temp_path = Path(temp_dir)
            serial_log = temp_path / "serial.log"

            mock_script = temp_path / "mock_silent.py"
            mock_script.write_text(
                "import sys\n"
                f"log_path = r'{serial_log}'\n"
                "with open(log_path, 'a', encoding='utf-8') as f:\n"
                "    f.write('Dropping to UEFI interactive shell...\\n')\n"
                "sys.exit(0)\n",
                encoding="utf-8",
            )

            res = run_qemu_boot(
                timeout=5.0,
                quiet=True,
                custom_command=[sys.executable, str(mock_script)],
                serial_log_override=serial_log,
            )

            self.assertFalse(res.is_success)
            self.assertEqual(res.status, "process-exited")

    def test_mock_timeout_handling_and_cleanup(self) -> None:
        """Process that runs indefinitely must be caught by timeout and killed."""
        with tempfile.TemporaryDirectory(prefix="malrynth test runner ") as temp_dir:
            temp_path = Path(temp_dir)
            serial_log = temp_path / "serial.log"

            mock_script = temp_path / "mock_hang.py"
            mock_script.write_text(
                "import time, sys\n"
                "while True:\n"
                "    time.sleep(0.1)\n",
                encoding="utf-8",
            )

            start = time.monotonic()
            res = run_qemu_boot(
                timeout=1.5,
                quiet=True,
                custom_command=[sys.executable, str(mock_script)],
                serial_log_override=serial_log,
            )
            elapsed = time.monotonic() - start

            self.assertFalse(res.is_success)
            self.assertEqual(res.status, "timeout")
            self.assertGreaterEqual(elapsed, 1.4)
            self.assertLess(elapsed, 4.0)


if __name__ == "__main__":
    unittest.main()
