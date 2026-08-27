# ADR-0006 — The Physical Direct Map Covers Classified RAM Only

- **Status:** ACCEPTED (2026-08-27). Constrains **M1B**. Recorded *before* M1A so that M1A's physical-memory representation cannot foreclose it.
- **Deciders:** Nikolay Nikolov Georgiev (founder)
- **Depends on:** [M1](../roadmap/M1.md) scope; the M0 boot handoff ABI (`MemoryKind`, `MemoryRegion`)
- **Review trigger:** M1B, when the direct map is actually built; again at M4, when device and IOMMU authority exist and can own device apertures properly.

## Context

[M1](../roadmap/M1.md) lists, in one line, "Kernel virtual address space layout, including a
physical-memory direct map." That line has an obvious implementation — map the whole physical
address space at a fixed virtual offset, write-back, and enjoy a constant `phys → virt`
conversion. That implementation is wrong on real hardware, and it is wrong in a way that an
emulator will not reveal.

**The handoff cannot distinguish RAM from devices.** The loader collapses the ~15 UEFI memory
types into six `MemoryKind` values, and it preserves **no** UEFI cache attributes at all —
`EFI_MEMORY_UC`, `EFI_MEMORY_WC`, `EFI_MEMORY_WT`, `EFI_MEMORY_WB` and the rest are discarded.
Everything the kernel is not meant to touch becomes `MemoryKind::Reserved`. A firmware-reserved
RAM range and a memory-mapped device aperture therefore arrive at the kernel as the *same*
value. From `BootInfo` alone, M1 cannot tell them apart.

**Mapping a device aperture as ordinary write-back RAM is not a performance mistake.** A
write-back mapping licenses the processor to fill cache lines, to read speculatively, to
combine and reorder writes, and to write back dirty lines at a time of its choosing. Against
device registers those are real bus transactions at unpredictable times: spurious reads with
side effects, writes that are merged or lost, and machine checks on ranges that do not tolerate
speculation. This is why an OS reaches for an explicitly uncached or write-combining mapping
when it touches a device, rather than letting device memory fall through a blanket RAM mapping.

**Aliasing makes it worse.** x86-64 treats two mappings of the same physical page with different
effective memory types as architecturally undefined. A blanket write-back direct map plus a
later, correct uncached device mapping of the same page is exactly that alias — so "map
everything now, map devices properly later" does not compose. The blanket map has to not exist
in the first place.

**QEMU will hide all of this.** Under TCG there are no caches to be incoherent, and the device
models tolerate access patterns that real silicon does not. A direct map built the wrong way
will boot, pass the M1 exit criteria, and fail on the first physical machine. That is precisely
the class of decision this project records before writing the code rather than after.

## Decision

The following invariants hold for the M1 direct map. They are stated now, before M1A, because
M1A chooses the representation that M1B has to build on.

1. **The direct map covers only physical memory Malrynth has positively classified as RAM it
   may treat as ordinary write-back memory.** Coverage is opt-in by classification, never by
   address range.

2. **Device and MMIO physical ranges are never implicitly included.** They are not covered by
   the direct map at any cache attribute.

3. **Unknown and `Reserved` physical space is not assumed to be RAM.** Absence of information is
   not evidence of RAM. Not allocating from a range is *not* the same as not mapping it: a
   write-back mapping alone already permits speculative access, so unclassified space must be
   left unmapped rather than merely un-allocated.

4. **Device memory is mapped deliberately, through the future device/`IoRegion` authority, with
   an explicit cache attribute chosen per region.** Device mappings are requested, not inherited.

5. **No physical page is reachable through two mappings with different cache attributes.** This
   follows from (1)–(4) and is stated separately because it is the invariant that a later
   "convenience" direct map would silently break.

### What this constrains in M1A

M1A must preserve, in whatever structure it chooses, the difference between:

- RAM the frame allocator may hand out,
- RAM-backed memory that exists but is not allocatable (the kernel image, the boot info block),
- and physical space **not known to be RAM** at all.

A representation that flattens physical address space into a single free/used bitmap spanning
`0 .. max_phys` erases the third category and makes invariants (2) and (3) unimplementable
without redesign. M1A must also not assume that the direct map exists, nor that `phys → virt`
is a constant offset valid across all of physical space.

M1A is otherwise unaffected. This ADR adds no work to it.

## Explicitly deferred

- **Whether `BootInfo` must carry UEFI cache attributes and finer memory types.** Recorded as a
  future decision; **the ABI is not expanded now.** There is no evidence yet that M1B cannot
  build a correct direct map from the existing classification, and M4's ACPI and PCIe
  enumeration is a more authoritative source for device apertures than the UEFI memory map is.
  If M1B demonstrates that the present handoff is insufficient, *that* is the evidence, and
  `BOOT_ABI_VERSION` is bumped then. The ABI is EXPERIMENTAL until M3 precisely so this can be
  decided late and on evidence.
- **Eager versus lazy construction** of the direct map.
- **The virtual base and layout** of the direct map, which M1 already requires an ADR for.

## Alternatives considered

- **Map all physical address space write-back and fix it when hardware complains.** Rejected.
  The failure is silent under emulation and non-deterministic on hardware, and by the time it
  is observed the constant-offset assumption is load-bearing throughout the kernel.
- **Expand `BootInfo` now to carry the full UEFI attribute set.** Rejected as premature. It
  commits the ABI to a shape chosen without a consumer, when the consumer (M1B) does not exist
  yet and the better source (M4 enumeration) is not built yet. Choosing late is cheap here;
  choosing wrong is not.
- **Direct-map `Reserved` too, but never allocate from it.** Rejected. It confuses allocation
  with mapping. The hazard is the mapping.
- **Say nothing until M1B and decide then.** Rejected. M1A picks the physical-memory
  representation, and the wrong representation makes the correct M1B unreachable without
  redesign. That is the whole reason this is recorded before M1A rather than with the code.

## Consequences

**What is given up.** The constant-offset `phys → virt` conversion that holds everywhere. M1B
must carry a notion of which physical ranges are direct-mapped, and code converting a physical
address must be able to fail or be restricted to addresses known to be covered. That is a real
cost in ergonomics, paid on every physical-address conversion in the kernel.

**What is protected.** Correctness on real hardware, and the ability to introduce device
mapping authority at M4 without unpicking a blanket mapping that the rest of the kernel has
come to depend on.

**Neutral.** Nothing is implemented. M1B is not started, no mapping code exists, and the boot
ABI is unchanged.
