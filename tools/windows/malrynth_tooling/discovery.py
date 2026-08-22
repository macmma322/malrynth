"""Discovery functions for Windows host, Git, Rust toolchain, QEMU, and OVMF firmware."""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .config import TARGET_KERNEL, TARGET_LOADER


def get_host_info() -> dict[str, str]:
    """Retrieve host OS, version, architecture, and CPU count."""
    os_name = platform.system()
    os_release = platform.release()
    os_version = platform.version()
    arch = platform.machine()
    cpus = str(os.cpu_count() or "?")

    # On Windows, try to get pretty caption from Win32 or platform
    pretty_os = f"{os_name} {os_release} (Build {os_version})"
    if sys.platform == "win32":
        try:
            # Query Windows version details
            win_ver = sys.getwindowsversion()
            pretty_os = f"Windows {win_ver.major}.{win_ver.minor} (Build {win_ver.build})"
        except Exception:
            pass

    return {
        "os": pretty_os,
        "kernel": f"{os_name} {os_version}",
        "architecture": arch,
        "cpus": cpus,
    }


def get_filesystem_info(path: Path) -> dict[str, str | int]:
    """Retrieve filesystem type and free space for the drive hosting path."""
    abs_path = path.resolve()
    fs_type = "unknown"
    free_bytes = 0
    total_bytes = 0

    if sys.platform == "win32":
        try:
            drive = abs_path.drive
            if not drive and str(abs_path).startswith("\\\\"):
                # UNC path root
                root_path = str(abs_path).split("\\")[0:4]
                root_str = "\\".join(root_path) + "\\"
            else:
                root_str = f"{drive}\\" if drive else str(abs_path)

            volume_name_buf = ctypes.create_unicode_buffer(261)
            fs_name_buf = ctypes.create_unicode_buffer(261)
            serial_number = ctypes.c_ulong()
            max_component_length = ctypes.c_ulong()
            file_system_flags = ctypes.c_ulong()

            res = ctypes.windll.kernel32.GetVolumeInformationW(
                root_str,
                volume_name_buf,
                ctypes.sizeof(volume_name_buf) // 2,
                ctypes.byref(serial_number),
                ctypes.byref(max_component_length),
                ctypes.byref(file_system_flags),
                fs_name_buf,
                ctypes.sizeof(fs_name_buf) // 2,
            )
            if res != 0:
                fs_type = fs_name_buf.value
        except Exception:
            pass

    try:
        usage = shutil.disk_usage(abs_path)
        free_bytes = usage.free
        total_bytes = usage.total
    except Exception:
        pass

    return {
        "filesystem": fs_type,
        "free_bytes": free_bytes,
        "total_bytes": total_bytes,
        "free_gb": f"{free_bytes / (1024**3):.1f} GB",
    }


def get_git_info(repo_root: Path) -> dict[str, str | None]:
    """Retrieve Git version and relevant repository configuration."""
    git_version: str | None = None
    file_mode: str | None = None
    autocrlf: str | None = None
    eol: str | None = None

    try:
        res = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        git_version = res.stdout.strip()
    except Exception:
        pass

    if git_version is not None:
        def query_config(key: str) -> str | None:
            try:
                res = subprocess.run(
                    ["git", "-C", str(repo_root), "config", "--get", key],
                    capture_output=True,
                    text=True,
                )
                if res.returncode == 0:
                    return res.stdout.strip()
            except Exception:
                pass
            return None

        file_mode = query_config("core.fileMode")
        autocrlf = query_config("core.autocrlf")
        eol = query_config("core.eol")

    return {
        "git_version": git_version,
        "core_filemode": file_mode,
        "core_autocrlf": autocrlf,
        "core_eol": eol,
    }


def get_rust_toolchain_info() -> dict[str, object]:
    """Inspect rustup, rustc, cargo, and installed compilation targets."""
    info: dict[str, object] = {
        "rustup_version": None,
        "rustc_version": None,
        "cargo_version": None,
        "active_toolchain": None,
        "installed_targets": [],
        "loader_target_installed": False,
        "kernel_target_installed": False,
        "error": None,
    }

    try:
        res = subprocess.run(["rustup", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            info["rustup_version"] = res.stdout.splitlines()[0]
    except Exception:
        pass

    try:
        res = subprocess.run(["rustc", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            info["rustc_version"] = res.stdout.strip()
    except Exception:
        pass

    try:
        res = subprocess.run(["cargo", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            info["cargo_version"] = res.stdout.strip()
    except Exception:
        pass

    try:
        res = subprocess.run(["rustup", "show", "active-toolchain"], capture_output=True, text=True)
        if res.returncode == 0:
            info["active_toolchain"] = res.stdout.strip().splitlines()[0]
    except Exception:
        pass

    try:
        res = subprocess.run(["rustup", "target", "list", "--installed"], capture_output=True, text=True)
        if res.returncode == 0:
            targets = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            info["installed_targets"] = targets
            info["loader_target_installed"] = TARGET_LOADER in targets
            info["kernel_target_installed"] = TARGET_KERNEL in targets
    except Exception:
        pass

    return info


def find_qemu(override_path: str | None = None) -> tuple[Path | None, str]:
    """Find qemu-system-x86_64 binary.

    Precedence:
    1. Explicit parameter or MALRYNTH_QEMU environment variable
    2. PATH discovery
    3. Standard Windows installation directories
    """
    env_override = override_path or os.environ.get("MALRYNTH_QEMU")
    if env_override:
        p = Path(env_override).resolve()
        if p.is_file():
            return p, f"environment override ({p})"
        return None, f"environment override path does not exist: {env_override}"

    # Search PATH
    which_qemu = shutil.which("qemu-system-x86_64")
    if which_qemu:
        return Path(which_qemu).resolve(), f"PATH ({which_qemu})"

    # Standard Windows install locations
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    user_profile = os.environ.get("USERPROFILE", "")

    candidates = [
        Path(program_files) / "qemu" / "qemu-system-x86_64.exe",
        Path(program_files_x86) / "qemu" / "qemu-system-x86_64.exe",
        Path(r"C:\tools\qemu\qemu-system-x86_64.exe"),
        Path(local_app_data) / "Programs" / "qemu" / "qemu-system-x86_64.exe",
        Path(user_profile) / "scoop" / "apps" / "qemu" / "current" / "qemu-system-x86_64.exe",
    ]

    for cand in candidates:
        if cand.is_file():
            return cand.resolve(), f"standard location ({cand})"

    return None, "qemu-system-x86_64 not found on PATH or standard locations"


def find_ovmf(
    code_override: str | None = None,
    vars_override: str | None = None,
    dir_override: str | None = None,
) -> tuple[Path | None, Path | None, str]:
    """Find OVMF firmware split CODE and VARS files.

    Precedence:
    1. MALRYNTH_OVMF_CODE and MALRYNTH_OVMF_VARS environment variables
    2. MALRYNTH_OVMF environment variable (directory or file prefix)
    3. Developer cache in %LOCALAPPDATA%\\Malrynth\\firmware or %USERPROFILE%\\.malrynth\\firmware
    4. QEMU share/ directory if QEMU is installed
    5. Standard Chocolatey/Scoop edk2 locations
    """
    code_env = code_override or os.environ.get("MALRYNTH_OVMF_CODE")
    vars_env = vars_override or os.environ.get("MALRYNTH_OVMF_VARS")

    if code_env and vars_env:
        c_path = Path(code_env).resolve()
        v_path = Path(vars_env).resolve()
        if c_path.is_file() and v_path.is_file():
            return c_path, v_path, "explicit environment override (CODE + VARS)"
        missing = []
        if not c_path.is_file():
            missing.append(f"CODE not found: {c_path}")
        if not v_path.is_file():
            missing.append(f"VARS not found: {v_path}")
        return None, None, f"invalid environment override: {'; '.join(missing)}"

    # Directory override
    dir_env = dir_override or os.environ.get("MALRYNTH_OVMF")
    search_dirs: list[Path] = []
    if dir_env:
        d_path = Path(dir_env).resolve()
        if d_path.is_dir():
            search_dirs.append(d_path)
        elif d_path.is_file():
            # If pointing to a single file, look in its parent
            search_dirs.append(d_path.parent)

    # Developer cache locations
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    user_profile = os.environ.get("USERPROFILE", "")
    if local_app_data:
        search_dirs.append(Path(local_app_data) / "Malrynth" / "firmware")
    if user_profile:
        search_dirs.append(Path(user_profile) / ".malrynth" / "firmware")

    # QEMU installation directory
    qemu_bin, _ = find_qemu()
    if qemu_bin:
        search_dirs.append(qemu_bin.parent / "share")
        search_dirs.append(qemu_bin.parent)

    # Standard package locations
    search_dirs.extend([
        Path(r"C:\tools\edk2"),
        Path(r"C:\tools\ovmf"),
        Path(r"C:\ProgramData\chocolatey\lib\edk2-ovmf"),
        Path(user_profile) / "scoop" / "apps" / "edk2" / "current",
    ])

    pair_names = [
        ("OVMF_CODE_4M.fd", "OVMF_VARS_4M.fd"),
        ("OVMF_CODE.fd", "OVMF_VARS.fd"),
        ("edk2-x86_64-code.fd", "edk2-i386-vars.fd"),
        ("edk2-x86_64-code.fd", "edk2-arm-vars.fd"),
        ("ovmf-x86_64-code.bin", "ovmf-x86_64-vars.bin"),
    ]

    for s_dir in search_dirs:
        if not s_dir.is_dir():
            continue
        for code_name, vars_name in pair_names:
            c = s_dir / code_name
            v = s_dir / vars_name
            if c.is_file() and v.is_file():
                return c.resolve(), v.resolve(), f"found in {s_dir}"

    return None, None, "OVMF firmware not found. Set MALRYNTH_OVMF_CODE and MALRYNTH_OVMF_VARS or place firmware in %LOCALAPPDATA%\\Malrynth\\firmware"
