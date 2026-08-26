"""Process supervisor and QEMU boot runner for Malrynth M0."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .config import BOOT_FAIL_MARKER, BOOT_OK_MARKER, MalrynthConfig
from .discovery import find_ovmf, find_qemu
from .util import format_fail, format_info, format_ok, strip_ansi


class BootRunnerResult:
    def __init__(self, status: str, serial_log_path: Path, cleaned_output: str,
                 duration_seconds: float, run_directory: Path) -> None:
        self.status = status
        self.serial_log_path = serial_log_path
        self.cleaned_output = cleaned_output
        self.duration_seconds = duration_seconds
        self.run_directory = run_directory

    @property
    def is_success(self) -> bool:
        return self.status == "ok"


def _terminate_process_tree(proc: subprocess.Popen[bytes]) -> None:
    """Terminate a process and all descendants without invoking a command shell."""
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        pid = int(proc.pid)
        subprocess.run(
            ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10.0,
        )
    else:
        proc.terminate()
    try:
        proc.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3.0)


def _classify_output(content: str) -> str | None:
    """Apply the one boot correctness state machine used by every mode."""
    lines = strip_ansi(content).splitlines()
    if any(line.strip() == BOOT_FAIL_MARKER for line in lines):
        return "fail-marker"
    if any(line.strip() == BOOT_OK_MARKER for line in lines):
        return "ok"
    return None


def _copy_vars_template(template: Path, run_directory: Path) -> Path:
    """Copy pristine NVRAM state into one run directory and return the mutable path."""
    destination = run_directory / "vars.fd"
    shutil.copy2(template, destination)
    return destination


def run_qemu_boot(
    repo_root: Path | None = None,
    timeout: float = 60.0,
    interactive: bool = False,
    quiet: bool = False,
    custom_command: list[str] | None = None,
    serial_log_override: Path | None = None,
    temp_root: Path | None = None,
    retain_run_dir: bool = False,
    esp_dir_override: Path | None = None,
) -> BootRunnerResult:
    """Supervise QEMU until an exact marker, process exit, cancellation, or timeout."""
    cfg = MalrynthConfig(repo_root)
    cfg.build_dir.mkdir(parents=True, exist_ok=True)
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    parent = str(temp_root.resolve()) if temp_root else None
    run_directory = Path(tempfile.mkdtemp(prefix="malrynth-qemu-", dir=parent))
    serial_log = serial_log_override or (run_directory / "serial.log")
    stderr_log = run_directory / "stderr.log"
    serial_log.parent.mkdir(parents=True, exist_ok=True)
    serial_log.write_text("", encoding="utf-8")

    def missing_result() -> BootRunnerResult:
        return BootRunnerResult("missing-dependency", serial_log, "", 0.0, run_directory)

    try:
        if custom_command is None:
            esp_dir = esp_dir_override.resolve() if esp_dir_override else cfg.esp_dir
            loader_path = esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"
            kernel_path = esp_dir / "malrynth" / "kernel.elf"
            if not loader_path.is_file():
                print(format_fail("no boot image; run build first"), file=sys.stderr)
                return missing_result()
            if not kernel_path.is_file():
                print(format_fail("no kernel image; run build first"), file=sys.stderr)
                return missing_result()
            qemu_bin, qemu_desc = find_qemu()
            if not qemu_bin:
                print(format_fail(f"QEMU binary missing ({qemu_desc})"), file=sys.stderr)
                return missing_result()
            ovmf_code, ovmf_vars, ovmf_desc = find_ovmf()
            if not ovmf_code or not ovmf_vars:
                print(format_fail(f"OVMF firmware missing ({ovmf_desc})"), file=sys.stderr)
                return missing_result()

            vars_copy = _copy_vars_template(ovmf_vars, run_directory)
            qemu_args = [
                str(qemu_bin), "-machine", "q35", "-m", "1024", "-cpu", "qemu64",
                "-drive", f"if=pflash,format=raw,readonly=on,file={ovmf_code}",
                "-drive", f"if=pflash,format=raw,file={vars_copy}",
                "-drive", f"format=raw,file=fat:rw:{esp_dir}",
                "-display", "default" if interactive else "none",
                "-net", "none", "-no-reboot", "-serial", f"file:{serial_log}",
            ]
        else:
            qemu_args = list(custom_command)

        mode = "interactive" if interactive else "headless"
        print(format_info(f"booting Malrynth M0 under {mode} supervisor (timeout {timeout}s)"))
        start_time = time.monotonic()
        deadline = start_time + timeout
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        with open(stderr_log, "wb") as err_f:
            proc = subprocess.Popen(
                qemu_args, stdout=subprocess.DEVNULL, stderr=err_f,
                shell=False, creationflags=creationflags,
            )

        terminal_reason = "timeout"
        try:
            while time.monotonic() < deadline:
                content = serial_log.read_text(encoding="utf-8", errors="replace") if serial_log.is_file() else ""
                marker_status = _classify_output(content)
                if marker_status is not None:
                    terminal_reason = "marker"
                    break
                if proc.poll() is not None:
                    terminal_reason = "process-exited"
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            terminal_reason = "cancelled"
        finally:
            _terminate_process_tree(proc)

        duration = time.monotonic() - start_time
        raw_output = serial_log.read_text(encoding="utf-8", errors="replace") if serial_log.is_file() else ""
        cleaned = strip_ansi(raw_output)
        final_marker = _classify_output(cleaned)
        if terminal_reason == "cancelled":
            result_status = "cancelled"
        elif terminal_reason == "timeout":
            result_status = "timeout"
        elif final_marker is not None:
            result_status = final_marker
        else:
            result_status = "process-exited"
        if not quiet:
            print("----- serial output -----")
            for line in cleaned.splitlines():
                if line.strip():
                    print(line)
            print("-------------------------")

        if result_status == "ok":
            print(format_ok(f"boot succeeded in {duration:.2f}s: observed {BOOT_OK_MARKER}"))
        elif result_status == "fail-marker":
            print(format_fail(f"kernel reported failure: observed {BOOT_FAIL_MARKER}"), file=sys.stderr)
        elif result_status == "process-exited":
            print(format_fail("QEMU exited without emitting a marker"), file=sys.stderr)
        elif result_status == "cancelled":
            print(format_fail("QEMU run cancelled before success marker"), file=sys.stderr)
        else:
            print(format_fail(f"timed out after {timeout}s without observing {BOOT_OK_MARKER}"), file=sys.stderr)
        return BootRunnerResult(result_status, serial_log, cleaned, duration, run_directory)
    finally:
        if not retain_run_dir:
            shutil.rmtree(run_directory, ignore_errors=True)
