# M1A Physical Memory Ownership

**Status:** internal stage implementation. `MALRYNTH_M1A_MEMORY_OK` is an M1A validation
marker, not the final `MALRYNTH_M1_BOOT_OK` milestone marker.

## Handoff and trust transition

The current boot path is:

```text
UEFI GetMemoryMap
  -> malboot checked bounded normalization (maximum 256 complete descriptors)
  -> malrynth_abi::BootInfo + MemoryRegion[]
  -> kernel pointer/count/arithmetic validation
  -> page-aware canonical ownership sweep
  -> explicit kernel/framebuffer/null-page reservations
  -> allocator-metadata selection and reservation
  -> bitmap initialization and bounded live self-check
```

The ABI records are partially trusted loader input. The kernel recomputes every byte end,
rounds usable memory inward, rounds reservations outward, applies reserved-wins precedence,
sorts and merges the result, and never trusts `BootInfo::usable_bytes` for allocator state.
Only the resulting sorted, non-overlapping `CanonicalRegion` slice is trusted kernel state.

## Ownership and allocator

M1A distinguishes usable RAM, generic reserved/unknown space, UEFI runtime, ACPI reclaimable,
kernel image, boot handoff, framebuffer, and allocator metadata. Gaps are reserved. Frame zero
is explicitly reserved. The allocator owns only canonical usable RAM; high MMIO does not
inflate its bitmap domain or RAM accounting.

The allocator uses two bitmaps: immutable availability and mutable allocation state. This
supports deterministic lowest-frame allocation and distinguishes reserved frees, invalid
frees, and double frees. Its accounting invariant is:

```text
allocatable = allocated + free
```

Initialization is single-threaded. The allocator object encapsulates all mutable bitmap
state; M1F can place a coarse lock around this boundary before SMP allocation begins.
Physical frame ownership is independent of any virtual address space, leaving mapping policy
to M1B and later `AddressSpace`/memory-object work.

## Metadata bootstrap and structural cost

Fixed `.bss` scratch arrays canonicalize the raw map without allocation. M1A then selects
the lowest sufficiently large usable range, marks it `AllocatorMetadata`, and only then
constructs the bitmaps through the inherited identity mapping. There is no recursive
allocation.

Two bits are used per represented RAM frame. The theoretical payload and page-rounded arena
costs are:

| Guest RAM | Bitmap payload | Metadata arena |
|---:|---:|---:|
| 512 MiB | 32 KiB | 8 frames |
| 1 GiB | 64 KiB | 16 frames |
| 4 GiB | 256 KiB | 64 frames |

Canonicalization sorts at most 520 endpoints and performs a bounded interval/descriptor
sweep (`O(n log n + n^2)` with `n <= 260`). Bitmap initialization is linear in usable
frames. Allocation is a deterministic lowest-free linear word scan followed by a bounded
usable-range lookup; free performs the same bounded range lookup and then an `O(1)` bit update.

The existing fixed kernel placement near 256 MiB makes a 128 MiB guest unsupported. M1A
does not move the kernel merely to satisfy that matrix; relocation/page-table ownership is
later work. Live validation therefore uses 512 MiB, 1 GiB, and 4 GiB.
