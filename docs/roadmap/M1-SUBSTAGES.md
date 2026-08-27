# M1 Sub-stages (M1A–M1F)

**Status:** ACCEPTED (2026-08-27) as a decomposition. **This document adds no scope.** Every
item below is already in [M1](M1.md); this splits that milestone into six dependency-ordered
sub-stages with their own boundaries and exit gates, so M1 can be started, reviewed and
stopped in pieces rather than as one indivisible block.

If an item is not in [M1](M1.md), it does not belong here. Anything discovered mid-M1 that is
not in M1 is a scope change and goes through the roadmap, not through this file.

## Why decompose at all

M1 is the largest milestone attempted so far: memory, paging, exceptions, interrupts, time and
SMP. As a single unit it has no reviewable intermediate state — either all of it works or none
of it is demonstrable. Six sub-stages give six points at which the kernel still boots, the
existing M0 tests still pass, and the work can be judged.

## Order and dependencies

| | Sub-stage | Depends on | One-line objective |
|---|---|---|---|
| **M1A** | Physical memory | M0 handoff | Own the physical frame supply |
| **M1B** | Virtual memory | M1A | Own the address space; run from the higher half |
| **M1C** | Exceptions | M1B | Fault deliberately and survive it with a diagnostic |
| **M1D** | Interrupts and time | M1C (+ M1E, see below) | A monotonic clock and delivered interrupts |
| **M1E** | ACPI subset | M1C | Enumerate CPUs and interrupt topology from the MADT |
| **M1F** | SMP | M1D, M1E | Every reported CPU reaches an idle loop |

### The one ordering question this decomposition surfaces

**M1D and M1E are not cleanly separable in the stated order.** The local APIC can be enabled
without ACPI, but the **I/O APIC** cannot be programmed correctly without the MADT: its base
address, the global system interrupt base and the interrupt source overrides all come from
there. Taking A–F literally would have M1D route interrupts using information M1E has not yet
produced.

**Recommended resolution:** M1D delivers the local APIC, TSC calibration, the monotonic clock
and the periodic timer — none of which need ACPI — and the **I/O APIC routing portion of M1D
runs after M1E**. The A–F labels are otherwise retained. The alternative, swapping M1D and M1E
outright, works equally well and is a matter of preference.

This is recorded rather than silently resolved because it is a real ordering constraint, and it
is a decision for M1D planning, not for this document.

---

## M1A — Physical memory

**Objective.** Take ownership of the physical frame supply handed over by M0.

**In scope (from M1).** A physical frame allocator over the M0 memory regions; accounting for
the kernel image and boot info block so the allocator cannot hand out memory the kernel is
executing from or reading.

**Constrained by [ADR-0006](../adr/ADR-0006-physical-direct-map-scope.md).** The representation
must distinguish allocatable RAM, RAM-backed but non-allocatable memory, and physical space not
known to be RAM. It must not assume a direct map exists or that `phys → virt` is a constant
offset. This constrains the *shape* of M1A; it adds no work to it.

**Not in this sub-stage.** Page tables, virtual addresses, the higher half, the direct map, the
kernel heap, `alloc`.

**Exit gate.**
- Frames are allocated and released without corrupting the map, verified against the M0 region
  list.
- The allocator refuses to hand out the kernel image, the boot info block, or any region not
  classified as usable RAM.
- Host unit tests cover allocation, exhaustion, release and double-release.
- An incomplete or absent memory map is rejected before the allocator is constructed, never
  treated as an empty one.
- M0 still boots; `MALRYNTH_M0_BOOT_OK` is unchanged.

## M1B — Virtual memory

**Objective.** Own the address space instead of inheriting UEFI's.

**In scope (from M1).** Malrynth-owned 4-level page tables; the move to the higher half
(`0xFFFF_FFFF_8000_0000`), retiring `KERNEL_PHYS_BASE`; W^X mapping driven by the existing
per-segment `PT_LOAD` permissions; the kernel virtual address space layout including the
physical-memory direct map; the kernel heap and `alloc` support.

**Governed by [ADR-0006](../adr/ADR-0006-physical-direct-map-scope.md).** The direct map covers
classified RAM only. Device and unknown physical space are not mapped here.

**Not in this sub-stage.** Exceptions, interrupts, timers, SMP, user-space address spaces.

**Exit gate.**
- The kernel executes from the higher half under page tables it built.
- No writable-executable mapping exists anywhere; W^X is asserted, not assumed.
- The direct map covers exactly the classified-RAM set and nothing else, and that is checked
  rather than asserted in a comment.
- `alloc` works; the heap survives an allocation/free stress test.
- `KERNEL_PHYS_BASE` is gone from the kernel, and the ABI change is versioned.

## M1C — Exceptions

**Objective.** Fault on purpose and survive it with a usable diagnostic.

**In scope (from M1).** GDT, IDT, TSS; exception handlers with diagnostic dumps; a dedicated
double-fault stack (IST).

**Not in this sub-stage.** Hardware interrupts, the APIC, timers, ACPI, SMP.

**Exit gate.**
- A deliberately triggered page fault produces a correct diagnostic dump — faulting address,
  error code, register state, and the existing validated frame-pointer backtrace — rather than
  a triple fault.
- A deliberately triggered double fault is handled on the IST stack and reports, rather than
  triple-faulting.
- Fault injection exists per exception class and runs in the test suite.
- The panic path and its symbolisation continue to work unchanged.

## M1D — Interrupts and time

**Objective.** A monotonic clock, and interrupts that arrive.

**In scope (from M1).** Local APIC; I/O APIC and interrupt routing; TSC calibration and a
monotonic clock; a periodic timer; boot-time instrumentation.

**Ordering.** The I/O APIC portion depends on M1E's MADT parsing — see above.

**Not in this sub-stage.** SMP bring-up, per-CPU data, drivers beyond the timer and interrupt
controller.

**Exit gate.**
- The periodic timer fires and is counted.
- The monotonic clock is monotonic, and its drift under QEMU is measured and recorded.
- Spurious and unhandled vectors are reported, not silently swallowed.
- Boot time is measured with an in-kernel timestamp, establishing the first real boot-time
  budget.

## M1E — ACPI subset

**Objective.** Learn the machine's CPU and interrupt topology from firmware, and nothing more.

**In scope (from M1).** ACPI table discovery from the RSDP captured in M0, **only as far as the
MADT** for CPU and APIC enumeration.

**Not in this sub-stage.** Any other ACPI table, AML, the ACPI interpreter, power management,
PCIe enumeration. Those are M4. This boundary is the one most likely to erode; M1 states it
explicitly and so does this document.

**Exit gate.**
- The RSDP captured at M0 is validated, and the table checksums are verified rather than
  trusted.
- The MADT yields the local APIC IDs, the I/O APIC base and the interrupt source overrides.
- A malformed or absent table is reported and refused, not worked around.
- The set of enumerated CPUs matches what QEMU was told to provide.

## M1F — SMP

**Objective.** Every CPU the firmware reports reaches an idle loop.

**In scope (from M1).** SMP bring-up; per-CPU data; replacing `static mut COM1` with a proper
lock.

**Not in this sub-stage.** Scheduling, threads, load balancing, user mode — all M2.

**Exit gate.**
- All CPUs reported by the MADT reach an idle loop.
- A multi-CPU rendezvous test passes.
- Console output from several CPUs is not interleaved into garbage; the lock is real.
- No `static mut` remains on the console path.
- `MALRYNTH_M1_BOOT_OK` is emitted after bring-up.

---

## What closes M1

M1 is complete when every sub-stage above has passed its exit gate **and** M1's own exit
criteria, tests, performance gates, security gates and documentation requirements in
[M1](M1.md) are met. Passing all six sub-stage gates is necessary, not sufficient: the
milestone-level security gates (W^X, kernel stack guard pages, the updated unsafe inventory)
and the required documentation (`MEMORY-MODEL.md`, the address-space ADR, the threat-model
revision) are checked against M1, not against any one sub-stage.
