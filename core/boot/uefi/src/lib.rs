#![no_std]

use malrynth_abi::{MemoryKind, MemoryRegion};

pub const PAGE_SIZE: u64 = 4096;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct RawMemoryRegion {
    pub start_phys: u64,
    pub page_count: u64,
    pub kind: MemoryKind,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MemoryMapError {
    TooManyRegions,
    ByteLengthOverflow,
    RegionEndOverflow,
    UsableBytesOverflow,
}

impl MemoryMapError {
    /// A reason string for the loader console. `Debug` is not enough here: this is the last
    /// thing printed before a refused boot, and it is read by a human.
    #[must_use]
    pub const fn describe(&self) -> &'static str {
        match self {
            Self::TooManyRegions => "firmware memory map does not fit the handoff array",
            Self::ByteLengthOverflow => "region page count overflows a byte length",
            Self::RegionEndOverflow => "region end address overflows 64 bits",
            Self::UsableBytesOverflow => "total usable bytes overflow 64 bits",
        }
    }
}

/// Descriptors reserved for the churn between the pre-flight snapshot and `ExitBootServices`.
///
/// The map must be checked while the UEFI console still exists, because after
/// `ExitBootServices` the loader cannot report anything. But reading the map allocates, and
/// freeing that allocation and exiting boot services both perturb the map again, so the
/// count observed at pre-flight is not the final count. This is the margin that makes the
/// pre-flight verdict hold at `ExitBootServices` rather than merely at the moment it was
/// taken. Firmware adds descriptors in ones and twos here; sixteen is generous.
pub const MEMORY_MAP_HEADROOM: usize = 16;

/// Decides, before `ExitBootServices`, whether the firmware map can still fit afterwards.
///
/// Separated from the UEFI glue so the decision is testable on the host: it is the check
/// that keeps an oversized map from reaching the point where it can no longer be reported.
pub const fn memory_map_fits(
    observed: usize,
    capacity: usize,
    headroom: usize,
) -> Result<(), MemoryMapError> {
    match observed.checked_add(headroom) {
        Some(required) if required <= capacity => Ok(()),
        _ => Err(MemoryMapError::TooManyRegions),
    }
}

pub fn normalise_memory_regions(
    regions: impl IntoIterator<Item = RawMemoryRegion>,
    out: &mut [MemoryRegion],
    kernel_start: u64,
    kernel_end: u64,
) -> Result<(usize, u64), MemoryMapError> {
    let mut count = 0usize;
    let mut usable_bytes = 0u64;

    for descriptor in regions {
        if count == out.len() {
            return Err(MemoryMapError::TooManyRegions);
        }
        let len = descriptor
            .page_count
            .checked_mul(PAGE_SIZE)
            .ok_or(MemoryMapError::ByteLengthOverflow)?;
        let end = descriptor
            .start_phys
            .checked_add(len)
            .ok_or(MemoryMapError::RegionEndOverflow)?;
        let kind = if descriptor.start_phys < kernel_end && end > kernel_start {
            MemoryKind::KernelImage
        } else {
            descriptor.kind
        };
        if kind == MemoryKind::Usable {
            usable_bytes = usable_bytes
                .checked_add(len)
                .ok_or(MemoryMapError::UsableBytesOverflow)?;
        }
        out[count] = MemoryRegion {
            start_phys: descriptor.start_phys,
            len,
            kind,
            _reserved: 0,
        };
        count += 1;
    }
    Ok((count, usable_bytes))
}

#[cfg(test)]
mod tests {
    use super::*;

    const EMPTY: MemoryRegion = MemoryRegion {
        start_phys: 0,
        len: 0,
        kind: MemoryKind::Reserved,
        _reserved: 0,
    };

    #[test]
    fn preflight_accepts_a_map_that_still_fits_with_headroom() {
        assert_eq!(memory_map_fits(0, 256, 16), Ok(()));
        assert_eq!(memory_map_fits(239, 256, 16), Ok(()));
        // Exactly at the limit: 240 + 16 == 256. A map this size is legitimate, not truncated.
        assert_eq!(memory_map_fits(240, 256, 16), Ok(()));
    }

    #[test]
    fn preflight_refuses_a_map_that_would_not_survive_boot_service_churn() {
        // 241 + 16 == 257. Still fits the array today, but not with room for churn, and the
        // overflow would then land after ExitBootServices where it cannot be reported.
        assert_eq!(
            memory_map_fits(241, 256, 16),
            Err(MemoryMapError::TooManyRegions)
        );
        assert_eq!(
            memory_map_fits(257, 256, 16),
            Err(MemoryMapError::TooManyRegions)
        );
    }

    #[test]
    fn preflight_addition_cannot_wrap() {
        assert_eq!(
            memory_map_fits(usize::MAX, 256, 16),
            Err(MemoryMapError::TooManyRegions)
        );
        assert_eq!(
            memory_map_fits(1, usize::MAX, usize::MAX),
            Err(MemoryMapError::TooManyRegions)
        );
    }

    #[test]
    fn every_error_has_a_distinct_human_reason() {
        let all = [
            MemoryMapError::TooManyRegions,
            MemoryMapError::ByteLengthOverflow,
            MemoryMapError::RegionEndOverflow,
            MemoryMapError::UsableBytesOverflow,
        ];
        for (i, a) in all.iter().enumerate() {
            assert!(!a.describe().is_empty());
            for b in &all[i + 1..] {
                assert_ne!(a.describe(), b.describe());
            }
        }
    }

    #[test]
    fn rejects_input_larger_than_handoff_capacity() {
        let exact = [RawMemoryRegion {
            start_phys: 0,
            page_count: 1,
            kind: MemoryKind::Reserved,
        }; 256];
        let mut exact_output = [EMPTY; 256];
        assert_eq!(
            normalise_memory_regions(exact, &mut exact_output, 0x1000_0000, 0x1001_0000),
            Ok((256, 0))
        );

        let input = [RawMemoryRegion {
            start_phys: 0,
            page_count: 1,
            kind: MemoryKind::Reserved,
        }; 257];
        let mut output = [EMPTY; 256];
        assert_eq!(
            normalise_memory_regions(input, &mut output, 0x1000_0000, 0x1001_0000),
            Err(MemoryMapError::TooManyRegions)
        );
    }

    #[test]
    fn rejects_byte_and_end_overflow() {
        let mut output = [EMPTY; 1];
        assert_eq!(
            normalise_memory_regions(
                [RawMemoryRegion {
                    start_phys: 0,
                    page_count: u64::MAX,
                    kind: MemoryKind::Usable,
                }],
                &mut output,
                0,
                0
            ),
            Err(MemoryMapError::ByteLengthOverflow)
        );
        assert_eq!(
            normalise_memory_regions(
                [RawMemoryRegion {
                    start_phys: u64::MAX - PAGE_SIZE + 1,
                    page_count: 1,
                    kind: MemoryKind::Usable,
                }],
                &mut output,
                0,
                0
            ),
            Err(MemoryMapError::RegionEndOverflow)
        );
    }
}
