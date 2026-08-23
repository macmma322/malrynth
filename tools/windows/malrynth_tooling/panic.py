"""Windows-native end-to-end validation for the deliberate M0 panic path."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .build import build_image
from .config import BOOT_FAIL_MARKER, BOOT_OK_MARKER, MalrynthConfig
from .runner import run_qemu_boot
from .util import format_fail, format_info, format_ok

FRAME_PATTERN = re.compile(r"^\s*#\d+\s+0x[0-9a-f]{16}\s*$", re.MULTILINE)


@dataclass(frozen=True)
class PanicOutputResult:
    is_valid: bool
    frame_count: int
    checks: dict[str, bool]


def evaluate_panic_output(output: str) -> PanicOutputResult:
    """Evaluate the same serial-output contract as Linux ``tools/check-panic-path``."""
    frames = len(FRAME_PATTERN.findall(output))
    checks = {
        "panic reached": re.search(r"^KERNEL PANIC", output, re.MULTILINE) is not None,
        "source location": re.search(r"^  at .*\.rs:\d+:\d+", output, re.MULTILINE) is not None,
        "panic message": "panic-test: this panic is intentional" in output,
        "backtrace header": re.search(r"^backtrace:", output, re.MULTILINE) is not None,
        "failure marker": BOOT_FAIL_MARKER in output,
        "success marker absent": BOOT_OK_MARKER not in output,
        "multiple frames": frames >= 2,
        "plausible frame chain": "no plausible frame chain" not in output,
    }
    return PanicOutputResult(all(checks.values()), frames, checks)


def check_panic_path(repo_root: Path | None = None, timeout: float = 60.0) -> int:
    """Build, boot, validate, symbolize, and then restore the normal M0 image."""
    cfg = MalrynthConfig(repo_root)
    result = 1
    try:
        print(format_info("building deliberate panic-test image"))
        if build_image(cfg.root, panic_test=True) != 0:
            print(format_fail("panic-test build failed"), file=sys.stderr)
        else:
            print(format_info("booting panic-test image (failure marker expected)"))
            boot = run_qemu_boot(cfg.root, timeout=timeout, quiet=True)
            evaluated = evaluate_panic_output(boot.cleaned_output)
            failures = 0
            if boot.status != "fail-marker":
                print(format_fail(f"panic runner status was {boot.status}; expected fail-marker"), file=sys.stderr)
                failures += 1
            for label, passed in evaluated.checks.items():
                if passed:
                    print(format_ok(label))
                else:
                    print(format_fail(label), file=sys.stderr)
                    failures += 1

            symbolizer = cfg.root / "tools" / "symbolize"
            kernel = cfg.esp_dir / "malrynth" / "kernel.elf"
            symbolized = subprocess.run(
                [sys.executable, str(symbolizer), "--kernel", str(kernel)],
                input=boot.cleaned_output,
                capture_output=True,
                text=True,
                cwd=str(cfg.root),
                shell=False,
                check=False,
            )
            symbols_ok = symbolized.returncode == 0 and re.search(r"\+0x[0-9a-f]+$", symbolized.stdout, re.MULTILINE)
            if symbols_ok:
                print(format_ok("symbolization resolved at least one frame"))
            else:
                print(format_fail("symbolization resolved no frames"), file=sys.stderr)
                if symbolized.stderr:
                    print(symbolized.stderr.rstrip(), file=sys.stderr)
                failures += 1
            result = 0 if failures == 0 else 1
    finally:
        print(format_info("restoring normal M0 image"))
        if build_image(cfg.root) != 0:
            print(format_fail("failed to restore normal M0 image"), file=sys.stderr)
            result = 1
    return result
