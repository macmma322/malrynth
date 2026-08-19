# Dependency Graph

**Status:** ACCEPTED.

## The question this answers

> **What must exist before X can exist?**

Roadmap order is not a preference. It is dictated by these chains, and most scope disputes
dissolve once the chain is written down: a feature is not "deprioritised", it is *blocked*.

## Primary chain — the platform spine

```
firmware (UEFI)
   └─> malboot ─────────────────────────────── M0 ✅
        └─> kernel entry + diagnostics ─────── M0 ✅
             └─> physical memory ───────────── M1
                  └─> paging / address spaces ─ M1
                       ├─> kernel heap ──────── M1
                       └─> exceptions ───────── M1
                            └─> interrupts ──── M1
                                 └─> time ───── M1
                                      └─> SMP ─ M1
                                           └─> threads ──────── M2
                                                └─> processes ─ M2
                                                     ├─> scheduler ─ M2
                                                     └─> syscalls ── M2
                                                          └─> kernel objects ─ M3
                                                               └─> capabilities ─ M3
                                                                    └─> IPC ───── M3
                                                                         └─> system services ─ M4+
```

**Nothing above M3 can be built honestly before capabilities exist**, because every service
written before them would be written against ambient authority and rewritten afterwards.

## Hardware chain

```
kernel (M1) ──> ACPI ──> PCIe ──> IOMMU ──> device manager ──> driver framework
                                    │                              ├─> NVMe ──> block ──> VFS
                                    │                              ├─> xHCI ──> HID ──> input
                                    │                              └─> Ethernet ──> netstack
                                    └── (IOMMU is the precondition for the ENTIRE
                                         user-space driver model; without it drivers
                                         are trusted, and the security argument fails)
```

## Runtime chain — the one that gates all applications

```
processes + IPC + capabilities (M3)
   └─> VFS + program loader (M5)
        └─> executable format + dynamic loader (M5)
             └─> libc  ◄── UNSOLVED, and it blocks everything downstream
                  ├─> POSIX facade ──> Unix software ports
                  ├─> Rust std port ──> Rust ecosystem
                  └─> native runtime API
                       └─> frameworks (UI, media, storage clients)
                            └─> application framework
                                 └─> SDK ──> first-party apps ──> third-party apps
```

**The libc decision is the highest-leverage unresolved item in the project.** It gates POSIX,
Rust `std`, the SDK, every application, and all of Wine/Proton. See
[`LIBC-STRATEGY.md`](../runtime/LIBC-STRATEGY.md) and
[`OPEN-QUESTIONS.md`](OPEN-QUESTIONS.md) Q1.

## Graphics chain

```
IOMMU + VM (M4)
   └─> kernel GPU mediation
        └─> GPU system driver  ◄── highest technical risk; may need vendor cooperation
             └─> Vulkan loader + ICD
                  ├─> compositor ──> native display protocol
                  │                    ├─> UI toolkit ──> Files, Settings, all GUI apps
                  │                    └─> Wayland compat ──> Linux GUI apps
                  └─> games / DXVK / vkd3d
```

Text and accessibility join at the toolkit:

```
Unicode data + shaping + rasterisation ──┐
                                          ├─> UI toolkit
accessibility tree + AT bus ─────────────┘
```

## Compatibility chain — why Windows gaming is so far out

```
processes + threads + futex-class primitives (M2-M3)
   └─> POSIX facade (M5)
        └─> Linux personality
             └─> Wine
                  └─> DXVK / vkd3d-proton
                       └─> Vulkan  ◄── ALSO required, from the graphics chain
                            └─> Windows gaming
```

Windows gaming sits at the confluence of **two** long chains. It cannot precede either.
Anti-cheat additionally requires vendor cooperation, which is not an engineering dependency at
all — see [`GAMING-PLATFORM.md`](../gaming/GAMING-PLATFORM.md).

## Media and Broadcast chain

```
GPU driver ──> Vulkan ──> compositor ──> capture authority ─┐
audio driver ──> audio device service ──> audio graph ──────┤
codecs (reused) ──> media graph ───────────────────────────┼─> Broadcast
storage ──> segmented recording ───────────────────────────┘
```

Broadcast is a *consumer* of platform capabilities, not a builder of them. If it needs plumbing
nothing else has, the platform is missing something — that is the design test.

## Security chain

```
verified boot ──> package signatures ──> capability enforcement ──> process isolation
                                              │
                                              ├─> SecurityEventStream ──> behaviour engine
                                              ├─> snapshots ──> ransomware containment
                                              └─> recovery
```

`SecurityEventStream` must be designed while the kernel objects are designed (M3), not
retrofitted — retrofitted observability becomes undocumented hooks.

## Cloud chain

```
netstack + TLS ──> account ──┬─> Store entitlements
                             ├─> Sync (E2E) ──> device restore
                             └─> Organizations ──> MDM ──> EDR
crypto + Vault ──────────────┘
```

Every one of these is optional by constitution: the device must be fully usable with none of
them.

## Cross-cutting: what M1–M4 must not foreclose

The reason H0.5 precedes M1. Each row is a decision made *early* that is expensive to reverse:

| Early decision | What it would foreclose | Guard |
|---|---|---|
| Single global address space | Per-process isolation, capabilities | `AddressSpace` is an object (ADR-0004) |
| Ambient-authority syscalls in M2 | The entire capability model | M2 syscalls declared explicitly temporary |
| Kernel-resident drivers "for now" | User-space driver model, IOMMU story | [`DRIVER-MODEL.md`](DRIVER-MODEL.md) requires an ADR per exception |
| Virtualization fully in kernel | Small TCB; user-space VMM | [`VIRTUALIZATION-ARCHITECTURE.md`](../virtualization/VIRTUALIZATION-ARCHITECTURE.md) |
| No security event design | EDR becomes undocumented hooks | `SecurityEventStream` designed at M3 |
| Kernel parses filesystems | Huge ring-0 attack surface | [`KERNEL-BOUNDARY.md`](KERNEL-BOUNDARY.md) |
| No 32-bit consideration in the ABI | Much Windows software | [`ABI-STRATEGY.md`](../runtime/ABI-STRATEGY.md) |
| Compositor without capture as a capability | Broadcast, screen-share privacy | [`GRAPHICS-STACK.md`](../graphics/GRAPHICS-STACK.md) |
