# Malrynth System Overview

**Status:** PROPOSED (architecture). Only the boot path below M0 is implemented.

## What Malrynth is

Malrynth is an independent operating-system family with its own kernel. It is not a Linux
distribution, a Linux fork, or a desktop environment.

```
        firmware (UEFI today)
              |
        Malrynth Boot            <- implemented (M0)
              |
        MALRYNTH KERNEL          <- implemented (M0: entry + diagnostics only)
              |
        Malrynth system services <- M2-M5
              |
        Malrynth runtime         <- M5-M7
              |
        applications
```

Linux appears in Malrynth only in roles that sit *beside or above* the kernel, never beneath
it: as today's development host, as a compatibility target, later as a guest VM, and
possibly as an isolated driver-compatibility domain. **Linux is never Malrynth's production
host kernel.** Any design that would require it is rejected by definition.

## Kernel shape

A **capability-oriented hybrid microkernel**:

- The kernel owns the minimum that cannot be delegated: address spaces, threads, scheduling,
  IPC, and the object/capability system.
- Drivers run in user space by default, confined by the IOMMU where the hardware permits.
- Services (filesystems, network stack, device management) are ordinary user-space programs
  holding capabilities.
- "Hybrid" is an admission, not a hedge: some paths (scheduling-adjacent work, the fast IPC
  path) will live in the kernel for performance, and each such case must be justified in an
  ADR rather than absorbed silently.

## Authority

There is no ambient authority for native applications. A program can do exactly what its
capabilities permit. This is the single most consequential architectural commitment in the
project, because it cannot be retrofitted: an OS that starts with ambient authority never
removes it. See `CAPABILITY-MODEL.md`.

## Products

Desktop, Server, Mobile and Console are **compositions**, not forks. There is one kernel and
one platform; a product selects a shell, a service set, a driver profile, a policy set, a
package set, and an update channel. See `PRODUCT-COMPOSITION.md`. Creating four kernels
would be the fastest available way to destroy the project.

## Architectures

x86-64 first, ARM64 later. No ARM64 code exists. The constraint that matters today is that
architecture-specific code is confined behind `core/kernel/src/arch/`, so ARM64 is an
additive change rather than a rewrite. `arch/mod.rs` enforces this with a `compile_error!`
on unsupported targets rather than a silent stub.

## Current state (M0)

Implemented and verified:

- A UEFI loader that reads, validates and places an ELF64 kernel image.
- A versioned, `#[repr(C)]` handoff ABI with layout assertions under test.
- `ExitBootServices`, transferring the machine from firmware to Malrynth.
- A kernel entry point that validates the handoff, normalises and reports the memory map,
  reports the framebuffer, and emits diagnostics over a 16550 UART.
- A deterministic QEMU boot test asserting an exact success marker, with verified failure
  detection.

Not implemented, and not pretended to be: memory management, paging, interrupts, exceptions,
timers, SMP, user mode, processes, scheduling, syscalls, capabilities, IPC, drivers,
filesystems, networking, graphics, and every application.
