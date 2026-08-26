"""Tests for Windows panic-path output validation."""

from __future__ import annotations

import sys
import unittest
import hashlib
from concurrent.futures import ThreadPoolExecutor
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
    @staticmethod
    def _fake_build(repo_root, debug=False, panic_test=False, esp_dir=None, cargo_target_dir=None):
        del repo_root, debug, panic_test, cargo_target_dir
        kernel = Path(esp_dir) / "malrynth" / "kernel.elf"
        loader = Path(esp_dir) / "EFI" / "BOOT" / "BOOTX64.EFI"
        kernel.parent.mkdir(parents=True, exist_ok=True)
        loader.parent.mkdir(parents=True, exist_ok=True)
        kernel.write_bytes(b"immutable-panic-kernel")
        loader.write_bytes(b"loader")
        return 0

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
            with patch("malrynth_tooling.panic.build_image", side_effect=self._fake_build), \
                 patch("malrynth_tooling.panic.run_qemu_boot", return_value=boot), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 1, "", "")):
                self.assertEqual(check_panic_path(Path(temp_dir), timeout=0.1), 1)

    def test_validator_rejects_missing_panic_diagnostics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            boot = BootRunnerResult(
                "fail-marker", run_dir / "serial.log", "MALRYNTH_M0_BOOT_FAIL\n", 0.1, run_dir
            )
            with patch("malrynth_tooling.panic.build_image", side_effect=self._fake_build), \
                 patch("malrynth_tooling.panic.run_qemu_boot", return_value=boot), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 1, "", "")):
                self.assertEqual(check_panic_path(Path(temp_dir)), 1)

    def test_symbolizer_uses_the_same_run_scoped_kernel(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "boot"
            boot = BootRunnerResult("fail-marker", run_dir / "serial.log", VALID_PANIC, 0.1, run_dir)
            seen: dict[str, Path] = {}

            def symbolize(args, **kwargs):
                del kwargs
                seen["kernel"] = Path(args[args.index("--kernel") + 1])
                return CompletedProcess(args, 0, "frame+0x1\n", "")

            with patch("malrynth_tooling.panic.build_image", side_effect=self._fake_build), \
                 patch("malrynth_tooling.panic.run_qemu_boot", return_value=boot) as run, \
                 patch("malrynth_tooling.panic.subprocess.run", side_effect=symbolize):
                self.assertEqual(check_panic_path(Path(temp_dir)), 0)
            boot_esp = Path(run.call_args.kwargs["esp_dir_override"])
            self.assertEqual(seen["kernel"], boot_esp / "malrynth" / "kernel.elf")
            self.assertNotEqual(boot_esp, Path(temp_dir) / "esp")

    def test_kernel_change_after_hash_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "boot"
            boot = BootRunnerResult("fail-marker", run_dir / "serial.log", VALID_PANIC, 0.1, run_dir)

            def mutate_kernel(*args, **kwargs):
                esp = Path(kwargs["esp_dir_override"])
                (esp / "malrynth" / "kernel.elf").write_bytes(b"swapped-kernel")
                return boot

            with patch("malrynth_tooling.panic.build_image", side_effect=self._fake_build), \
                 patch("malrynth_tooling.panic.run_qemu_boot", side_effect=mutate_kernel), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 0, "frame+0x1\n", "")):
                self.assertEqual(check_panic_path(Path(temp_dir)), 1)

    def test_panic_run_never_changes_canonical_kernel(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            canonical = root / "esp" / "malrynth" / "kernel.elf"
            canonical.parent.mkdir(parents=True)
            canonical.write_bytes(b"canonical-normal-kernel")
            before = hashlib.sha256(canonical.read_bytes()).digest()
            run_dir = root / "boot"
            boot = BootRunnerResult("fail-marker", run_dir / "serial.log", VALID_PANIC, 0.1, run_dir)
            with patch("malrynth_tooling.panic.build_image", side_effect=self._fake_build), \
                 patch("malrynth_tooling.panic.run_qemu_boot", return_value=boot), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 0, "frame+0x1\n", "")):
                self.assertEqual(check_panic_path(root), 0)
            self.assertEqual(hashlib.sha256(canonical.read_bytes()).digest(), before)

    def test_concurrent_panic_preparation_uses_distinct_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "boot"
            boot = BootRunnerResult("fail-marker", run_dir / "serial.log", VALID_PANIC, 0.1, run_dir)
            boot_esps: list[Path] = []

            def capture_boot(*args, **kwargs):
                del args
                boot_esps.append(Path(kwargs["esp_dir_override"]))
                return boot

            def execute(_index: int) -> int:
                return check_panic_path(root)

            with patch("malrynth_tooling.panic.build_image", side_effect=self._fake_build), \
                 patch("malrynth_tooling.panic.run_qemu_boot", side_effect=capture_boot), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 0, "frame+0x1\n", "")):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(execute, (1, 2)))
            self.assertEqual(results, [0, 0])
            self.assertEqual(len(set(boot_esps)), 2)

    def test_cancelled_panic_run_cleans_run_scoped_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "boot"
            boot = BootRunnerResult("cancelled", run_dir / "serial.log", "", 0.1, run_dir)
            captured: list[Path] = []

            def capture_boot(*args, **kwargs):
                del args
                captured.append(Path(kwargs["esp_dir_override"]))
                return boot

            with patch("malrynth_tooling.panic.build_image", side_effect=self._fake_build), \
                 patch("malrynth_tooling.panic.run_qemu_boot", side_effect=capture_boot), \
                 patch("malrynth_tooling.panic.subprocess.run", return_value=CompletedProcess([], 1, "", "")):
                self.assertEqual(check_panic_path(root), 1)
            self.assertEqual(len(captured), 1)
            self.assertFalse(captured[0].exists())


if __name__ == "__main__":
    unittest.main()
