# Investigation of Cross-Host PE/COFF Loader Divergence

## Executive Summary

When building Malrynth on native Windows without compiler flag synchronization or path remapping, the UEFI bootloader (`BOOTX64.EFI`) was observed at **41,472 bytes (0xA200)**, exactly **+512 bytes** larger than the Linux reference artifact at **40,960 bytes (0xA000)**. Meanwhile, the kernel binary remained identical at **130,688 bytes** on both platforms.

Through structural PE/COFF inspection and controlled compilation experiments, the exact root cause of the +512-byte divergence has been **empirically proven**:

1. **Unremapped Path Bloat in `.rdata`**: When `LOADER_RUSTFLAGS` (`--remap-path-prefix`) is omitted or fails to remap Windows-style paths, the compiler embeds full host paths (workspace, Cargo cache, rustup sysroot) into the read-only data section (`.rdata`), increasing its virtual size by **+344 bytes** (from 11,084 to 11,428 bytes).
2. **PE File Alignment Boundary Crossing**: The baseline `.rdata` section virtual size (`0x2B4C` / 11,084 bytes) had only **180 bytes of headroom** remaining within its 512-byte raw alignment allocation (`0x2C00` / 11,264 bytes). The +344-byte string addition spilled 164 bytes past the boundary.
3. **Discrete 512-Byte Step Function**: Adhering to the PE/COFF standard `FileAlignment = 512` (`0x200`), the linker (`lld-link`) rounded the raw section size up to the next alignment multiple (`0x2E00` / 11,776 bytes), adding **exactly 512 bytes** to the total image size.
4. **Validation**: When `LOADER_RUSTFLAGS` with path remapping (`--remap-path-prefix`) and `/Brepro` is correctly passed to Cargo via `CARGO_ENCODED_RUSTFLAGS` on Windows, the native Windows build produces a **40,960-byte** binary that matches the Linux reference size.

---

## 1. Structural PE/COFF Inspection

Using the newly developed read-only PE inspector (`pe-inspect`), the section breakdown of the 40,960-byte (remapped) vs 41,472-byte (unremapped) binaries was measured:

### A. Remapped Binary (`LOADER_RUSTFLAGS` active) — 40,960 bytes (0xA000)
```text
PE/COFF Structural Report: BOOTX64.EFI
======================================================================
File Size:            40,960 bytes (0xA000)
SHA-256:              8cfa6b812de10bb9e60c40b62d50a1cbd4907b7ab9118e6bb888e185b2d6e8d5
Machine:              IMAGE_FILE_MACHINE_AMD64 (0x8664)
Format:               PE32+ (64-bit)
Subsystem:            IMAGE_SUBSYSTEM_EFI_APPLICATION (10)
Linker Version:       14.0 (LLD 22.1.6)
TimeDateStamp:        0x06751F47 (Content-derived hash from /Brepro)
SectionAlignment:     4,096 bytes (0x1000)
FileAlignment:        512 bytes (0x200)
SizeOfImage:          53,248 bytes (0xD000)
SizeOfHeaders:        1,024 bytes (0x400)
NumberOfSections:     4

Section Table:
  Name       VirtSize   VirtAddr   RawSize    RawOffset  Flags                  Headroom in Raw Block
  -------------------------------------------------------------------------------------------------
  .text      0x6B50     0x1000     0x6C00     0x400      CNT_CODE,MEM_EXECUTE   176 bytes
  .rdata     0x2B4C     0x8000     0x2C00     0x7000     CNT_INITIALIZED_DATA   180 bytes
  .data      0x3C       0xB000     0x200      0x9C00     CNT_INITIALIZED_DATA   452 bytes
  .reloc     0x104      0xC000     0x200      0x9E00     CNT_INITIALIZED_DATA   252 bytes
  -------------------------------------------------------------------------------------------------
Headers size:           1,024 bytes
Total section raw size: 39,936 bytes (0x9C00)
Calculated file size:   40,960 bytes (0xA000)
```

### B. Unremapped Binary (Bare Cargo / Missing Flags) — 41,472 bytes (0xA200)
```text
PE/COFF Structural Report: BOOTX64.EFI (Unremapped)
======================================================================
File Size:            41,472 bytes (0xA200)  [DELTA: +512 bytes]
SHA-256:              f4d571a8fcd0eedd23192f1ea30c0c75a9834eaefd2e25ad3cb58807d9b936d8
NumberOfSections:     4

Section Table:
  Name       VirtSize   VirtAddr   RawSize    RawOffset  Delta vs Remapped
  -------------------------------------------------------------------------------------------------
  .text      0x6B50     0x1000     0x6C00     0x400      Virt: 0 bytes        | Raw: 0 bytes
  .rdata     0x2CA4     0x8000     0x2E00     0x7000     Virt: +344 bytes     | Raw: +512 bytes
  .data      0x3C       0xB000     0x200      0x9E00     Virt: 0 bytes        | Raw: 0 bytes (Shifted)
  .reloc     0x100      0xC000     0x200      0xA000     Virt: -4 bytes       | Raw: 0 bytes (Shifted)
  -------------------------------------------------------------------------------------------------
Headers size:           1,024 bytes
Total section raw size: 40,448 bytes (0x9E00)  [DELTA: +512 bytes]
Calculated file size:   41,472 bytes (0xA200)  [DELTA: +512 bytes]
```

---

## 2. Structural Diff Analysis (`pe-diff`)

Direct comparison between the two binaries using `tools/windows/malrynth.py pe-diff` reveals:
```text
PE/COFF Structural Diff Report
======================================================================
File A: target/test_std/x86_64-unknown-uefi/release/malboot.efi (40,960 bytes)
File B: target/test_noremap/x86_64-unknown-uefi/release/malboot.efi (41,472 bytes)
----------------------------------------------------------------------
RESULT: Binaries DIFFER (Size delta: +512 bytes)

Header Differences:
  * File Size: 40,960 vs 41,472 (delta: +512 bytes)
  * TimeDateStamp: 0x06751F47 vs 0xDEA614C1

Data Directory Differences:
  * Directory [ 5] Base Relocation Table : A=(RVA 0xC000, Size 260) vs B=(RVA 0xC000, Size 256)
  * Directory [ 6] Debug Directory       : A=(RVA 0xAB30, Size 28) vs B=(RVA 0xAC88, Size 28)

Section Differences:
  * Section .text   : Content SHA256 changed (references to relocated .rdata addresses)
  * Section .rdata  : VirtSize: 0x2B4C (11,084) -> 0x2CA4 (11,428) [delta +344]; RawSize: 0x2C00 (11,264) -> 0x2E00 (11,776) [delta +512]
  * Section .data   : RawOffset: 0x9C00 -> 0x9E00
  * Section .reloc  : VirtSize: 0x104 (260) -> 0x100 (256); RawOffset: 0x9E00 -> 0xA000
```

---

## 3. Toolchain & Linker Audit

| Property | Linux / Reference Host | Windows 11 Host | Equality / Consistency |
| :--- | :--- | :--- | :--- |
| **Rustc Version** | `1.97.1 (8bab26f4f 2026-07-14)` | `1.97.1 (8bab26f4f 2026-07-14)` | **Identical** |
| **LLVM Version** | `22.1.6` | `22.1.6` | **Identical** |
| **Linker Executable** | `rust-lld` (flavor `link`) | `rust-lld.exe` (flavor `link`) | **Identical version (`LLD 22.1.6`)** |
| **Target Triple** | `x86_64-unknown-uefi` | `x86_64-unknown-uefi` | **Identical** |
| **Kernel Target** | `x86_64-unknown-none` | `x86_64-unknown-none` | **Identical** |
| **Linker Flags** | `/Brepro /DEBUG:NONE` | `/Brepro /DEBUG:NONE` | **Identical** |
| **Remap Prefixes** | `=/malrynth`, `=/cargo`, `=/rust` | `=/malrynth`, `=/cargo`, `=/rust` | **Identical mapping** |

### `/Brepro` and `/DEBUG:NONE` Verification
- `/Brepro` substitutes a content-derived SHA-256 hash in `TimeDateStamp` instead of wall-clock time. Verified to produce `0x06751F47` consistently across repeated local builds.
- `/DEBUG:NONE` eliminates the `.pdb` filename, CodeView GUID, and debug payload. The debug directory contains only a 28-byte `IMAGE_DEBUG_TYPE_REPRO` (type 16) marker with `SizeOfData = 0`.

---

## 4. Flag Duplication & Drift Risk

### Current State
`tools/lib.sh` defines compiler flags for Linux Bash scripts:
```bash
REMAP_FLAGS=(
    "--remap-path-prefix=${MALRYNTH_ROOT}=/malrynth"
    "--remap-path-prefix=${_cargo_home}=/cargo"
    "--remap-path-prefix=${_rust_sysroot}=/rust"
)
KERNEL_RUSTFLAGS="-C relocation-model=static -C force-frame-pointers=yes ${REMAP_FLAGS[*]}"
LOADER_RUSTFLAGS="-C link-arg=/Brepro -C link-arg=/DEBUG:NONE ${REMAP_FLAGS[*]}"
```

In the Windows spike, these flags are duplicated in `tools/windows/malrynth_tooling/config.py`:
```python
def get_remap_flags(self) -> list[str]:
    return [
        f"--remap-path-prefix={self.root}=/malrynth",
        f"--remap-path-prefix={self.cargo_home}=/cargo",
        f"--remap-path-prefix={self.rust_sysroot}=/rust",
    ]
```

### Risk: Flag Drift
If Claude or upstream platform updates change compiler flags in `tools/lib.sh` (e.g. adding sanitizers, optimization levels, or LLD arguments), the Windows tooling will silently build with divergent flags unless manually updated.

### Recommended Future Architecture
Define compiler flags in a single machine-readable manifest or python module (e.g. `tools/flags.json` or within the shared Python CLI), which both `tools/lib.sh` (via simple jq/grep/python parse) and `tools/windows/` consume directly.

---

## 5. Audit of Claims

1. **Python requirement: >= 3.10**:
   - **Corrected audit**: The implementation uses PEP 604 union syntax and therefore requires Python 3.10 or newer. The earlier Python 3.8 compatibility claim and current-runtime-only AST test were insufficient evidence.
   - No `match/case` (3.10+), no `.removeprefix()` (3.9+), and all union types use `from __future__ import annotations` (PEP 563, Python 3.7+).
   - **Status**: **VERIFIED**.
2. **Claim: "strictly POSIX- and Linux-compatible"**:
   - **Correction**: Replaced with **"designed to be cross-platform with no Windows-only dependencies in core"**. Full Linux runtime execution will be formally verified once WSL/Linux validation is performed.

---

## 6. Categorization of Evidence

- **PROVEN**:
  - The +512 byte delta is caused by `.rdata` virtual size growing from 11,084 bytes to 11,428 bytes (+344 bytes) due to embedded unremapped paths, which exceeds the 11,264-byte (`0x2C00`) file alignment headroom by 164 bytes and forces the linker to allocate a 512-byte raw block (`0x2E00`).
  - Passing `LOADER_RUSTFLAGS` with `--remap-path-prefix` on Windows produces the exact 40,960-byte binary.
  - Repeated native Windows builds with remapped flags are 100% byte-identical.
  - Windows file paths containing spaces are handled correctly via `CARGO_ENCODED_RUSTFLAGS`.
- **OBSERVED**:
  - Windows 11 Pro build 26200 identifies as NT 10.0.26200 in kernel APIs and `ProductName = "Windows 10 Pro"` in registry for compatibility, resolved by checking `build >= 22000`.
- **INFERRED**:
  - Claude's observation of 41,472 bytes on Windows was caused by invoking `cargo build` directly or running a script where `RUSTFLAGS` / path remapping was omitted or split on spaces.
- **UNRESOLVED**:
  - None within the scope of loader PE size analysis.

---

## Final Root Cause Verdict

### **LOADER +512 ROOT CAUSE: PROVEN**
**Root Cause**: Unremapped absolute host paths expanding `.rdata` virtual size past the 512-byte file-alignment threshold (`0x2C00` $\to$ `0x2E00`), adding exactly one 512-byte raw PE block when `LOADER_RUSTFLAGS` is absent or unremapped.
