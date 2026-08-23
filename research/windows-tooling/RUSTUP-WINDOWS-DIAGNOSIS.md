# Windows Rustup Toolchain Diagnosis

## Context
Malrynth pins its toolchain via `rust-toolchain.toml` to:
- Channel: `1.97.1`
- Profile: `minimal`
- Components: `["rustfmt", "clippy"]`
- Targets: `["x86_64-unknown-uefi", "x86_64-unknown-none"]`

During initial inspection on Windows 11 Pro (build 26200), invoking `rustc` / `cargo` / `rustup` produced:
```text
info: recovering from a partially installed toolchain
info: removing previous version of component rustc
...
error: could not rename 'component' file from 'C:\Users\nikol\.rustup\tmp\ljd32inp9k7fyxzz_dir\bk' to 'C:\Users\nikol\.rustup\toolchains\1.97.1-x86_64-pc-windows-msvc\lib\rustlib\x86_64-unknown-none': The directory is not empty. (os error 145)
```

## Root Cause Analysis
1. **Windows Atomic Rename Semantics on Non-Empty Directories**:
   On Windows NTFS, moving/renaming a directory onto an existing destination directory fails with Win32 error `ERROR_DIR_NOT_EMPTY` (`os error 145`). Rustup extracts component archives into temporary directories in `%USERPROFILE%\.rustup\tmp\` and performs atomic directory renames (`MoveFileExW` / `rename`). If an earlier installation was interrupted, or if target subdirectories (`lib\rustlib\x86_64-unknown-none`) already existed from a partial install or were locked by an active process / indexing service / antivirus scanner, rustup's rollback/recovery mechanism encounters `os error 145`.

2. **Global Toolchain State vs. Clean State**:
   - The global `C:\Users\nikol\.rustup` had stale/partial artifacts from a previous interrupted update.
   - The global rustup binaries (`C:\Users\nikol\.cargo\bin\rustup.exe`, `cargo.exe`, `rustc.exe`) themselves are functional (rustup 1.29.0).
   - No conflicting third-party package-manager rustc/cargo binaries were on `PATH` (only `.cargo\bin`).

## Verification in Isolated Environment
To verify whether official Rust 1.97.1 and Malrynth's targets can be cleanly installed on Windows without global mutations, an isolated environment was provisioned:
- `RUSTUP_HOME = %LOCALAPPDATA%\Malrynth\windows-tooling-spike\rustup`
- `CARGO_HOME = %LOCALAPPDATA%\Malrynth\windows-tooling-spike\cargo`

Installation command executed:
```powershell
rustup toolchain install 1.97.1 --profile minimal --component rustfmt,clippy --target x86_64-unknown-uefi,x86_64-unknown-none
```

### Result:
- **Clean Download & Extraction**: All 7 components (`rustc`, `cargo`, `rust-std`, `rustfmt`, `clippy`, `rust-std-x86_64-unknown-uefi`, `rust-std-x86_64-unknown-none`) downloaded and unpacked without any conflict or error.
- **Compiler Execution**: `rustc 1.97.1 (8bab26f4f 2026-07-14)` ran cleanly.
- **Targets Verified**:
  - `x86_64-pc-windows-msvc`
  - `x86_64-unknown-none`
  - `x86_64-unknown-uefi`

## Recommendations for Developer Tooling & Doctor
1. **Read-Only Doctor Behavior**:
   `doctor` must not mutate the filesystem or trigger background package downloads. It should run `rustup show active-toolchain` or `rustc --version` and query installed targets via `rustup target list --installed`. If rustup returns a non-zero exit code or error output, `doctor` should report `MISSING` / `WARNING` with clear remediation instructions rather than failing unexpectedly.
2. **Isolation for Testing/CI**:
   Windows testing workflows can safely set `RUSTUP_HOME` / `CARGO_HOME` when running in disposable environments.
3. **No Destructive Global Actions**:
   Do not delete `%USERPROFILE%\.rustup` or execute aggressive cleanups without explicit user interaction.
