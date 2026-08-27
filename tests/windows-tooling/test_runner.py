"""Unit tests for QEMU process supervision, markers, timeouts, and process cleanup."""

from __future__ import annotations

import sys
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

# Add tools/windows to sys.path
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "windows"
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from malrynth_tooling.runner import _classify_output, _copy_vars_template, run_qemu_boot


class TestRunner(unittest.TestCase):
    def test_marker_classification_requires_complete_logical_lines(self) -> None:
        self.assertEqual(_classify_output("MALRYNTH_M0_BOOT_OK\r\n"), "ok")
        self.assertEqual(_classify_output("\x1b[32mMALRYNTH_M0_BOOT_OK\x1b[0m\n"), "ok")
        self.assertIsNone(_classify_output("NOT_MALRYNTH_M0_BOOT_OK_BOGUS\n"))
        self.assertIsNone(_classify_output("prefix MALRYNTH_M0_BOOT_FAIL suffix\n"))

    def test_late_failure_during_teardown_overrides_observed_success(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth final classification ") as temp_dir:
            root = Path(temp_dir)
            serial_log = root / "serial.log"
            script = (
                "import time; from pathlib import Path; "
                f"Path(r'{serial_log}').write_text('MALRYNTH_M0_BOOT_OK\\n'); time.sleep(60)"
            )

            def append_failure(proc) -> None:
                serial_log.write_text(
                    serial_log.read_text() + "MALRYNTH_M0_BOOT_FAIL\n", encoding="utf-8"
                )
                proc.kill()
                proc.wait()

            with patch(
                "malrynth_tooling.runner._terminate_process_tree", side_effect=append_failure
            ):
                result = run_qemu_boot(
                    timeout=5.0,
                    quiet=True,
                    custom_command=[sys.executable, "-c", script],
                    serial_log_override=serial_log,
                )
            self.assertEqual(result.status, "fail-marker")

    def test_success_written_only_after_timeout_does_not_pass(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth timeout boundary ") as temp_dir:
            root = Path(temp_dir)
            serial_log = root / "serial.log"
            script = "import time; time.sleep(60)"

            def append_success(proc) -> None:
                serial_log.write_text("MALRYNTH_M0_BOOT_OK\n", encoding="utf-8")
                proc.kill()
                proc.wait()

            with patch(
                "malrynth_tooling.runner._terminate_process_tree", side_effect=append_success
            ):
                result = run_qemu_boot(
                    timeout=0.2,
                    quiet=True,
                    custom_command=[sys.executable, "-c", script],
                    serial_log_override=serial_log,
                )
            self.assertEqual(result.status, "timeout")
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

    def test_failure_marker_wins_if_both_markers_appear(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth both markers ") as temp_dir:
            serial_log = Path(temp_dir) / "serial.log"
            script = (
                "from pathlib import Path; "
                f"Path(r'{serial_log}').write_text('MALRYNTH_M0_BOOT_OK\\nMALRYNTH_M0_BOOT_FAIL\\n')"
            )
            res = run_qemu_boot(
                timeout=5.0,
                quiet=True,
                custom_command=[sys.executable, "-c", script],
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

    def test_interactive_exit_zero_without_marker_is_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth interactive ") as temp_dir:
            serial_log = Path(temp_dir) / "serial.log"
            res = run_qemu_boot(
                timeout=5.0,
                interactive=True,
                quiet=True,
                custom_command=[sys.executable, "-c", "raise SystemExit(0)"],
                serial_log_override=serial_log,
            )
            self.assertFalse(res.is_success)
            self.assertEqual(res.status, "process-exited")

    def test_unique_run_directories_are_cleaned(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth run roots ") as temp_dir:
            root = Path(temp_dir)
            results = []
            for index in range(2):
                log = root / f"serial-{index}.log"
                script = (
                    "from pathlib import Path; "
                    f"Path(r'{log}').write_text('MALRYNTH_M0_BOOT_OK\\n')"
                )
                results.append(run_qemu_boot(
                    timeout=5.0,
                    quiet=True,
                    custom_command=[sys.executable, "-c", script],
                    serial_log_override=log,
                    temp_root=root,
                ))
            self.assertNotEqual(results[0].run_directory, results[1].run_directory)
            self.assertFalse(results[0].run_directory.exists())
            self.assertFalse(results[1].run_directory.exists())

    def test_vars_template_is_immutable_and_copies_are_independent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth vars isolation ") as temp_dir:
            root = Path(temp_dir)
            template = root / "edk2-i386-vars.fd"
            pristine = b"pristine-vars-template"
            template.write_bytes(pristine)
            run_a = root / "run-a"
            run_b = root / "run-b"
            run_a.mkdir()
            run_b.mkdir()
            copy_a = _copy_vars_template(template, run_a)
            copy_b = _copy_vars_template(template, run_b)
            copy_a.write_bytes(b"mutated-by-run-a")
            self.assertEqual(template.read_bytes(), pristine)
            self.assertEqual(copy_b.read_bytes(), pristine)
            self.assertNotEqual(copy_a, copy_b)

    def test_concurrent_runs_do_not_share_directories(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth concurrent runs ") as temp_dir:
            root = Path(temp_dir)

            def execute(index: int):
                log = root / f"concurrent-{index}.log"
                script = (
                    "import time; from pathlib import Path; "
                    f"Path(r'{log}').write_text('MALRYNTH_M0_BOOT_OK\\n'); time.sleep(0.5)"
                )
                return run_qemu_boot(
                    timeout=5.0,
                    quiet=True,
                    custom_command=[sys.executable, "-c", script],
                    serial_log_override=log,
                    temp_root=root,
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(execute, (1, 2)))
            self.assertTrue(all(result.is_success for result in results))
            self.assertNotEqual(results[0].run_directory, results[1].run_directory)
            self.assertTrue(all(not result.run_directory.exists() for result in results))

    @unittest.skipUnless(sys.platform == "win32", "Windows process-tree semantics")
    def test_timeout_kills_descendant_process(self) -> None:
        with tempfile.TemporaryDirectory(prefix="malrynth process tree ") as temp_dir:
            root = Path(temp_dir)
            pid_file = root / "child.pid"
            parent = root / "parent.py"
            parent.write_text(
                "import subprocess, sys, time\n"
                "from pathlib import Path\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
                f"Path(r'{pid_file}').write_text(str(child.pid))\n"
                "time.sleep(60)\n",
                encoding="utf-8",
            )
            res = run_qemu_boot(
                timeout=1.5,
                quiet=True,
                custom_command=[sys.executable, str(parent)],
                serial_log_override=root / "serial.log",
                temp_root=root,
            )
            self.assertEqual(res.status, "timeout")
            child_pid = int(pid_file.read_text())
            probe = subprocess.run(
                ["tasklist.exe", "/FI", f"PID eq {child_pid}", "/NH"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotIn(str(child_pid), probe.stdout)


if __name__ == "__main__":
    unittest.main()
