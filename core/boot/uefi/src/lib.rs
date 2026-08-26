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
    fn rejects_input_larger_than_handoff_capacity() {
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
