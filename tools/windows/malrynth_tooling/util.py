"""Cross-platform utility functions and output formatting for Malrynth tooling."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path


class TerminalColors:
    """ANSI color codes for terminal output with auto-detection."""

    def __init__(self, enabled: bool | None = None) -> None:
        if enabled is None:
            # Enable if stdout is a TTY and NO_COLOR is not set
            is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
            no_color = bool(os.environ.get("NO_COLOR"))
            self.enabled = is_tty and not no_color
            if sys.platform == "win32" and self.enabled:
                # Enable virtual terminal processing on Windows if possible
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    h_std_out = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                    mode = ctypes.c_ulong()
                    kernel32.GetConsoleMode(h_std_out, ctypes.byref(mode))
                    # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                    kernel32.SetConsoleMode(h_std_out, mode.value | 0x0004)
                except Exception:
                    pass
        else:
            self.enabled = enabled

    @property
    def red(self) -> str:
        return "\033[31m" if self.enabled else ""

    @property
    def green(self) -> str:
        return "\033[32m" if self.enabled else ""

    @property
    def yellow(self) -> str:
        return "\033[33m" if self.enabled else ""

    @property
    def bold(self) -> str:
        return "\033[1m" if self.enabled else ""

    @property
    def reset(self) -> str:
        return "\033[0m" if self.enabled else ""


colors = TerminalColors()


def format_info(msg: str) -> str:
    return f"{colors.bold}==>{colors.reset} {msg}"


def format_ok(msg: str) -> str:
    return f"{colors.green}  ok{colors.reset}   {msg}"


def format_warn(msg: str) -> str:
    return f"{colors.yellow}  warn{colors.reset} {msg}"


def format_fail(msg: str) -> str:
    return f"{colors.red}  FAIL{colors.reset} {msg}"


def log_info(msg: str) -> None:
    print(format_info(msg))


def log_ok(msg: str) -> None:
    print(format_ok(msg))


def log_warn(msg: str) -> None:
    print(format_warn(msg), file=sys.stderr)


def log_fail(msg: str) -> None:
    print(format_fail(msg), file=sys.stderr)


def compute_sha256(path: Path | str) -> str:
    """Compute SHA-256 hexadecimal digest for a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    import re
    ansi_regex = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\[=[0-9]*h")
    return ansi_regex.sub("", text)
