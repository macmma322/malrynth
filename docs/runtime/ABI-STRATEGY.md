# ABI Strategy

**Status:** PROPOSED. No version numbers are frozen.

## Why separate these

"The ABI" is not one thing. Malrynth has at least seven distinct contracts with very different
stability requirements, and conflating them is how a platform ends up unable to change its
kernel because an application depends on a syscall number.

| # | Contract | Between | Stability | Mechanism |
|---|---|---|---|---|
| 1 | **Syscall ABI** | kernel ↔ userspace | versioned, **deliberately small** | register convention, `mly_*` |
| 2 | **Kernel IPC protocol** | processes via kernel | versioned per protocol | channels, memory objects, rings |
| 3 | **Native userspace ABI** | `libmalrynth` ↔ programs | **stable, long-lived** | C ABI |
| 4 | **C ABI** | any language ↔ platform | stable (platform-defined) | SysV AMD64 |
| 5 | **Rust source API** | Rust programs ↔ SDK crates | semver, source-level | Rust crates |
| 6 | **Stable application API** | apps ↔ frameworks | versioned runtimes, side-by-side | protocols + libraries |
| 7 | **Driver protocol ABI** | driver ↔ device manager | versioned | IPC protocols |
| 8 | **Compatibility ABI** | foreign binaries | fixed externally (Linux/Win32) | personality layers |

## Core decisions

**The syscall ABI is not the platform contract.** Applications bind to `libmalrynth` and the
frameworks, not to syscall numbers. This is what lets the kernel evolve — and it is the single
most important rule here.

**Long-term binary stability uses the C ABI.** Rust deliberately has no stable ABI, and
depending on `rustc`'s current layout would tie binary compatibility to a compiler version.
Public boundaries are therefore `extern "C"` with `#[repr(C)]` types. Rust developers see
idiomatic Rust crates *wrapping* that boundary, so the ergonomics cost is contained to the
wrapper rather than paid by every caller.

**Rust-to-Rust internal boundaries may use Rust types**, because they are recompiled together.
The C ABI is required only where a binary boundary must survive a compiler upgrade.

## Versioning philosophy

- **Additive by default.** New functions and new protocol messages; never silent semantic changes.
- **Explicit version negotiation** for IPC protocols; a peer that does not understand a version says so.
- **Side-by-side runtimes.** An application targets `Malrynth ABI 1`, `Runtime UI 5`, and the
  system keeps compatible runtimes installed. This is what avoids classic dependency hell
  without statically bundling everything.
- **Deprecation windows**, never silent removal. Once an interface is LOCKED it carries a
  compatibility commitment (Constitution §18).
- **Nothing is stable before M3.** Everything today is EXPERIMENTAL and may change without
  notice — which is precisely why nothing is being numbered yet.

## What must not happen

| Anti-pattern | Consequence |
|---|---|
| Applications calling syscalls directly | Kernel can never change |
| Stabilising Rust's compiler ABI | Binary compatibility tied to a compiler version |
| A single monolithic "system library" | Everything becomes one version, so nothing can move |
| Version numbers assigned before M3 | Stability implied where none exists |
| Compatibility layers with private kernel interfaces | Two security models, one kernel |
