# Native Windows M0 validation

Date: 2026-08-23

## Scope and provenance

- Tooling base: `origin/feature/windows-native-tooling-spike` at
  `a016b10dae35e7149bc5bb5aee9078f8e0996ec2`.
- Implementation worktree: `D:\Malrynth-Codex-NativeBoot`.
- Branch: `fix/windows-native-boot-validation`.
- Linux scripts remained the behavioral oracle and were read only.
- No kernel, loader, ABI, root Cargo, CI workflow, architecture, platform, or H0.5 source
  file was modified.

## Installed boot environment

The invoking process had stale PATH: `Get-Command` and `where.exe` found no QEMU. Standard
installation-path discovery found and successfully executed:

- QEMU: `C:\Program Files\qemu\qemu-system-x86_64.exe`
- Version: `11.1.0 (v11.1.0-12130-ge470268ff4)`
- Non-secure CODE: `C:\Program Files\qemu\share\edk2-x86_64-code.fd`, 3,653,632 bytes
- Shared x86 VARS template: `C:\Program Files\qemu\share\edk2-i386-vars.fd`, 540,672 bytes
- Secure alternative present but not selected:
  `C:\Program Files\qemu\share\edk2-x86_64-secure-code.fd`, 3,653,632 bytes

Doctor independently probed the executable and reported:

```text
BUILD READY: YES
BOOT READY: YES
```

No PATH edit, reboot, reinstall, driver, Windows feature, or virtualization setting change
was made.

## Hardening implemented

### Firmware compatibility

Discovery now validates known firmware families and fails closed. QEMU's asymmetric but
valid `edk2-x86_64-code.fd + edk2-i386-vars.fd` pair passes. Cross-family x86/ARM pairs,
missing files, unknown filename families, and Secure Boot CODE fail. Explicit environment
pairs use the same validator. Automatic selection prefers non-secure x86 CODE.

Doctor includes `INVALID FIRMWARE PAIR` when incompatible files are discovered.

### One marker state machine

Headless and interactive presentation share one supervisor and one correctness rule:
`MALRYNTH_M0_BOOT_OK` is the only normal-boot success. Failure marker, clean exit without a
marker, cancellation, and timeout fail. Failure-marker precedence prevents output containing
both markers from passing.

### Run isolation and cleanup

Every invocation creates `%TEMP%\malrynth-qemu-<unique>\` with a private `vars.fd`, serial
log, and stderr log. The installed VARS template is copied, never attached writable. The run
directory is removed after success, marker failure, timeout, cancellation, or supervisor
failure unless explicit diagnostic retention is requested. Tests prove independent copies,
template immutability, distinct run directories, and cleanup.

On Windows, cleanup calls `taskkill.exe /PID <numeric-pid> /T /F` using an argv list and
`shell=False`. A mock parent/child timeout test proves the descendant is gone afterward.

### Runtime requirements and panic validation

The truthful minimum is Python >= 3.10. The launcher fails before importing syntax that an
older interpreter cannot parse; doctor reports `UNSUPPORTED` and `BUILD READY: NO` below the
minimum. Doctor also requires Rust 1.97.1 for build readiness.

`check-panic-path` reproduces the Linux contract: it builds the deliberate panic kernel,
requires the failure marker, checks source/message/backtrace diagnostics and at least two
plausible frames, rejects the normal success marker, invokes the existing host symbolizer,
and restores the normal image in all paths.

## M0 validation evidence

### Build artifacts

| Artifact | Size | Format | SHA-256 |
|---|---:|---|---|
| `BOOTX64.EFI` | 40,960 | PE32+ EFI application | `8cfa6b812de10bb9e60c40b62d50a1cbd4907b7ab9118e6bb888e185b2d6e8d5` |
| `kernel.elf` | 130,688 | ELF64 ET_EXEC | `701c0b282011f3ef219de29ad507c086fd8a5ea5c7e5d7bc9585107082168556` |

Loader structural evidence remained `.rdata` virtual `0x2B4C` (11,084), `.rdata` raw
`0x2C00` (11,264), and PE `FileAlignment=0x200` (512). `/Brepro`, `/DEBUG:NONE`, remapping,
and `CARGO_ENCODED_RUSTFLAGS` remain intact. Neither artifact contains the implementation
worktree's absolute path.

### First real native boot

The hardened Windows CLI observed this relevant sequence:

```text
Malrynth Boot v0.0.1 (UEFI x86_64)
malboot: kernel.elf loaded, 130688 bytes
malboot: exiting boot services
MALRYNTH KERNEL
memory map received (106 regions, 974 MiB usable)
framebuffer discovered (1280x800, stride 1280 px, BGRX8888, 0x0000000080000000)
boot services exited
kernel entered successfully
MALRYNTH_M0_BOOT_OK
```

Observed duration: 2.33 seconds.

### Independent three-boot matrix

| Boot | Result | Duration |
|---:|---|---:|
| 1 | `MALRYNTH_M0_BOOT_OK` | 2.46 s |
| 2 | `MALRYNTH_M0_BOOT_OK` | 2.46 s |
| 3 | `MALRYNTH_M0_BOOT_OK` | 2.31 s |

Each invocation used a new private VARS copy and removed its run directory.

### Panic path

- Deliberate panic reached: PASS
- Source and intentional message: PASS
- Failure marker / no success marker: PASS
- Multiple plausible backtrace frames: PASS
- Host symbolization: PASS
- Process/run-directory cleanup: PASS
- Normal-image restoration: PASS

### Same-host path reproducibility

The same source was built from the implementation worktree and a different-length temporary
source path. Loader and kernel were byte-identical. This proves Windows same-host build-path
reproducibility only; it is not a Linux/Windows cross-host identity claim.

## H0.5 detached validation

Remote `origin/docs/platform-foundation` remained at
`3428b5b491b5b0847e13d6f4135f5cfef819ca40`. A detached temporary worktree was created at
`D:\Malrynth-Codex-H05-Validation`; the hardened tooling was invoked externally from this
branch while repository-root discovery targeted the detached H0.5 worktree. No merge or H0.5
source modification occurred, and the temporary worktree was removed afterward.

Observed Windows results:

- Build and structural verification: PASS
- First native normal boot: PASS, 2.43 s
- Three independent boots: PASS, 2.35 s / 2.44 s / 2.48 s
- Panic path and symbolization: PASS
- Windows same-host path reproducibility: PASS
- Loader: 40,960 bytes, SHA-256 `8cfa6b812de10bb9e60c40b62d50a1cbd4907b7ab9118e6bb888e185b2d6e8d5`
- Kernel: **130,688 bytes**, SHA-256 `701c0b282011f3ef219de29ad507c086fd8a5ea5c7e5d7bc9585107082168556`

The earlier 130,704-byte kernel observation was not reproduced and is not accepted. The
130,688-byte value above is recorded as **OBSERVED WINDOWS VALIDATION**, not as a rewritten
performance baseline.

## Tests and remaining limitations

The Windows tooling suite expanded from 24 to 43 tests, covering firmware pairing, secure
selection, missing files, environment overrides, marker states, interactive semantics,
timeouts, process-tree termination, unique/clean run state, VARS immutability, Python gating,
and panic parser/timeout/missing-diagnostics behavior.

Remaining integration work:

- Linux and Windows build flags remain duplicated. The deferred shared-manifest recommendation
  (`tools/m0-contract.toml`) remains unchanged.
- `ci/windows-native-m0` is still based on the earlier tooling SHA and requires a later
  rebase/update to exercise this hardened branch. No workflow was modified here.
- Interactive GUI presentation has unit-level marker-state coverage; the accepted native
  boot evidence is from the deterministic headless mode.
- This branch is experimental and must receive independent Codex/Claude integration review
  before merge.
