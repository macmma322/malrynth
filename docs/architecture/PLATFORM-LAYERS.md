# Platform Layers

**Status:** ACCEPTED as architectural direction. No individual API is frozen.
**Supersedes in scope:** the layering sketch in [`SYSTEM-OVERVIEW.md`](SYSTEM-OVERVIEW.md).

## Why this document is load-bearing

A layer diagram is decoration unless every boundary states what changes when you cross it.
The four properties that matter are **privilege**, **trust**, **mechanism**, and **what
happens when the thing on the far side dies**. Those are what stop a subsystem from drifting
into the kernel one reasonable exception at a time.

## The stack

```
  ┌──────────────────────────────────────────────────────────────┐
  │ L9  PRODUCTS      Desktop · Server · Mobile · Console        │  compositions, not forks
  ├──────────────────────────────────────────────────────────────┤
  │ L8  APPLICATIONS  first-party · third-party · compatibility  │  unprivileged
  ├──────────────────────────────────────────────────────────────┤
  │ L7  COMPATIBILITY Linux · Windows · Android · Web · VM       │  unprivileged, capability-holding
  ├──────────────────────────────────────────────────────────────┤
  │ L6  FRAMEWORKS    UI · graphics · text · media · storage     │  unprivileged libraries + services
  │                   notifications · clipboard · a11y · l10n    │
  ├──────────────────────────────────────────────────────────────┤
  │ L5  RUNTIME       native API · libc/POSIX facade · Rust std  │  in-process, unprivileged
  │                   dynamic loader · startup                    │
  ├──────────────────────────────────────────────────────────────┤
  │ L4  DRIVER DOMAINS storage · net · USB · GPU · audio · camera │  unprivileged + device capabilities
  ├──────────────────────────────────────────────────────────────┤
  │ L3  SYSTEM SERVICES component mgr · device mgr · fs · net     │  unprivileged but highly trusted
  │                     security · package/update · log · policy  │
  ├──────────────────────────────────────────────────────────────┤
  │ L2  KERNEL        sched · memory · IPC · objects · caps       │  ring 0 — the TCB
  │                   interrupt/time · IOMMU · virt primitives    │
  ├──────────────────────────────────────────────────────────────┤
  │ L1  MALRYNTH BOOT malboot: load, verify, hand off             │  ring 0, transient
  ├──────────────────────────────────────────────────────────────┤
  │ L0  FIRMWARE      UEFI · ACPI · TPM                           │  outside Malrynth's TCB
  └──────────────────────────────────────────────────────────────┘
```

**Linux never appears in this stack below L7.** That is the invariant the whole project rests
on, and it is why compatibility is a layer *above* the runtime rather than a substrate.

## Boundary contracts

| Boundary | Privilege change | Trust | Mechanism | Stability | Failure isolation |
|---|---|---|---|---|---|
| **L0 → L1** | firmware → ring 0 | firmware trusted by necessity; unverifiable | UEFI protocols | UEFI spec (external) | none — firmware failure is fatal |
| **L1 → L2** | ring 0 → ring 0 | loader in TCB while running, then gone | `BootInfo` handoff struct | **versioned, validated** (`malrynth-abi`) | none — mismatch halts with a diagnostic |
| **L2 → L3** | ring 0 → ring 3 | services trusted, not privileged | syscalls + handles | syscall ABI: small, versioned | service crash is contained and restartable |
| **L3 → L4** | ring 3 → ring 3 | drivers **untrusted**, capability-confined | IPC + device capabilities | driver protocol ABI | driver crash contained; device reset + restart |
| **L4 → hardware** | — | device untrusted | MMIO/IRQ/DMA capabilities | hardware spec | **IOMMU** — or explicitly no protection |
| **L3 → L5** | ring 3 → ring 3 | runtime trusted only by its own process | IPC via runtime stubs | **stable C ABI** | per-process |
| **L5 → L6** | none | frameworks are process-local libraries + remote services | in-process calls + IPC | versioned framework runtimes | per-process; service crash contained |
| **L6 → L7** | none | compatibility layers untrusted | framework APIs + IPC | compat ABI (external shape) | per-process |
| **L7 → L8** | none | apps untrusted | framework APIs | **stable application API** | per-process |
| **L8 → L9** | none | product = composition | manifests | product manifest | n/a — build-time |

## The three rules this layering exists to enforce

**1. Authority decreases upward, never increases.** No layer obtains authority its caller did
not hold. A framework cannot grant a capability an application was not given; a compatibility
layer cannot manufacture ambient authority for a Linux binary.

**2. Trust is not privilege.** L3 system services are *highly trusted* and *entirely
unprivileged*. They run in ring 3 holding capabilities. This is the distinction that makes a
microkernel worth its IPC cost, and it is the one most easily eroded by "just this once".

**3. Crossing a boundary means validating.** Every arrow is a place where the receiver treats
input as hostile. This already holds at L1→L2 (the loader validates the ELF; the kernel
validates the handoff) and must hold at every boundary added later.

## Where each layer's specification lives

| Layer | Document |
|---|---|
| L1–L2 | [`KERNEL-BOUNDARY.md`](KERNEL-BOUNDARY.md), [ADR-0004](../adr/ADR-0004-kernel-object-model.md), [`IPC-MODEL.md`](IPC-MODEL.md) |
| L3 | [`PLATFORM-CAPABILITY-MAP.md`](PLATFORM-CAPABILITY-MAP.md) |
| L4 | [`DRIVER-MODEL.md`](DRIVER-MODEL.md), [`DDK-ARCHITECTURE.md`](../sdk/DDK-ARCHITECTURE.md) |
| L5 | [`ABI-STRATEGY.md`](../runtime/ABI-STRATEGY.md), [`LIBC-STRATEGY.md`](../runtime/LIBC-STRATEGY.md), [`EXECUTABLE-MODEL.md`](../runtime/EXECUTABLE-MODEL.md) |
| L6 | [`UI-PLATFORM.md`](../ui/UI-PLATFORM.md), [`GRAPHICS-STACK.md`](../graphics/GRAPHICS-STACK.md), [`MEDIA-FRAMEWORK.md`](../media/MEDIA-FRAMEWORK.md), [`STORAGE-ARCHITECTURE.md`](../storage/STORAGE-ARCHITECTURE.md) |
| L7 | [`COMPATIBILITY-ARCHITECTURE.md`](../compatibility/COMPATIBILITY-ARCHITECTURE.md) |
| L8 | [`NATIVE-APPLICATION-MODEL.md`](../apps/NATIVE-APPLICATION-MODEL.md), [`APPLICATION-MAP.md`](../apps/APPLICATION-MAP.md) |
| L9 | [`PRODUCT-COMPOSITION.md`](../products/PRODUCT-COMPOSITION.md) |

## Implementation status

Only **L0–L2 exist**, and L2 contains an entry point and diagnostics, nothing more. L3–L9 are
specification. `PLATFORM-CAPABILITY-MAP.md` records per-subsystem status so this document is
never mistaken for a description of a working system.
