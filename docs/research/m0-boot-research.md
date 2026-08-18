# M0 Boot Research

**Status:** LOCKED (input to [ADR-0003](../adr/ADR-0003-toolchain-and-targets.md))
**Date:** 2026-08-19

## Sources consulted

- **[P]** UEFI Specification — <https://uefi.org/specifications>
- **[P]** Rust `x86_64-unknown-uefi` target docs — <https://doc.rust-lang.org/rustc/platform-support/unknown-uefi.html>
- **[P]** Rust `x86_64-unknown-none` target docs — <https://doc.rust-lang.org/rustc/platform-support/x86_64-unknown-none.html>
- **[P]** The `rustc` book, platform support tiers — <https://doc.rust-lang.org/rustc/platform-support.html>
- **[P]** `uefi` crate (uefi-rs) 0.39.0 — <https://docs.rs/uefi> / <https://github.com/rust-osdev/uefi-rs>
- **[P]** QEMU documentation, `q35` machine and firmware — <https://www.qemu.org/docs/master/system/i386/pc.html>
- **[P]** TianoCore / EDK II OVMF — <https://github.com/tianocore/tianocore.github.io/wiki/OVMF>
- **[P]** System V AMD64 ABI — <https://gitlab.com/x86-psABIs/x86-64-ABI>
- **[P]** ELF-64 Object File Format specification
- **[E]** Local verification: `rustup target list`, `qemu-system-x86_64 --version`, OVMF package contents

## Key findings

### 1. Both required targets are Tier 2 with precompiled `core`

`x86_64-unknown-uefi` and `x86_64-unknown-none` both ship `rust-std` via rustup. This is the
single most consequential finding: it removes the need for `-Z build-std` and therefore the
need for **nightly**. The conventional "Rust kernel needs nightly + custom target JSON" recipe
is not required for M0.

`x86_64-unknown-none` additionally disables MMX/SSE, enables soft-float and disables the red
zone — exactly the constraints kernel code requires, which would otherwise have to be
specified by hand in a custom target.

### 2. `rust-lld` is bundled; no system linker is needed

The toolchain ships `rust-lld` (plus `ld.lld`, `lld-link`) and uses it by default for both
targets. `clang`, `lld`, `cmake` and `ninja` — none installed on this host — are unnecessary.
This reduces the bootstrap to "install rustup" and removes a class of host-configuration drift.

### 3. Rust defaults `x86_64-unknown-none` to PIE — a real hazard

Verified empirically: the kernel initially linked as `ET_DYN` (`e_type=3`). A loader that
does not process `R_X86_64_RELATIVE` relocations would place such an image and jump into
unresolved code. Two options: teach the loader to relocate, or build non-PIE.

Chosen: `-C relocation-model=static -C link-arg=--no-pie`, producing `ET_EXEC`, **and the
loader verifies `e_type` and the link address**. The verification is the important part —
without it the failure is silent, which is the worst possible property for a boot path.

### 4. Loader strategy

Four options were considered against the brief's guidance that a standards binding is safer
than hand-rolled firmware parsing:

| Option | Verdict |
|---|---|
| Existing full loader crate (e.g. `bootloader`) | Rejected — imposes its own handoff ABI and boot policy, which is exactly the layer Malrynth must own. |
| **Custom `malboot` using the `uefi` crate** | **Chosen.** Malrynth owns the handoff and boot policy; firmware structure definitions come from a maintained standards binding. |
| Hand-written UEFI FFI | Rejected — a wrong field offset corrupts memory during boot with no diagnostic. Not worth it for code that stops at `ExitBootServices`. |
| Defer the loader entirely | Rejected — M0's entire purpose is proving the loader/kernel boundary. |

The dependency is confined to the loader, which stops executing at `ExitBootServices` and is
therefore not part of the runtime TCB. The kernel keeps zero dependencies.

### 5. Ordering constraint around `ExitBootServices`

After `ExitBootServices` there is no allocator, no console, and no protocol. Every allocation
— the `BootInfo` block and the memory-region array — must happen **before** the call and only
be *filled in* afterwards. The memory map is only final at that moment, so the loader
allocates a fixed-capacity region array in advance and reports at the cap rather than
truncating the kernel's view of physical memory silently.

`EfiLoaderData` survives the transition and is the correct memory type for handoff data.

### 6. Boot medium without root or `mtools`

`mtools` is absent on this host and installing packages was out of scope. QEMU's virtual FAT
(`-drive format=raw,file=fat:rw:<dir>`) presents a directory as a FAT volume, requiring
neither root nor loop mounts. Verified working with OVMF, which boots
`\EFI\BOOT\BOOTX64.EFI` — the UEFI-specified removable-media default path, so no NVRAM boot
entry is needed.

Gap: no distributable `.img`. Recorded in `docs/roadmap/M0.md`; `tools/doctor` reports
`mtools` as optional.

### 7. OVMF must use split CODE/VARS with a per-run pristine variable store

The 4 MiB split build (`OVMF_CODE_4M.fd` + `OVMF_VARS_4M.fd`) is what current OVMF ships.
`tools/run-qemu` copies the variable store fresh on every run: a carried-over store makes boot
order depend on previous runs, which would make a boot test non-deterministic in exactly the
way a boot test must not be.

### 8. Serial output and test observation

QEMU's `-serial file:` captures COM1 deterministically. Piping `-serial stdio` through a
pipeline was found to buffer and hide output, so the harness writes to a file and polls it.

The kernel drives a 16550 UART at `0x3F8` directly rather than relying on the firmware
console, so diagnostics do not depend on firmware routing — and continue to work after
`ExitBootServices`, when no firmware console exists.

**The kernel contains no QEMU-specific exit device.** A debug-exit port would put test-only
behaviour into the kernel; instead the harness watches for the marker and terminates QEMU. The
kernel halts, which is what a real kernel does at the end of M0.

## Decisions taken into ADR-0003

1. Pin exact stable Rust 1.97.1; no nightly.
2. Built-in targets now; custom target JSON when the kernel needs an ABI they cannot express
   (expected at M1 for `code-model = "kernel"`).
3. Non-PIE `ET_EXEC` kernel, with loader-side verification.
4. `uefi` crate in the loader only; kernel keeps zero dependencies.
5. QEMU virtual FAT for the test loop; real image generation deferred and documented.
