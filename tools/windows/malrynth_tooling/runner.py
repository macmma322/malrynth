"""Process supervisor and QEMU boot runner for Malrynth M0."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .config import (
    BOOT_FAIL_MARKER,
    BOOT_OK_MARKER,
    MalrynthConfig,
)
from .discovery import find_ovmf, find_qemu
from .util import format_fail, format_info, format_ok, format_warn, strip_ansi


class BootRunnerResult:
    def __init__(
        self,
        status: str,  # "ok", "fail-marker", "process-exited", "timeout", "missing-dependency"
        serial_log_path: Path,
        cleaned_output: str,
        duration_seconds: float,
    ) -> None:
        self.status = status
        self.serial_log_path = serial_log_path
        self.cleaned_output = cleaned_output
        self.duration_seconds = duration_seconds

    @property
    def is_success(self) -> bool:
        return self.status == "ok"


def run_qemu_boot(
    repo_root: Path | None = None,
    timeout: float = 60.0,
    interactive: bool = False,
    quiet: bool = False,
    custom_command: list[str] | None = None,
    serial_log_override: Path | None = None,
) -> BootRunnerResult:
    """Supervise a QEMU boot execution until the success marker, failure marker, or timeout."""
    cfg = MalrynthConfig(repo_root)
    cfg.build_dir.mkdir(parents=True, exist_ok=True)
    serial_log = serial_log_override or (cfg.build_dir / "serial.log")
    stderr_log = cfg.build_dir / "qemu.stderr"

    # Precondition checks (only if not running a custom mock command)
    if custom_command is None:
        loader_path = cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"
        kernel_path = cfg.esp_dir / "malrynth" / "kernel.elf"

        if not loader_path.is_file():
            print(format_fail("no boot image; run build first"), file=sys.stderr)
            return BootRunnerResult("missing-dependency", serial_log, "", 0.0)

        if not kernel_path.is_file():
            print(format_fail("no kernel image; run build first"), file=sys.stderr)
            return BootRunnerResult("missing-dependency", serial_log, "", 0.0)

        qemu_bin, qemu_desc = find_qemu()
        if not qemu_bin:
            print(format_fail(f"QEMU binary missing ({qemu_desc})"), file=sys.stderr)
            return BootRunnerResult("missing-dependency", serial_log, "", 0.0)

        ovmf_code, ovmf_vars, ovmf_desc = find_ovmf()
        if not ovmf_code or not ovmf_vars:
            print(format_fail(f"OVMF firmware missing ({ovmf_desc})"), file=sys.stderr)
            return BootRunnerResult("missing-dependency", serial_log, "", 0.0)

        # Create a fresh pristine copy of the variable store in the build directory
        vars_copy = cfg.build_dir / "OVMF_VARS.fd"
        shutil.copy2(ovmf_vars, vars_copy)

        qemu_args = [
            str(qemu_bin),
            "-machine", "q35",
            "-m", "1024",
            "-cpu", "qemu64",
            "-drive", f"if=pflash,format=raw,readonly=on,file={ovmf_code}",
            "-drive", f"if=pflash,format=raw,file={vars_copy}",
            "-drive", f"format=raw,file=fat:rw:{cfg.esp_dir}",
            "-display", "none",
            "-net", "none",
            "-no-reboot",
        ]
    else:
        qemu_args = list(custom_command)

    # Initialize empty serial log
    serial_log.write_text("", encoding="utf-8")

    if interactive and custom_command is None:
        print(format_info("starting QEMU interactively (Ctrl-A X to quit)"))
        interactive_args = qemu_args + ["-serial", "mon:stdio"]
        res = subprocess.run(interactive_args)
        status = "ok" if res.returncode == 0 else "process-exited"
        return BootRunnerResult(status, serial_log, "", 0.0)

    # Non-interactive supervised launch
    if custom_command is None:
        cmd = qemu_args + ["-serial", f"file:{serial_log}"]
    else:
        cmd = qemu_args

    print(format_info(f"booting Malrynth M0 under supervisor (timeout {timeout}s)"))
    start_time = time.monotonic()
    deadline = start_time + timeout

    with open(stderr_log, "wb") as err_f:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=err_f,
        )

    result_status = "timeout"
    try:
        while time.monotonic() < deadline:
            # Check serial log content
            if serial_log.is_file():
                try:
                    content = serial_log.read_text(encoding="utf-8", errors="replace")
                    if BOOT_FAIL_MARKER in content:
                        result_status = "fail-marker"
                        break
                    if BOOT_OK_MARKER in content:
                        result_status = "ok"
                        break
                except Exception:
                    pass

            # Check if process died prematurely
            ret = proc.poll()
            if ret is not None:
                # Read one final time to avoid race condition where marker was written right before exit
                time.sleep(0.05)
                if serial_log.is_file():
                    content = serial_log.read_text(encoding="utf-8", errors="replace")
                    if BOOT_OK_MARKER in content:
                        result_status = "ok"
                        break
                    if BOOT_FAIL_MARKER in content:
                        result_status = "fail-marker"
                        break
                result_status = "process-exited"
                break

            time.sleep(0.1)
    finally:
        # Guarantee child process is terminated
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2.0)

    duration = time.monotonic() - start_time

    # Process and clean output
    raw_output = serial_log.read_text(encoding="utf-8", errors="replace") if serial_log.is_file() else ""
    cleaned = strip_ansi(raw_output)

    if not quiet:
        print("----- serial output -----")
        non_empty = [line for line in cleaned.splitlines() if line.strip()]
        for line in non_empty:
            print(line)
        print("-------------------------")

    if result_status == "ok":
        print(format_ok(f"boot succeeded in {duration:.2f}s: observed {BOOT_OK_MARKER}"))
    elif result_status == "fail-marker":
        print(format_fail(f"kernel reported failure: observed {BOOT_FAIL_MARKER}"), file=sys.stderr)
    elif result_status == "process-exited":
        print(format_fail(f"QEMU exited unexpectedly without emitting marker (see {stderr_log})"), file=sys.stderr)
    elif result_status == "timeout":
        print(format_fail(f"timed out after {timeout}s without observing {BOOT_OK_MARKER}"), file=sys.stderr)

    return BootRunnerResult(result_status, serial_log, cleaned, duration)
