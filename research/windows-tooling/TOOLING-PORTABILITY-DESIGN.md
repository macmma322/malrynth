# Malrynth Developer Tooling Portability Design

## 1. Problem Statement
The current Malrynth developer tooling (`tools/lib.sh`, `tools/doctor`, `tools/build`, `tools/run-qemu`, `tools/test`, `tools/check-reproducible`, `tools/check-panic-path`) is Bash/Linux-specific. It relies on POSIX utilities and Linux conventions:
- Bash-specific syntax (`set -Eeuo pipefail`, `${BASH_SOURCE[0]}`)
- GNU coreutils / Linux commands (`findmnt`, `seq`, `mktemp`, `sha256sum`, `stat -c%s`, `readlink`)
- Linux-specific OVMF paths (`/usr/share/OVMF/OVMF_CODE_4M.fd`, etc.)
- Linux process and signal semantics (`kill -TERM`, `kill -0`, background subshells)

While developers can run inside WSL2 in the short term, Malrynth's long-term goal is a first-class, native Windows development workflow without requiring WSL or third-party POSIX emulation layers.

## 2. Tooling Architecture Options Comparison

| Dimension | Option A: Parallel PowerShell Scripts | Option B: Pure Cross-Platform Python CLI | Option C: Native Rust CLI (`malrynth`) | Option D: Hybrid (Thin Launchers + Shared Core) |
| :--- | :--- | :--- | :--- | :--- |
| **Description** | Duplicate every `.sh` script into a `.ps1` script (`build.ps1`, `doctor.ps1`, etc.) | Implement all developer workflows in Python 3 (`tools/malrynth.py`) | Compile a native Rust binary (`cargo run -p malrynth-cli`) | Thin platform wrappers (`malrynth.ps1`, `./malrynth`) forwarding to Python core |
| **Maintenance Cost** | **High**: Duplicate logic, flags, and regexes in two languages. Inevitable divergence. | **Low**: Single implementation for Windows, Linux, and macOS. | **Medium**: Single implementation, but higher code volume and build setup. | **Low**: Platform launchers are ~10 lines; 100% of logic lives in shared core. |
| **Bootstrap / Chicken-and-Egg** | **Good**: PowerShell is preinstalled on Windows; Bash on Linux. | **Good**: Python 3 is already a dependency (used by `tools/symbolize`). | **Poor**: Cannot run `malrynth doctor` to diagnose missing Rust if the CLI itself requires Rust to build. | **Good**: Runs anywhere Python 3 exists without compiling anything. |
| **Windows Compatibility** | Requires PowerShell 5.1 or 7+ handling. PS5.1 has quirkier syntax and slower startup. | Runs identically on Windows 10/11 with Python 3.8+ (standard library only). | Native `.exe`, but requires compilation step before first use. | Zero prerequisite beyond Python 3. Native feel on PowerShell, CMD, and Bash. |
| **Process / Signal Handling** | Complex process supervision and timeout handling across PowerShell versions. | Clean, cross-platform process trees, polling, timeout, and buffer flushing via `subprocess`. | Robust process handling via Rust standard library / crates. | Robust via Python standard library. |
| **Dependencies** | PowerShell 5.1/7+, Git for Windows. | Python 3 standard library only (no `pip install` required). | Rust toolchain, Cargo, compilation dependencies. | Python 3 + standard OS shell. |
| **Long-term Viability** | Fragile maintenance burden. | Excellent foundation; easily maintained by OS developers. | Excellent for end-user distribution once the toolchain is bootstrapped. | Ideal evolutionary bridge: Python core now; optional standalone binary later. |

## 3. Recommended Architecture: Option D (Hybrid / Python Core)

### Why Python Core?
1. **Existing Dependency**: Malrynth already uses Python for `tools/symbolize` (pure stdlib ELF parser).
2. **Zero External Dependencies**: Python standard library (`subprocess`, `pathlib`, `struct`, `ctypes`, `shutil`, `hashlib`, `time`, `argparse`, `json`) provides full operating-system capabilities without third-party packages.
3. **True Cross-Platform Correctness**: Path normalization, timeout handling, binary parsing, and hashing work identically on Windows NTFS, Linux ext4, and macOS APFS.
4. **Fast and Testable**: Comprehensive unit and integration test suites can be executed with `python -m unittest` without spawning heavyweight shell subprocesses.

### Architecture Structure for the Spike
```text
tools/
├── windows/
│   ├── malrynth.ps1            # Ergonomic PowerShell launcher
│   ├── malrynth.cmd            # Ergonomic CMD launcher
│   ├── malrynth_tooling/       # Core tooling package
│   │   ├── __init__.py
│   │   ├── cli.py              # CLI entry point (doctor, build, run, test)
│   │   ├── config.py           # Paths, targets, compiler flags (single source of truth)
│   │   ├── doctor.py           # Read-only host, toolchain, and workspace diagnostics
│   │   ├── discovery.py        # QEMU, OVMF, Rust toolchain, Git discovery
│   │   ├── build.py            # Cargo invocation, flag synthesis, ESP layout assembly
│   │   ├── runner.py           # Headless QEMU runner, process supervisor, marker detection
│   │   ├── verify.py           # ELF ET_EXEC validator, PE header checker, size reporter
│   │   └── util.py             # Cross-platform SHA-256, filesystem probes, ANSI formatting
```

### Command Surface
```powershell
# Via PowerShell launcher:
.\tools\windows\malrynth.ps1 doctor
.\tools\windows\malrynth.ps1 build [--debug]
.\tools\windows\malrynth.ps1 run [--timeout SECONDS] [--interactive] [--quiet]
.\tools\windows\malrynth.ps1 test [--boots N] [--skip-boot]

# Or direct Python invocation:
python tools/windows/malrynth.py doctor
python tools/windows/malrynth.py build
python tools/windows/malrynth.py run
python tools/windows/malrynth.py test
```

## 4. Hardware & Toolchain Contracts
1. **Compiler Flags Single Source of Truth**:
   - `KERNEL_RUSTFLAGS`: `-C relocation-model=static -C force-frame-pointers=yes --remap-path-prefix=...`
   - `LOADER_RUSTFLAGS`: `-C link-arg=/Brepro -C link-arg=/DEBUG:NONE --remap-path-prefix=...`
   - Remap path prefixes for workspace, cargo home, and rust sysroot to ensure byte reproducibility.
2. **QEMU & OVMF Discovery Hierarchy**:
   - Explicit environment variable override (`MALRYNTH_QEMU`, `MALRYNTH_OVMF_CODE`, `MALRYNTH_OVMF_VARS` / `MALRYNTH_OVMF`)
   - `PATH` lookup (`where.exe` / `Get-Command`)
   - Known standard Windows installation directories (`C:\Program Files\qemu`, Scoop, Chocolatey, etc.)
   - Repository-external developer cache (`%LOCALAPPDATA%\Malrynth\firmware`, etc.)
3. **Strict Read-Only Doctor Guarantee**:
   - `doctor` reports `OK`, `WARNING`, `MISSING`, `UNSUPPORTED`.
   - Never mutates system or downloads packages implicitly.
   - Missing QEMU or OVMF is reported clearly as `MISSING` with remediation advice, not a crash.
4. **Deterministic Boot Supervision**:
   - QEMU run is supervised with monotonic deadlines.
   - Boot success requires the explicit marker `MALRYNTH_M0_BOOT_OK`.
   - Clean QEMU exit without the marker is a hard `FAIL`.
   - Panic marker `MALRYNTH_M0_BOOT_FAIL` or timeout triggers immediate process termination and cleanup.
