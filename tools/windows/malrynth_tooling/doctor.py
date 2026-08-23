"""Windows-native doctor implementation for Malrynth.

Strictly READ-ONLY. Never installs, upgrades, or mutates any configuration.
Reports what is present, what is missing, and how to obtain missing items.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .config import MalrynthConfig, TARGET_KERNEL, TARGET_LOADER
from .discovery import (
    find_ovmf,
    find_qemu,
    get_filesystem_info,
    get_git_info,
    get_host_info,
    get_qemu_version,
    get_rust_toolchain_info,
)
from .util import format_fail, format_info, format_ok, format_warn

MINIMUM_PYTHON = (3, 10)
REQUIRED_RUST_VERSION = "1.97.1"


def python_version_supported(version: tuple[int, ...]) -> bool:
    return version[:2] >= MINIMUM_PYTHON


def run_doctor(repo_root: Path | None = None) -> int:
    """Run all host and environment diagnostics and print report."""
    cfg = MalrynthConfig(repo_root)
    build_failures = 0
    boot_failures = 0
    warning_count = 0

    def print_item_ok(label: str, value: str) -> None:
        print(format_ok(f"{label:<22} {value}"))

    def print_item_warn(label: str, value: str) -> None:
        nonlocal warning_count
        warning_count += 1
        print(format_warn(f"{label:<22} {value}"), file=sys.stderr)

    def print_item_fail(label: str, hint: str, *, boot_only: bool = False, unsupported: bool = False) -> None:
        nonlocal build_failures, boot_failures
        if boot_only:
            boot_failures += 1
        else:
            build_failures += 1
        state = "UNSUPPORTED" if unsupported else "MISSING"
        print(format_fail(f"{label:<22} {state} -- {hint}"), file=sys.stderr)

    # 1. Host
    print(format_info("host"))
    host = get_host_info()
    print_item_ok("os", host["os"])
    print_item_ok("kernel", host["kernel"])
    print_item_ok("architecture", host["architecture"])
    print_item_ok("cpus", host["cpus"])
    print()

    # 2. Toolchain
    print(format_info("toolchain (required)"))
    git_info = get_git_info(cfg.root)
    if git_info["git_version"]:
        print_item_ok("git", git_info["git_version"])
    else:
        print_item_fail("git", "Git for Windows not found on PATH (https://git-scm.com)")

    rust = get_rust_toolchain_info()
    if rust["rustup_version"]:
        print_item_ok("rustup", str(rust["rustup_version"]))
    else:
        print_item_fail("rustup", "https://rustup.rs")

    if rust["cargo_version"]:
        print_item_ok("cargo", str(rust["cargo_version"]))
    else:
        print_item_fail("cargo", "https://rustup.rs")

    rustc_version = str(rust["rustc_version"] or "")
    if rustc_version.startswith(f"rustc {REQUIRED_RUST_VERSION} "):
        print_item_ok("rustc", rustc_version)
    elif rustc_version:
        print_item_fail("rustc", f"requires Rust {REQUIRED_RUST_VERSION}; found {rustc_version}", unsupported=True)
    else:
        print_item_fail("rustc", "https://rustup.rs")

    # Python check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if python_version_supported((sys.version_info.major, sys.version_info.minor, sys.version_info.micro)):
        print_item_ok("python", f"Python {py_ver} ({sys.executable})")
    else:
        print_item_fail("python", f"requires Python >= 3.10; found {py_ver}", unsupported=True)
    print()

    # 3. Compilation targets
    print(format_info("compilation targets (required)"))
    if rust["loader_target_installed"]:
        print_item_ok(TARGET_LOADER, "installed")
    else:
        print_item_fail(TARGET_LOADER, f"rustup target add {TARGET_LOADER}")

    if rust["kernel_target_installed"]:
        print_item_ok(TARGET_KERNEL, "installed")
    else:
        print_item_fail(TARGET_KERNEL, f"rustup target add {TARGET_KERNEL}")
    print()

    # 4. Virtualisation
    print(format_info("virtualisation (required to run M0)"))
    qemu_bin, qemu_desc = find_qemu()
    if qemu_bin:
        qemu_version, qemu_version_desc = get_qemu_version(qemu_bin)
        if qemu_version:
            print_item_ok("qemu-system-x86_64", f"{qemu_bin} [{qemu_desc}; {qemu_version_desc}]")
        else:
            print_item_fail("qemu-system-x86_64", f"executable probe failed: {qemu_version_desc}", boot_only=True)
    else:
        print_item_fail(
            "qemu-system-x86_64",
            "winget install SoftwareFreedomConservancy.QEMU, choco install qemu, or set MALRYNTH_QEMU",
            boot_only=True,
        )

    ovmf_code, ovmf_vars, ovmf_desc = find_ovmf()
    if ovmf_code and ovmf_vars:
        print_item_ok("OVMF code", f"{ovmf_code}")
        print_item_ok("OVMF vars", f"{ovmf_vars} [{ovmf_desc}]")
    else:
        label = "OVMF firmware"
        hint = ovmf_desc if "INVALID FIRMWARE PAIR" in ovmf_desc else (
            "Set MALRYNTH_OVMF_CODE and MALRYNTH_OVMF_VARS, or place firmware in %LOCALAPPDATA%\\Malrynth\\firmware"
        )
        print_item_fail(label, hint, boot_only=True)

    # Windows Hypervisor Platform / WHPX check (equivalent of KVM on Linux)
    if sys.platform == "win32":
        # Check if WHPX is available or TCG fallback
        print_item_ok("acceleration", "TCG emulation (default). WHPX can be enabled if configured in QEMU.")
    print()

    # 5. Workspace & Filesystem
    print(format_info("workspace"))
    print_item_ok("root", str(cfg.root))
    print_item_ok("target dir", str(cfg.cargo_target_dir))

    fs_info = get_filesystem_info(cfg.root)
    print_item_ok("filesystem", str(fs_info["filesystem"]))
    print_item_ok("free disk space", str(fs_info["free_gb"]))

    fs_type_lower = str(fs_info["filesystem"]).lower()
    if "ntfs" in fs_type_lower or "refs" in fs_type_lower:
        file_mode = git_info.get("core_filemode")
        if file_mode == "false":
            print_item_ok("git core.fileMode", "false (correct for Windows filesystem)")
        elif file_mode == "true":
            print_item_warn(
                "git core.fileMode",
                "is set to 'true'; on NTFS/Windows this may cause spurious filemode diffs. Recommend: git config core.fileMode false",
            )
        else:
            print_item_ok("git core.fileMode", f"{file_mode or 'unset'}")

        autocrlf = git_info.get("core_autocrlf")
        if autocrlf:
            print_item_ok("git core.autocrlf", autocrlf)
        eol = git_info.get("core_eol")
        if eol:
            print_item_ok("git core.eol", eol)

    print()
    build_ready = build_failures == 0
    boot_ready = build_ready and boot_failures == 0
    print(format_ok(f"BUILD READY: {'YES' if build_ready else 'NO'}") if build_ready else format_fail("BUILD READY: NO"))
    print(format_ok(f"BOOT READY: {'YES' if boot_ready else 'NO'}") if boot_ready else format_fail("BOOT READY: NO"))
    if warning_count > 0:
        print(format_info(f"{warning_count} warning(s) noted above"))
    return 0 if boot_ready else 1
