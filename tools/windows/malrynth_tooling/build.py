"""Windows-native build implementation for Malrynth M0 boot image."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .config import MalrynthConfig, TARGET_KERNEL, TARGET_LOADER
from .util import format_fail, format_info, format_ok, format_warn
from .verify import validate_kernel_elf, validate_loader_pe


def build_image(
    repo_root: Path | None = None,
    debug: bool = False,
    panic_test: bool = False,
) -> int:
    """Build the Malrynth loader and kernel, and assemble the ESP directory."""
    cfg = MalrynthConfig(repo_root)
    profile = "debug" if debug else "release"
    profile_flag = [] if debug else ["--release"]

    print(format_info(f"building loader ({TARGET_LOADER}, {profile})"))
    loader_env = os.environ.copy()
    loader_env["CARGO_ENCODED_RUSTFLAGS"] = cfg.loader_encoded_rustflags
    loader_env.pop("RUSTFLAGS", None)
    loader_env["CARGO_TARGET_DIR"] = str(cfg.cargo_target_dir)

    res = subprocess.run(
        ["cargo", "build", "-p", "malboot", "--target", TARGET_LOADER, *profile_flag],
        cwd=str(cfg.root),
        env=loader_env,
    )
    if res.returncode != 0:
        print(format_fail(f"loader compilation failed (exit code {res.returncode})"))
        return res.returncode

    kernel_features: list[str] = []
    if panic_test:
        kernel_features = ["--features", "panic-test"]

    print(format_info(f"building kernel ({TARGET_KERNEL}, {profile}{', panic-test' if panic_test else ''})"))
    kernel_env = os.environ.copy()
    kernel_env["CARGO_ENCODED_RUSTFLAGS"] = cfg.kernel_encoded_rustflags
    kernel_env.pop("RUSTFLAGS", None)
    kernel_env["CARGO_TARGET_DIR"] = str(cfg.cargo_target_dir)

    res = subprocess.run(
        ["cargo", "build", "-p", "malrynth-kernel", "--target", TARGET_KERNEL, *profile_flag, *kernel_features],
        cwd=str(cfg.root),
        env=kernel_env,
    )
    if res.returncode != 0:
        print(format_fail(f"kernel compilation failed (exit code {res.returncode})"))
        return res.returncode

    # Locate generated output binaries
    # Note: On Windows or Linux, malboot produces malboot.efi for UEFI target, and malrynth-kernel for none target.
    # On Windows host, the output might be named malboot.efi and malrynth-kernel (or malrynth-kernel.exe if msvc, but target is x86_64-unknown-none which produces ELF).
    loader_candidate = cfg.cargo_target_dir / TARGET_LOADER / profile / "malboot.efi"
    kernel_candidate = cfg.cargo_target_dir / TARGET_KERNEL / profile / "malrynth-kernel"
    if not kernel_candidate.is_file() and (cfg.cargo_target_dir / TARGET_KERNEL / profile / "malrynth-kernel.exe").is_file():
        kernel_candidate = cfg.cargo_target_dir / TARGET_KERNEL / profile / "malrynth-kernel.exe"

    if not loader_candidate.is_file():
        print(format_fail(f"loader binary not produced at expected location: {loader_candidate}"))
        return 1

    if not kernel_candidate.is_file():
        print(format_fail(f"kernel binary not produced at expected location: {kernel_candidate}"))
        return 1

    # Validate binaries
    try:
        loader_meta = validate_loader_pe(loader_candidate)
        kernel_meta = validate_kernel_elf(kernel_candidate)
    except Exception as e:
        print(format_fail(f"binary validation failed: {e}"))
        return 1

    # Assemble ESP directory
    print(format_info("assembling EFI system partition"))
    if cfg.esp_dir.exists():
        shutil.rmtree(cfg.esp_dir)

    esp_boot_dir = cfg.esp_dir / "EFI" / "BOOT"
    esp_kernel_dir = cfg.esp_dir / "malrynth"
    esp_boot_dir.mkdir(parents=True, exist_ok=True)
    esp_kernel_dir.mkdir(parents=True, exist_ok=True)

    dest_loader = esp_boot_dir / "BOOTX64.EFI"
    dest_kernel = esp_kernel_dir / "kernel.elf"

    shutil.copy2(loader_candidate, dest_loader)
    shutil.copy2(kernel_candidate, dest_kernel)

    loader_size = dest_loader.stat().st_size
    kernel_size = dest_kernel.stat().st_size

    # Size report
    cfg.build_dir.mkdir(parents=True, exist_ok=True)
    size_report = cfg.build_dir / "size-report.txt"
    size_report.write_text(
        f"loader_bytes={loader_size}\n"
        f"kernel_bytes={kernel_size}\n"
        f"profile={profile}\n",
        encoding="utf-8",
    )

    print(format_ok(f"loader  {loader_size} bytes ({loader_meta['format']})"))
    print(format_ok(f"kernel  {kernel_size} bytes ({kernel_meta['format']} {kernel_meta['type']})"))
    print(format_ok(f"image   {cfg.esp_dir}"))
    return 0
