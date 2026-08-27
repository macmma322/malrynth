"""Command line interface dispatcher for Malrynth Windows tooling."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .build import build_image
from .config import MalrynthConfig, TARGET_KERNEL, TARGET_LOADER
from .doctor import run_doctor
from .pe_diff import diff_pe
from .pe_inspect import format_pe_report, inspect_pe
from .panic import check_panic_path
from .runner import run_qemu_boot
from .util import format_fail, format_info, format_ok, format_warn
from .verify import validate_kernel_elf, validate_loader_pe


def cmd_pe_inspect(args: argparse.Namespace) -> int:
    cfg = MalrynthConfig()
    target_path = Path(args.file).resolve() if args.file else (cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI")
    try:
        pe = inspect_pe(target_path)
        print(format_pe_report(pe))
        return 0
    except Exception as e:
        print(format_fail(f"PE inspection failed: {e}"), file=sys.stderr)
        return 1


def cmd_pe_diff(args: argparse.Namespace) -> int:
    try:
        report = diff_pe(args.file_a, args.file_b)
        print(report.format_report())
        return 0 if report.is_identical else 1
    except Exception as e:
        print(format_fail(f"PE diff failed: {e}"), file=sys.stderr)
        return 1


def cmd_doctor(args: argparse.Namespace) -> int:
    return run_doctor()


def cmd_build(args: argparse.Namespace) -> int:
    return build_image(debug=args.debug, panic_test=args.panic_test)


def cmd_run(args: argparse.Namespace) -> int:
    result = run_qemu_boot(
        timeout=args.timeout,
        interactive=args.interactive,
        quiet=args.quiet,
        memory_mib=args.memory_mib,
    )
    return 0 if result.is_success else 1


def cmd_verify(args: argparse.Namespace) -> int:
    cfg = MalrynthConfig()
    loader_path = cfg.esp_dir / "EFI" / "BOOT" / "BOOTX64.EFI"
    kernel_path = cfg.esp_dir / "malrynth" / "kernel.elf"

    failures = 0
    try:
        loader_info = validate_loader_pe(loader_path)
        print(format_ok(f"loader PE/COFF valid: {loader_info['format']} ({loader_info['size_bytes']} bytes)"))
    except Exception as e:
        print(format_fail(f"loader validation failed: {e}"))
        failures += 1

    try:
        kernel_info = validate_kernel_elf(kernel_path)
        print(format_ok(f"kernel ELF valid: {kernel_info['format']} {kernel_info['type']} ({kernel_info['size_bytes']} bytes)"))
    except Exception as e:
        print(format_fail(f"kernel validation failed: {e}"))
        failures += 1

    return 0 if failures == 0 else 1


def cmd_check_panic_path(args: argparse.Namespace) -> int:
    return check_panic_path(timeout=args.timeout)


def cmd_test(args: argparse.Namespace) -> int:
    cfg = MalrynthConfig()
    failures = 0

    def step(name: str, cmd_list: list[str], env: dict[str, str] | None = None) -> bool:
        print(format_info(name))
        res = subprocess.run(cmd_list, cwd=str(cfg.root), env=env)
        if res.returncode == 0:
            print(format_ok(name))
            return True
        else:
            print(format_fail(name))
            nonlocal failures
            failures += 1
            return False

    # 1. Formatting
    step("formatting", ["cargo", "fmt", "--all", "--", "--check"])

    # 2. Lint ABI
    step("lint (abi, host)", ["cargo", "clippy", "-p", "malrynth-abi", "--all-targets", "--", "-D", "warnings"])

    # 3. Lint Loader
    loader_env = os.environ.copy()
    loader_env["CARGO_ENCODED_RUSTFLAGS"] = cfg.loader_encoded_rustflags
    loader_env.pop("RUSTFLAGS", None)
    step(
        "lint (loader)",
        ["cargo", "clippy", "-p", "malboot", "--target", TARGET_LOADER, "--", "-D", "warnings"],
        env=loader_env,
    )

    # 4. Lint Kernel
    kernel_env = os.environ.copy()
    kernel_env["CARGO_ENCODED_RUSTFLAGS"] = cfg.kernel_encoded_rustflags
    kernel_env.pop("RUSTFLAGS", None)
    step(
        "lint (kernel)",
        ["cargo", "clippy", "-p", "malrynth-kernel", "--target", TARGET_KERNEL, "--", "-D", "warnings"],
        env=kernel_env,
    )

    # 5. Lint Kernel (panic-test)
    step(
        "lint (kernel, panic-test)",
        [
            "cargo", "clippy", "-p", "malrynth-kernel", "--target", TARGET_KERNEL,
            "--features", "panic-test", "--", "-D", "warnings",
        ],
        env=kernel_env,
    )

    # 6. Unit tests
    step("unit tests (abi)", ["cargo", "test", "-p", "malrynth-abi"])
    step("unit tests (loader memory map)", ["cargo", "test", "-p", "malboot", "--lib"])
    step("unit tests (kernel memory)", ["cargo", "test", "-p", "malrynth-kernel", "--lib"])

    # 7. Build
    print(format_info("build"))
    if build_image() == 0:
        print(format_ok("build"))
    else:
        print(format_fail("build"))
        failures += 1

    # 8. Boot smoke test (if requested and QEMU/OVMF present)
    if not args.skip_boot:
        boots = max(1, args.boots)
        for i in range(1, boots + 1):
            print(format_info(f"boot smoke test {i}/{boots}"))
            res = run_qemu_boot(timeout=60.0, quiet=True)
            if res.is_success:
                print(format_ok(f"boot smoke test {i}/{boots}"))
            else:
                print(format_fail(f"boot smoke test {i}/{boots}"))
                failures += 1
        print(format_info("panic path"))
        if check_panic_path(cfg.root) == 0:
            print(format_ok("panic path"))
        else:
            print(format_fail("panic path"))
            failures += 1
    else:
        print(format_warn("boot smoke tests skipped (--skip-boot)"))

    print()
    if failures == 0:
        print(format_ok("all checks passed"))
        return 0
    else:
        print(format_fail(f"{failures} check(s) failed"))
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="malrynth",
        description="Malrynth Operating System Windows Tooling (Experimental)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Inspect host and toolchain readiness")
    p_doctor.set_defaults(func=cmd_doctor)

    # build
    p_build = subparsers.add_parser("build", help="Build Malrynth loader, kernel, and ESP")
    p_build.add_argument("--debug", action="store_true", help="Build debug profile instead of release")
    p_build.add_argument("--panic-test", action="store_true", help="Build kernel with panic-test feature")
    p_build.set_defaults(func=cmd_build)

    # run
    p_run = subparsers.add_parser("run", help="Boot Malrynth image under supervised QEMU")
    p_run.add_argument("--timeout", type=float, default=60.0, help="Boot timeout in seconds (default 60)")
    p_run.add_argument("--memory-mib", type=int, default=1024, help="Guest RAM in MiB")
    p_run.add_argument("--interactive", action="store_true", help="Run QEMU interactively in console")
    p_run.add_argument("--quiet", action="store_true", help="Suppress serial output dump")
    p_run.set_defaults(func=cmd_run)

    # verify
    p_verify = subparsers.add_parser("verify", help="Validate binary artifacts in esp/")
    p_verify.set_defaults(func=cmd_verify)

    p_panic = subparsers.add_parser("check-panic-path", help="Validate deliberate kernel panic diagnostics")
    p_panic.add_argument("--timeout", type=float, default=60.0, help="Panic boot timeout in seconds")
    p_panic.set_defaults(func=cmd_check_panic_path)

    # pe-inspect
    p_pe_inspect = subparsers.add_parser("pe-inspect", help="Inspect structural PE/COFF header of a binary")
    p_pe_inspect.add_argument("file", nargs="?", default=None, help="Path to PE/EFI binary (default: esp/EFI/BOOT/BOOTX64.EFI)")
    p_pe_inspect.set_defaults(func=cmd_pe_inspect)

    # pe-diff
    p_pe_diff = subparsers.add_parser("pe-diff", help="Structurally compare two PE/COFF binaries")
    p_pe_diff.add_argument("file_a", help="First PE/EFI binary path")
    p_pe_diff.add_argument("file_b", help="Second PE/EFI binary path")
    p_pe_diff.set_defaults(func=cmd_pe_diff)

    # test
    p_test = subparsers.add_parser("test", help="Run formatting, lints, unit tests, and build")
    p_test.add_argument("--boots", type=int, default=3, help="Number of repeated boot smoke tests (default 3)")
    p_test.add_argument("--skip-boot", action="store_true", help="Skip QEMU boot smoke tests")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
