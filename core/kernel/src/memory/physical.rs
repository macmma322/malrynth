//! Canonical physical ownership map and bounded bitmap allocator.

use super::{FrameRange, PAGE_SIZE, PhysicalAddress, PhysicalFrame};

/// Maximum number of raw firmware regions accepted from the handoff.
pub const MAX_RAW_REGIONS: usize = 260;

/// Kernel-owned classification of physical memory.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OwnershipKind {
    /// RAM available to the frame allocator.
    Usable,
    /// Unknown, firmware-reserved, or otherwise unavailable memory.
    Reserved,
    /// UEFI runtime code or data.
    UefiRuntime,
    /// ACPI reclaimable memory, not yet reclaimed.
    AcpiReclaimable,
    /// The loaded kernel image.
    KernelImage,
    /// Loader handoff structures and retained loader allocations.
    BootInfo,
    /// Linear framebuffer memory.
    Framebuffer,
    /// Bitmap allocator metadata.
    AllocatorMetadata,
}

impl OwnershipKind {
    const fn priority(self) -> u8 {
        match self {
            Self::Usable => 0,
            Self::AcpiReclaimable => 1,
            Self::Reserved => 2,
            Self::BootInfo => 3,
            Self::UefiRuntime => 4,
            Self::Framebuffer => 5,
            Self::KernelImage => 6,
            Self::AllocatorMetadata => 7,
        }
    }
}

/// Untrusted byte range before page-boundary canonicalization.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RawRegion {
    /// Physical byte base.
    pub start: u64,
    /// Length in bytes.
    pub len: u64,
    /// Proposed ownership classification.
    pub kind: OwnershipKind,
}

/// Trusted page-granular ownership range.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CanonicalRegion {
    /// Half-open frame range.
    pub frames: FrameRange,
    /// Sole owner/classification of every frame in the range.
    pub kind: OwnershipKind,
}

/// Rejection reasons for untrusted maps or bounded scratch storage.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MapError {
    /// No descriptors were supplied.
    Empty,
    /// More descriptors were supplied than M1A accepts.
    TooManyInputRegions,
    /// A region's byte end wrapped.
    AddressOverflow,
    /// A reservation could not be rounded outward without wrapping.
    AlignmentOverflow,
    /// Endpoint scratch storage was too small.
    EndpointCapacity,
    /// Canonical output storage was too small.
    OutputCapacity,
    /// No usable frames remain.
    NoUsableMemory,
    /// No usable contiguous range can hold allocator metadata.
    NoMetadataRange,
    /// Bitmap size arithmetic overflowed or caller storage is too small.
    BitmapCapacity,
}

/// Canonicalizes untrusted ranges into deterministic, sorted, non-overlapping ownership.
pub fn canonicalize(
    raw: &[RawRegion],
    endpoints: &mut [u64],
    output: &mut [CanonicalRegion],
) -> Result<usize, MapError> {
    if raw.is_empty() {
        return Err(MapError::Empty);
    }
    if raw.len() > MAX_RAW_REGIONS {
        return Err(MapError::TooManyInputRegions);
    }
    let required_endpoints = raw.len().checked_mul(2).ok_or(MapError::EndpointCapacity)?;
    if endpoints.len() < required_endpoints {
        return Err(MapError::EndpointCapacity);
    }

    let mut endpoint_count = 0usize;
    for region in raw {
        let Some(byte_end) = region.start.checked_add(region.len) else {
            return Err(MapError::AddressOverflow);
        };
        if region.len == 0 {
            continue;
        }
        let start = PhysicalAddress::new(region.start);
        let end = PhysicalAddress::new(byte_end);
        let (aligned_start, aligned_end) = if region.kind == OwnershipKind::Usable {
            (
                start
                    .checked_align_up(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?,
                end.align_down(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?,
            )
        } else {
            (
                start
                    .align_down(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?,
                end.checked_align_up(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?,
            )
        };
        if aligned_start.as_u64() >= aligned_end.as_u64() {
            continue;
        }
        endpoints[endpoint_count] = aligned_start.as_u64();
        endpoints[endpoint_count + 1] = aligned_end.as_u64();
        endpoint_count += 2;
    }
    if endpoint_count == 0 {
        return Err(MapError::NoUsableMemory);
    }
    endpoints[..endpoint_count].sort_unstable();
    let mut unique = 0usize;
    for index in 0..endpoint_count {
        if unique == 0 || endpoints[index] != endpoints[unique - 1] {
            endpoints[unique] = endpoints[index];
            unique += 1;
        }
    }

    let mut output_count = 0usize;
    for pair in endpoints[..unique].windows(2) {
        let start = pair[0];
        let end = pair[1];
        if start == end {
            continue;
        }
        let mut selected = OwnershipKind::Reserved;
        let mut covered = false;
        for region in raw {
            let Some(byte_end) = region.start.checked_add(region.len) else {
                return Err(MapError::AddressOverflow);
            };
            if region.len == 0 {
                continue;
            }
            let aligned_start = if region.kind == OwnershipKind::Usable {
                PhysicalAddress::new(region.start)
                    .checked_align_up(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?
                    .as_u64()
            } else {
                PhysicalAddress::new(region.start)
                    .align_down(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?
                    .as_u64()
            };
            let aligned_end = if region.kind == OwnershipKind::Usable {
                PhysicalAddress::new(byte_end)
                    .align_down(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?
                    .as_u64()
            } else {
                PhysicalAddress::new(byte_end)
                    .checked_align_up(PAGE_SIZE)
                    .ok_or(MapError::AlignmentOverflow)?
                    .as_u64()
            };
            if aligned_start <= start && aligned_end >= end {
                if !covered || region.kind.priority() > selected.priority() {
                    selected = region.kind;
                }
                covered = true;
            }
        }
        if output_count > 0
            && output[output_count - 1].kind == selected
            && output[output_count - 1].frames.end.number() == start / PAGE_SIZE
        {
            output[output_count - 1].frames.end = PhysicalFrame::from_number(end / PAGE_SIZE);
            continue;
        }
        if output_count == output.len() {
            return Err(MapError::OutputCapacity);
        }
        output[output_count] = CanonicalRegion {
            frames: FrameRange::new(
                PhysicalFrame::from_number(start / PAGE_SIZE),
                PhysicalFrame::from_number(end / PAGE_SIZE),
            )
            .ok_or(MapError::AddressOverflow)?,
            kind: selected,
        };
        output_count += 1;
    }
    if !output[..output_count]
        .iter()
        .any(|region| region.kind == OwnershipKind::Usable && !region.frames.is_empty())
    {
        return Err(MapError::NoUsableMemory);
    }
    Ok(output_count)
}

/// Returns metadata frames required for two bits per represented frame.
pub fn metadata_frames_required(highest_frame: u64) -> Result<u64, MapError> {
    let bitmap_bytes = highest_frame
        .checked_add(3)
        .ok_or(MapError::BitmapCapacity)?
        / 4;
    Ok(bitmap_bytes.div_ceil(PAGE_SIZE).max(1))
}

/// Selects the lowest usable range large enough for bitmap metadata.
pub fn select_metadata_range(
    regions: &[CanonicalRegion],
    frames_required: u64,
) -> Result<FrameRange, MapError> {
    for region in regions {
        if region.kind == OwnershipKind::Usable && region.frames.len() >= frames_required {
            return FrameRange::new(
                region.frames.start,
                PhysicalFrame::from_number(region.frames.start.number() + frames_required),
            )
            .ok_or(MapError::NoMetadataRange);
        }
    }
    Err(MapError::NoMetadataRange)
}

/// Physical-frame accounting for allocator-controlled RAM.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Accounting {
    /// Frames represented from zero through the highest described frame.
    pub total_represented: u64,
    /// Frames the allocator owns, whether free or allocated.
    pub allocatable: u64,
    /// Permanently unavailable represented frames.
    pub reserved: u64,
    /// Currently allocated frames.
    pub allocated: u64,
    /// Currently free allocator-owned frames.
    pub free: u64,
}

/// Invalid deallocation reason.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FreeError {
    /// Frame lies outside the represented domain.
    OutsideDomain,
    /// Frame is permanently reserved.
    Reserved,
    /// Frame is allocator-owned but is not currently allocated.
    NotAllocated,
}

/// Deterministic lowest-free bitmap physical-frame allocator.
pub struct BitmapAllocator<'a> {
    available: &'a mut [u64],
    allocated: &'a mut [u64],
    highest_frame: u64,
    accounting: Accounting,
}

impl<'a> BitmapAllocator<'a> {
    /// Initializes allocator state in caller-provided metadata words.
    pub fn new(
        regions: &[CanonicalRegion],
        available: &'a mut [u64],
        allocated: &'a mut [u64],
    ) -> Result<Self, MapError> {
        let highest_frame = regions
            .iter()
            .filter(|region| region.kind == OwnershipKind::Usable)
            .map(|region| region.frames.end.number())
            .max()
            .ok_or(MapError::NoUsableMemory)?;
        let words_u64 = highest_frame.div_ceil(64);
        let words = usize::try_from(words_u64).map_err(|_| MapError::BitmapCapacity)?;
        if available.len() < words || allocated.len() < words {
            return Err(MapError::BitmapCapacity);
        }
        available[..words].fill(0);
        allocated[..words].fill(0);
        let mut allocatable = 0u64;
        for region in regions {
            if region.kind != OwnershipKind::Usable {
                continue;
            }
            for number in region.frames.start.number()..region.frames.end.number() {
                set_bit(available, number, true);
                allocatable = allocatable.checked_add(1).ok_or(MapError::BitmapCapacity)?;
            }
        }
        let accounting = Accounting {
            total_represented: highest_frame,
            allocatable,
            reserved: highest_frame - allocatable,
            allocated: 0,
            free: allocatable,
        };
        Ok(Self {
            available: &mut available[..words],
            allocated: &mut allocated[..words],
            highest_frame,
            accounting,
        })
    }

    /// Allocates the lowest-numbered free frame.
    pub fn allocate(&mut self) -> Option<PhysicalFrame> {
        for (word_index, (&available, allocated)) in self
            .available
            .iter()
            .zip(self.allocated.iter_mut())
            .enumerate()
        {
            let free = available & !*allocated;
            if free == 0 {
                continue;
            }
            let bit = free.trailing_zeros() as u64;
            let frame = word_index as u64 * 64 + bit;
            if frame >= self.highest_frame {
                return None;
            }
            *allocated |= 1u64 << bit;
            self.accounting.allocated += 1;
            self.accounting.free -= 1;
            return Some(PhysicalFrame::from_number(frame));
        }
        None
    }

    /// Releases an allocated frame, rejecting invalid state transitions.
    pub fn free(&mut self, frame: PhysicalFrame) -> Result<(), FreeError> {
        let number = frame.number();
        if number >= self.highest_frame {
            return Err(FreeError::OutsideDomain);
        }
        if !get_bit(self.available, number) {
            return Err(FreeError::Reserved);
        }
        if !get_bit(self.allocated, number) {
            return Err(FreeError::NotAllocated);
        }
        set_bit(self.allocated, number, false);
        self.accounting.allocated -= 1;
        self.accounting.free += 1;
        Ok(())
    }

    /// Returns current accounting.
    #[must_use]
    pub const fn accounting(&self) -> Accounting {
        self.accounting
    }

    /// Returns whether a frame is permanently reserved.
    #[must_use]
    pub fn is_reserved(&self, frame: PhysicalFrame) -> bool {
        frame.number() >= self.highest_frame || !get_bit(self.available, frame.number())
    }
}

fn get_bit(words: &[u64], number: u64) -> bool {
    let index = number as usize / 64;
    let bit = number % 64;
    words
        .get(index)
        .is_some_and(|word| word & (1u64 << bit) != 0)
}

fn set_bit(words: &mut [u64], number: u64, value: bool) {
    let index = number as usize / 64;
    let bit = number % 64;
    if value {
        words[index] |= 1u64 << bit;
    } else {
        words[index] &= !(1u64 << bit);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const EMPTY_CANONICAL: CanonicalRegion = CanonicalRegion {
        frames: FrameRange {
            start: PhysicalFrame::from_number(0),
            end: PhysicalFrame::from_number(0),
        },
        kind: OwnershipKind::Reserved,
    };

    fn canonical(raw: &[RawRegion]) -> Result<([CanonicalRegion; 32], usize), MapError> {
        let mut endpoints = [0; 64];
        let mut output = [EMPTY_CANONICAL; 32];
        let count = canonicalize(raw, &mut endpoints, &mut output)?;
        Ok((output, count))
    }

    #[test]
    fn hostile_map_validation_and_alignment() {
        assert_eq!(canonical(&[]), Err(MapError::Empty));
        assert_eq!(
            canonical(&[RawRegion {
                start: u64::MAX - 1,
                len: 4,
                kind: OwnershipKind::Usable
            }]),
            Err(MapError::AddressOverflow)
        );
        assert_eq!(
            canonical(&[RawRegion {
                start: u64::MAX - 4095,
                len: 1,
                kind: OwnershipKind::Reserved
            }]),
            Err(MapError::AlignmentOverflow)
        );
        assert_eq!(
            canonical(&[RawRegion {
                start: 1,
                len: 4094,
                kind: OwnershipKind::Usable
            }]),
            Err(MapError::NoUsableMemory)
        );
    }

    #[test]
    fn input_and_scratch_capacities_fail_explicitly() {
        let input = [RawRegion {
            start: 0,
            len: PAGE_SIZE,
            kind: OwnershipKind::Usable,
        }; MAX_RAW_REGIONS + 1];
        let mut endpoints = [0; 2];
        let mut output = [EMPTY_CANONICAL; 1];
        assert_eq!(
            canonicalize(&input, &mut endpoints, &mut output),
            Err(MapError::TooManyInputRegions)
        );
        assert_eq!(
            canonicalize(&input[..2], &mut endpoints, &mut output),
            Err(MapError::EndpointCapacity)
        );
    }

    #[test]
    fn usable_rounds_inward_and_reservations_round_outward() {
        let input = [
            RawRegion {
                start: 1,
                len: PAGE_SIZE * 4 - 2,
                kind: OwnershipKind::Usable,
            },
            RawRegion {
                start: PAGE_SIZE + 1,
                len: 1,
                kind: OwnershipKind::Reserved,
            },
        ];
        let (regions, count) = canonical(&input).unwrap();
        assert_eq!(count, 2);
        assert_eq!(regions[0].kind, OwnershipKind::Reserved);
        assert_eq!(regions[0].frames.start.number(), 1);
        assert_eq!(regions[0].frames.end.number(), 2);
        assert_eq!(regions[1].kind, OwnershipKind::Usable);
        assert_eq!(regions[1].frames.start.number(), 2);
        assert_eq!(regions[1].frames.end.number(), 3);
    }

    #[test]
    fn reserved_wins_and_output_is_sorted_and_merged() {
        let input = [
            RawRegion {
                start: 0x5000,
                len: 0x3000,
                kind: OwnershipKind::Usable,
            },
            RawRegion {
                start: 0x1000,
                len: 0x7000,
                kind: OwnershipKind::Usable,
            },
            RawRegion {
                start: 0x3001,
                len: 1,
                kind: OwnershipKind::Framebuffer,
            },
            RawRegion {
                start: 0x1000,
                len: 0x7000,
                kind: OwnershipKind::Usable,
            },
        ];
        let (output, count) = canonical(&input).unwrap();
        assert_eq!(count, 3);
        assert_eq!(
            output[0].frames,
            FrameRange::new(PhysicalFrame::from_number(1), PhysicalFrame::from_number(3)).unwrap()
        );
        assert_eq!(output[0].kind, OwnershipKind::Usable);
        assert_eq!(output[1].kind, OwnershipKind::Framebuffer);
        assert_eq!(output[2].kind, OwnershipKind::Usable);
    }

    #[test]
    fn permutation_is_deterministic_and_explicit_reservations_win() {
        let a = RawRegion {
            start: 0x1000,
            len: 0x9000,
            kind: OwnershipKind::Usable,
        };
        let b = RawRegion {
            start: 0x3000,
            len: 0x2000,
            kind: OwnershipKind::KernelImage,
        };
        let c = RawRegion {
            start: 0x7000,
            len: 0x1000,
            kind: OwnershipKind::BootInfo,
        };
        let first = canonical(&[a, b, c]).unwrap();
        let second = canonical(&[c, a, b]).unwrap();
        assert_eq!(&first.0[..first.1], &second.0[..second.1]);
        assert!(
            first.0[..first.1]
                .iter()
                .any(|r| r.kind == OwnershipKind::KernelImage)
        );
        assert!(
            first.0[..first.1]
                .iter()
                .any(|r| r.kind == OwnershipKind::BootInfo)
        );
    }

    #[test]
    fn metadata_selection_and_footprint_are_bounded() {
        assert_eq!(
            metadata_frames_required(512 * 1024 * 1024 / PAGE_SIZE),
            Ok(8)
        );
        assert_eq!(
            metadata_frames_required(1024 * 1024 * 1024 / PAGE_SIZE),
            Ok(16)
        );
        assert_eq!(
            metadata_frames_required(4 * 1024 * 1024 * 1024 / PAGE_SIZE),
            Ok(64)
        );
        let (regions, count) = canonical(&[RawRegion {
            start: 0x1000,
            len: 0x20_000,
            kind: OwnershipKind::Usable,
        }])
        .unwrap();
        let selected = select_metadata_range(&regions[..count], 2).unwrap();
        assert_eq!(selected.start.number(), 1);
        assert_eq!(selected.len(), 2);
        assert_eq!(
            select_metadata_range(&regions[..count], 1000),
            Err(MapError::NoMetadataRange)
        );
    }

    #[test]
    fn allocator_state_machine_accounting_and_order() {
        let regions = [
            CanonicalRegion {
                frames: FrameRange::new(
                    PhysicalFrame::from_number(0),
                    PhysicalFrame::from_number(2),
                )
                .unwrap(),
                kind: OwnershipKind::Reserved,
            },
            CanonicalRegion {
                frames: FrameRange::new(
                    PhysicalFrame::from_number(2),
                    PhysicalFrame::from_number(4),
                )
                .unwrap(),
                kind: OwnershipKind::Usable,
            },
            CanonicalRegion {
                frames: FrameRange::new(
                    PhysicalFrame::from_number(4),
                    PhysicalFrame::from_number(5),
                )
                .unwrap(),
                kind: OwnershipKind::AllocatorMetadata,
            },
        ];
        let mut available = [0u64; 1];
        let mut allocated = [0u64; 1];
        let mut allocator = BitmapAllocator::new(&regions, &mut available, &mut allocated).unwrap();
        assert_eq!(
            allocator.accounting(),
            Accounting {
                total_represented: 4,
                allocatable: 2,
                reserved: 2,
                allocated: 0,
                free: 2
            }
        );
        let first = allocator.allocate().unwrap();
        let second = allocator.allocate().unwrap();
        assert_eq!((first.number(), second.number()), (2, 3));
        assert!(allocator.allocate().is_none());
        assert_eq!(
            allocator.free(PhysicalFrame::from_number(0)),
            Err(FreeError::Reserved)
        );
        assert_eq!(
            allocator.free(PhysicalFrame::from_number(5)),
            Err(FreeError::OutsideDomain)
        );
        allocator.free(first).unwrap();
        assert_eq!(allocator.free(first), Err(FreeError::NotAllocated));
        assert_eq!(allocator.allocate(), Some(first));
        assert_eq!(allocator.accounting().allocated, 2);
        assert_eq!(allocator.accounting().free, 0);
    }

    #[test]
    fn one_frame_and_no_allocatable_memory() {
        let (regions, count) = canonical(&[RawRegion {
            start: 0x1000,
            len: PAGE_SIZE,
            kind: OwnershipKind::Usable,
        }])
        .unwrap();
        let mut available = [0u64; 1];
        let mut allocated = [0u64; 1];
        let mut allocator =
            BitmapAllocator::new(&regions[..count], &mut available, &mut allocated).unwrap();
        assert_eq!(allocator.allocate(), Some(PhysicalFrame::from_number(1)));
        assert!(allocator.allocate().is_none());
        assert_eq!(
            canonical(&[RawRegion {
                start: 0,
                len: PAGE_SIZE,
                kind: OwnershipKind::Reserved
            }]),
            Err(MapError::NoUsableMemory)
        );
    }

    #[test]
    fn high_mmio_does_not_inflate_allocator_domain() {
        let regions = [
            CanonicalRegion {
                frames: FrameRange::new(
                    PhysicalFrame::from_number(0),
                    PhysicalFrame::from_number(256),
                )
                .unwrap(),
                kind: OwnershipKind::Usable,
            },
            CanonicalRegion {
                frames: FrameRange::new(
                    PhysicalFrame::from_number(1 << 28),
                    PhysicalFrame::from_number((1 << 28) + 1),
                )
                .unwrap(),
                kind: OwnershipKind::Reserved,
            },
        ];
        let mut available = [0u64; 4];
        let mut allocated = [0u64; 4];
        let allocator = BitmapAllocator::new(&regions, &mut available, &mut allocated).unwrap();
        assert_eq!(allocator.accounting().total_represented, 256);
        assert_eq!(allocator.accounting().allocatable, 256);
        assert_eq!(allocator.accounting().reserved, 0);
    }

    #[test]
    fn generated_overlap_invariants_hold() {
        for usable_start in 0..8u64 {
            for reserved_start in 0..8u64 {
                let input = [
                    RawRegion {
                        start: usable_start * PAGE_SIZE,
                        len: 4 * PAGE_SIZE,
                        kind: OwnershipKind::Usable,
                    },
                    RawRegion {
                        start: reserved_start * PAGE_SIZE,
                        len: 2 * PAGE_SIZE,
                        kind: OwnershipKind::Reserved,
                    },
                ];
                if let Ok((regions, count)) = canonical(&input) {
                    for pair in regions[..count].windows(2) {
                        assert_eq!(pair[0].frames.end, pair[1].frames.start);
                        assert_ne!(pair[0].kind, pair[1].kind);
                    }
                }
            }
        }
    }
}
