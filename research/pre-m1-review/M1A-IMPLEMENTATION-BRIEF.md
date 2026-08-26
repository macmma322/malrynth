# M1A Implementation Brief — Physical Memory Ownership Foundation

**Status:** implementation-ready design; no M1 code written.  
**Input evidence:** `malrynth_abi::BootInfo` carries `regions_phys`, `regions_len`, `usable_bytes`, framebuffer data, and kernel extent. `malrynth_abi::MemoryRegion` carries `u64 start_phys`, `u64 len`, and `MemoryKind`. The UEFI loader currently collapses firmware types after `ExitBootServices`; the kernel currently only reports the resulting slice.

## Scope and boundary

M1A owns validation, canonicalization, physical ownership, frame allocation/deallocation, accounting, deterministic diagnostics, host tests, and QEMU evidence. It does not implement virtual address spaces, page tables, a heap, SMP locking, DMA/IOMMU, NUMA, or physical-memory objects.

Do not create a second handoff representation. Consume ABI `MemoryRegion` as the raw input and convert it once into kernel-owned canonical regions. Keep ABI types dumb; kernel-only address/frame types belong in the kernel memory module.

## Trust model

- **Untrusted/partially trusted:** the `BootInfo` pointer after the minimal ABI header check; `regions_phys`; region count; byte extent; every firmware-derived base, length, kind, ordering, alignment and overlap; `usable_bytes`; framebuffer extent; kernel extent arithmetic.
- **Trusted only after validation:** a bounded, sorted, gap-aware, non-overlapping canonical map produced by pure code. Never trust the loader's `usable_bytes`; recompute it.
- **Kernel-owned:** canonical-map storage, allocator metadata, allocation bits/state, reservation records and accounting counters.

Before constructing a Rust slice, validate non-null/alignment, `regions_len <= MAX_INPUT_REGIONS`, checked `count * size_of::<MemoryRegion>()`, checked pointer end, and that the handoff allocation is identity-accessible during this boot phase. ABI enum discriminants need a validation-friendly representation before treating arbitrary bytes as a Rust enum; if the loader remains the only producer this is partially trusted, not proof against corruption.

## Canonicalization algorithm

Use a bounded sweep over half-open byte ranges `[start, end)`:

1. Validate each input: known kind, nonzero length, checked `start + len`, and physical-address ceiling supported by x86_64/configuration.
2. Convert each input to conservative full-frame coverage:
   - usable: `start = align_up(start)`, `end = align_down(end)`;
   - non-usable/reservations: `start = align_down(start)`, `end = align_up(end)` using checked arithmetic.
3. Add explicit kernel, loader-required/BootInfo, framebuffer, runtime, MMIO/reserved, and allocator-metadata reservations. A framebuffer that overlaps firmware “usable” must win.
4. Collect bounded interval endpoints, sort deterministically, and walk adjacent endpoint pairs. For each span choose the highest-priority covering classification. Suggested precedence: explicit kernel/metadata > framebuffer > UEFI runtime/MMIO/reserved > BootInfo/loader-required > ACPI reclaimable > usable. Keep reasons distinct for diagnostics even if all are non-allocatable.
5. Merge adjacent spans only when classification and reservation reason match.
6. Treat gaps/unmentioned physical space as reserved/unknown; never infer usability.
7. Recompute usable and reserved frame counts with checked arithmetic and validate all postconditions.

If the loader map was truncated, initialization is boot-fatal. Fix the current silent cap before M1A.

## Core types and safe arithmetic

Use small `#[repr(transparent)]` newtypes, not a generic arithmetic framework:

- `PhysicalAddress(u64)`: checked construction against the supported physical ceiling; `checked_add`, `align_down`, `checked_align_up`.
- `PhysicalFrame(u64)`: frame number, with checked conversion to/from a 4 KiB-aligned physical address.
- `FrameRange { start: PhysicalFrame, end: PhysicalFrame }`: half-open; checked length, intersection, containment, and bounded iteration.
- `PAGE_SIZE: u64 = 4096`; assert power-of-two once.

Never use `usize` for physical addresses or byte lengths. Convert to `usize` only after checking a bounded host/kernel allocation index. `MemoryRegion::end_phys()` is unchecked today and must not be used on unvalidated input.

## Required invariants and challenges

1. No zero-sized canonical region. Challenge with zero input, sub-page usable input, and alignment collapse.
2. No overflow in base+length, alignment, frame conversion, counts, or accounting. Challenge `u64::MAX` boundaries.
3. Canonical regions are sorted, non-overlapping, maximal-by-equal-class, and deterministic for every permutation of the same input.
4. Every represented frame has exactly one classification; every gap is implicitly unknown/reserved.
5. Reserved wins over usable for any overlap. Challenge nested, partial, duplicate and multi-way overlaps.
6. Allocator never returns kernel, loader-required/BootInfo, framebuffer, runtime, ACPI-not-yet-reclaimed, MMIO/unknown, metadata, or explicit reservations.
7. An allocated frame transitions free → allocated exactly once; deallocation transitions allocated → free exactly once.
8. Double free, never-allocated free, out-of-domain free and reserved-frame free are rejected without mutating state.
9. `free + allocated + permanently_reserved == managed_total`; counters change only after successful state transitions.
10. Allocation order is deterministic (lowest frame first for M1A unless policy is explicitly changed).
11. No frame zero allocation by default; keep the null-page reservation explicit.

## Allocator choice

| Design | M1 complexity | Metadata | Allocate/free | Fragmentation / future |
|---|---:|---:|---|---|
| Bitmap | low | 1 bit/frame plus bounded summaries/state | linear scan worst case; O(1) free | arbitrary reservations easy; contiguous search can fragment |
| Free-range list | low initially | proportional to holes | first-fit O(r); free/coalesce O(r) | metadata growth and bootstrap mutation are awkward |
| Buddy | medium/high | moderate | O(log n) | strong contiguous/power-of-two support; premature for M1A |
| Hierarchical bitmap | medium | slightly above bitmap | near O(levels) | good evolution, unnecessary before measurements |

**Recommendation: bounded bitmap with a next-fit/lowest-free search hint and explicit allocation-state checking.** It is the smallest deterministic design that supports arbitrary reservations and hostile host tests. Use one bit for allocatable ownership and one bit for current allocation, or equivalent immutable availability plus mutable state; this distinguishes invalid/reserved frees from double frees. Do not use a free-range list whose node storage itself depends on the allocator.

Migration path: keep the public `PhysicalFrameAllocator` API in frame/range terms. Later replace internals with a hierarchical bitmap or buddy allocator for contiguous/huge-page demand without changing consumers. Do not promise huge-page efficiency in M1A.

## Metadata bootstrap

Use staged initialization with a reserved bootstrap arena:

1. Purely validate/canonicalize into fixed-capacity early storage linked into kernel `.bss` (bounded by the accepted input-region cap).
2. Compute bitmap bytes from the highest managed frame using checked arithmetic.
3. Select a page-aligned contiguous subrange from canonical usable memory, excluding all explicit reservations, without calling the allocator.
4. Mark that range `AllocatorMetadata`, zero it through the current identity mapping, initialize bits/counters, then expose the allocator.
5. Keep the tiny canonical-map array in kernel static storage initially. Later, after the heap exists, it may be copied into ordinary kernel-owned memory.

This avoids circular allocation and avoids relying on loader-provided mutable scratch after ownership transfer. Failure to place metadata is boot-fatal. Print its physical range and byte/frame cost.

## Failure policy

- **Boot-fatal:** invalid ABI pointer/count/enum; truncated map; arithmetic overflow; malformed or impossible canonicalization; canonical invariant failure; reservation outside supported address space; metadata cannot be placed; no usable frames after reservations; accounting mismatch during initialization.
- **Normal later failure:** allocation exhaustion returns `None`/`OutOfMemory` without corrupting counters.
- **Programming/invariant violation:** invalid, double, never-allocated, or reserved deallocation returns a typed error in testable APIs; kernel-internal callers may escalate that error to panic with deterministic diagnostics. Do not silently ignore it.

## File/module ownership

Fit the current small kernel rather than creating a deep hierarchy:

```text
core/kernel/src/
  memory/
    mod.rs       # initialization boundary, public allocator API, diagnostics
    addr.rs      # PhysicalAddress, PhysicalFrame, FrameRange, alignment/arithmetic
    physical.rs  # canonicalization + bitmap allocator + host-side unit tests
  main.rs        # minimal call site and M1A diagnostic marker wiring only
```

Three files are sufficient initially. If `physical.rs` materially exceeds reviewability, split `map.rs` from allocator code then, not pre-emptively. ABI layout changes for truncation handling remain owned by the pre-M1 fix, not M1A implementation.

## Host-side test strategy

Make canonicalization and allocator state transitions pure over caller-supplied fixed buffers so they run on the host with zero new kernel dependencies.

Mandatory table tests:

- empty map; one usable region; unsorted input; all permutations produce identical output;
- overlapping/adjacent usable; usable plus reserved overlap; duplicate and nested regions;
- zero length; `base + length` overflow; count/endpoint-cap exhaustion;
- below-page, partially aligned, and alignment-collapsed usable ranges;
- region ending at supported address maximum and `u64::MAX` rejection;
- kernel, BootInfo/loader, framebuffer, runtime and explicit reservation inside usable input;
- missing/unmentioned gaps remain reserved;
- no allocatable memory; one frame; allocate to exhaustion; exhaustion is stable;
- free/reallocate deterministic behavior; double, invalid, out-of-domain, and reserved free;
- accounting before/after every success and rejected operation;
- metadata placement exact fit, fragmented failure, exclusion from allocation;
- loader descriptor overflow produces an explicit error.

Property/fuzz testing is justified for the pure normalizer because overlap/permutation state space is high. Start with deterministic generated tests using an in-tree PRNG or exhaustive small maps; add no dependency yet. Add a fuzz crate only after it finds value and remains host-only, outside the zero-dependency kernel target.

## QEMU M1A matrix and evidence

Boot at minimum with `-m 128M`, `-m 1G`, and `-m 4G`. The current fixed kernel base at 256 MiB makes 128 MiB impossible in M0, so the M1A sequence must either retire that placement first or explicitly record 128 MiB as an expected pre-relocation failure; do not falsely call the matrix passing while the fixed base remains.

Where supported, add QEMU memory holes/devices that produce extra reserved/MMIO ranges and vary framebuffer presence. Run cold boots with pristine NVRAM and repeat each size to establish determinism.

Before the future `MALRYNTH_M1_BOOT_OK`, print deterministic evidence:

- raw input count and validated completeness;
- canonical region count and stable digest/summary;
- total described, usable, reserved, metadata, free and allocated frames;
- kernel, handoff/loader, framebuffer and metadata frame ranges;
- allocator self-test: allocate a bounded sample, prove uniqueness/reservation exclusion, free it, and prove accounting restoration;
- explicit success/failure line for every invariant check.

Do not add the M1 marker during preparation.

## Performance budgets

- Metadata: bitmap payload no more than 2 bits per managed 4 KiB frame plus small fixed summaries/cursors; report actual bytes and percentage of RAM.
- Initialization: bounded by sorting endpoints plus a linear sweep; target `O(n log n + F/word_size)` for `n` regions and `F` managed frames. No quadratic overlap loop over frames × regions.
- Single-frame allocation: amortized scan from a hint; worst case bounded by bitmap words. Record scanned-word count in host benchmarks before setting time targets.
- Free: O(1) bit/counter update with validation.

No nanosecond gates until measurement exists.

## SMP and later architecture

Initialization remains single-core. Encapsulate all mutable allocator state so callers cannot retain raw bitmap references. At SMP bring-up, place a coarse spinlock around the global allocator first; later add per-CPU caches for single frames only if contention is measured. Contiguous allocations and reservations remain globally coordinated. The API uses physical frames/ranges, preparing for AddressSpace mappings, DMA/IOMMU constraints and physical-memory objects without implementing them.

## Conflict-free Codex / Claude split

- **Codex owns after approval:** `core/kernel/src/memory/**`, the narrow `main.rs` initialization/diagnostic call site, host allocator tests, and QEMU M1A diagnostics/tests.
- **Claude owns:** architecture and invariant review, unsafe-code audit, ABI/truncation-fix approval, and final integration decision. Claude should comment/review these files, not edit them concurrently.
- **Pre-M1 fixes:** land boot tooling, panic artifact binding, and loader/ABI truncation handling before opening the M1A implementation branch. Assign each file set to one implementer at a time.

## M1A completion gate

M1A is complete only when all hostile host tests pass, the three memory sizes have evidence appropriate to the then-current placement model, all reservations are excluded, accounting returns to baseline after self-test, no new kernel dependency is introduced, and an independent unsafe/invariant review approves the exact implementation.
