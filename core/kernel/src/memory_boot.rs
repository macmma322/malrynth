//! Early-boot binding from the loader ABI to the physical-memory subsystem.

use crate::println;
use core::mem::{align_of, size_of};
use malrynth_abi::{BootInfo, MemoryKind, MemoryRegion};
use malrynth_kernel::memory::{
    BitmapAllocator, CanonicalRegion, FrameRange, MapError, OwnershipKind, PhysicalFrame,
    RawRegion, canonicalize, metadata_frames_required, select_metadata_range,
};

const MAX_FIRMWARE_REGIONS: usize = 256;
const MAX_RAW_REGIONS: usize = 260;
const MAX_ENDPOINTS: usize = MAX_RAW_REGIONS * 2;
const MAX_CANONICAL_REGIONS: usize = MAX_ENDPOINTS;
const SELF_CHECK_FRAMES: usize = 32;

const EMPTY_RAW: RawRegion = RawRegion {
    start: 0,
    len: 0,
    kind: OwnershipKind::Reserved,
};
const EMPTY_CANONICAL: CanonicalRegion = CanonicalRegion {
    frames: FrameRange {
        start: PhysicalFrame::from_number(0),
        end: PhysicalFrame::from_number(0),
    },
    kind: OwnershipKind::Reserved,
};

static mut RAW_REGIONS: [RawRegion; MAX_RAW_REGIONS] = [EMPTY_RAW; MAX_RAW_REGIONS];
static mut ENDPOINTS: [u64; MAX_ENDPOINTS] = [0; MAX_ENDPOINTS];
static mut CANONICAL_REGIONS: [CanonicalRegion; MAX_CANONICAL_REGIONS] =
    [EMPTY_CANONICAL; MAX_CANONICAL_REGIONS];

#[derive(Clone, Copy, Debug)]
pub(crate) enum BootMemoryError {
    BadRegionCount,
    BadRegionPointer,
    RegionBytesOverflow,
    Map(MapError),
    MetadataAddressOverflow,
    MetadataWordOverflow,
    SelfCheckAllocation,
    SelfCheckReserved,
    SelfCheckDuplicate,
    SelfCheckFree,
    SelfCheckAccounting,
}

impl core::fmt::Display for BootMemoryError {
    fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::Map(error) => write!(formatter, "map error: {error:?}"),
            other => write!(formatter, "{other:?}"),
        }
    }
}

impl From<MapError> for BootMemoryError {
    fn from(error: MapError) -> Self {
        Self::Map(error)
    }
}

pub(crate) fn initialize(info: &BootInfo) -> Result<BitmapAllocator<'static>, BootMemoryError> {
    let firmware_count =
        usize::try_from(info.regions_len).map_err(|_| BootMemoryError::BadRegionCount)?;
    if firmware_count == 0 || firmware_count > MAX_FIRMWARE_REGIONS {
        return Err(BootMemoryError::BadRegionCount);
    }
    if info.regions_phys == 0
        || !(info.regions_phys as usize).is_multiple_of(align_of::<MemoryRegion>())
    {
        return Err(BootMemoryError::BadRegionPointer);
    }
    let region_bytes = firmware_count
        .checked_mul(size_of::<MemoryRegion>())
        .ok_or(BootMemoryError::RegionBytesOverflow)?;
    info.regions_phys
        .checked_add(region_bytes as u64)
        .ok_or(BootMemoryError::RegionBytesOverflow)?;

    // SAFETY: the loader owns the ABI allocation, keeps it alive after ExitBootServices,
    // and the validated count, alignment, multiplication, and pointer end bound this slice.
    // M1A still treats every region field as untrusted input below.
    let firmware = unsafe {
        core::slice::from_raw_parts(info.regions_phys as *const MemoryRegion, firmware_count)
    };

    // SAFETY: early boot runs on one CPU before interrupts; these fixed .bss arrays have
    // no other references. Raw-pointer construction avoids creating references to the
    // `static mut` objects themselves.
    let raw = unsafe {
        core::slice::from_raw_parts_mut((&raw mut RAW_REGIONS).cast::<RawRegion>(), MAX_RAW_REGIONS)
    };
    let mut raw_count = 0usize;
    for region in firmware {
        raw[raw_count] = RawRegion {
            start: region.start_phys,
            len: region.len,
            kind: match region.kind {
                MemoryKind::Usable => OwnershipKind::Usable,
                MemoryKind::Reserved => OwnershipKind::Reserved,
                MemoryKind::KernelImage => OwnershipKind::KernelImage,
                MemoryKind::BootInfo => OwnershipKind::BootInfo,
                MemoryKind::UefiRuntime => OwnershipKind::UefiRuntime,
                MemoryKind::AcpiReclaimable => OwnershipKind::AcpiReclaimable,
            },
        };
        raw_count += 1;
    }

    raw[raw_count] = RawRegion {
        start: 0,
        len: 4096,
        kind: OwnershipKind::Reserved,
    };
    raw_count += 1;
    raw[raw_count] = RawRegion {
        start: info.kernel_phys_base,
        len: info.kernel_size,
        kind: OwnershipKind::KernelImage,
    };
    raw_count += 1;
    if info.framebuffer_present != 0 {
        raw[raw_count] = RawRegion {
            start: info.framebuffer.base_phys,
            len: info.framebuffer.size,
            kind: OwnershipKind::Framebuffer,
        };
        raw_count += 1;
    }

    let (endpoints, canonical) = early_buffers();
    let mut canonical_count = canonicalize(&raw[..raw_count], endpoints, canonical)?;
    let highest_frame = canonical[..canonical_count]
        .iter()
        .filter(|region| region.kind == OwnershipKind::Usable)
        .map(|region| region.frames.end.number())
        .max()
        .ok_or(MapError::NoUsableMemory)?;
    let metadata_frames = metadata_frames_required(highest_frame)?;
    let metadata = select_metadata_range(&canonical[..canonical_count], metadata_frames)?;
    let metadata_start = metadata
        .start
        .start_address()
        .ok_or(BootMemoryError::MetadataAddressOverflow)?
        .as_u64();
    let metadata_len = metadata_frames
        .checked_mul(4096)
        .ok_or(BootMemoryError::MetadataAddressOverflow)?;

    raw[raw_count] = RawRegion {
        start: metadata_start,
        len: metadata_len,
        kind: OwnershipKind::AllocatorMetadata,
    };
    raw_count += 1;
    canonical_count = canonicalize(&raw[..raw_count], endpoints, canonical)?;

    let words_u64 = highest_frame.div_ceil(64);
    let words = usize::try_from(words_u64).map_err(|_| BootMemoryError::MetadataWordOverflow)?;
    let one_bitmap_bytes = words
        .checked_mul(size_of::<u64>())
        .ok_or(BootMemoryError::MetadataWordOverflow)?;
    let total_bitmap_bytes = one_bitmap_bytes
        .checked_mul(2)
        .ok_or(BootMemoryError::MetadataWordOverflow)?;
    if total_bitmap_bytes as u64 > metadata_len {
        return Err(BootMemoryError::MetadataWordOverflow);
    }

    // SAFETY: canonicalization selected this identity-mapped, page-aligned usable RAM and
    // reserved it as AllocatorMetadata before any allocator became active. The two slices
    // are disjoint, fit inside that arena, and remain valid for the kernel lifetime.
    let (available, allocated) = unsafe {
        core::ptr::write_bytes(metadata_start as *mut u8, 0, metadata_len as usize);
        let available = core::slice::from_raw_parts_mut(metadata_start as *mut u64, words);
        let allocated = core::slice::from_raw_parts_mut(
            (metadata_start as usize + one_bitmap_bytes) as *mut u64,
            words,
        );
        (available, allocated)
    };
    let mut allocator = BitmapAllocator::new(&canonical[..canonical_count], available, allocated)?;
    let baseline = allocator.accounting();

    let mut sample = [PhysicalFrame::from_number(0); SELF_CHECK_FRAMES];
    for index in 0..SELF_CHECK_FRAMES {
        let frame = allocator
            .allocate()
            .ok_or(BootMemoryError::SelfCheckAllocation)?;
        if allocator.is_reserved(frame) {
            return Err(BootMemoryError::SelfCheckReserved);
        }
        if sample[..index].contains(&frame) {
            return Err(BootMemoryError::SelfCheckDuplicate);
        }
        sample[index] = frame;
    }
    for frame in sample {
        allocator
            .free(frame)
            .map_err(|_| BootMemoryError::SelfCheckFree)?;
    }
    if allocator.accounting() != baseline {
        return Err(BootMemoryError::SelfCheckAccounting);
    }

    println!("M1A physical memory:");
    println!("  raw descriptors: {firmware_count} (complete)");
    println!("  canonical ranges: {canonical_count}");
    println!(
        "  metadata: {:#018x}..{:#018x} ({} frames, {} bytes bitmap payload)",
        metadata_start,
        metadata_start + metadata_len,
        metadata_frames,
        total_bitmap_bytes
    );
    println!(
        "  frames: represented={} allocatable={} reserved={} allocated={} free={}",
        baseline.total_represented,
        baseline.allocatable,
        baseline.reserved,
        baseline.allocated,
        baseline.free
    );
    println!("  allocator self-check: {SELF_CHECK_FRAMES} unique frames, accounting restored");
    println!("MALRYNTH_M1A_MEMORY_OK");
    Ok(allocator)
}

fn early_buffers() -> (&'static mut [u64], &'static mut [CanonicalRegion]) {
    // SAFETY: called once during single-core early boot; no aliases exist. These buffers
    // remain kernel-owned for the boot lifetime and are never exposed outside this module.
    unsafe {
        (
            core::slice::from_raw_parts_mut((&raw mut ENDPOINTS).cast::<u64>(), MAX_ENDPOINTS),
            core::slice::from_raw_parts_mut(
                (&raw mut CANONICAL_REGIONS).cast::<CanonicalRegion>(),
                MAX_CANONICAL_REGIONS,
            ),
        )
    }
}
