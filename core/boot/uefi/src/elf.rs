//! A deliberately minimal ELF64 program-header loader.
//!
//! This parses only what is required to load a static, non-relocatable `ET_EXEC` x86-64
//! image: the header, and the `PT_LOAD` program headers. It does not handle dynamic
//! linking, relocations, or section headers, because the Malrynth kernel has none of those.
//!
//! Every field is read with explicit little-endian byte extraction from a `&[u8]` rather
//! than by casting to a `#[repr(C)]` struct. The file buffer has no alignment guarantee,
//! so casting would be undefined behaviour; bounds-checked slicing also makes a truncated
//! or hostile image a clean error instead of an out-of-bounds read.

/// Errors that can arise while parsing or loading an ELF image.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ElfError {
    /// The file is shorter than the structure being read.
    Truncated,
    /// The `\x7fELF` magic is absent.
    BadMagic,
    /// Not a 64-bit little-endian ELF.
    NotElf64Le,
    /// Not `ET_EXEC`; Malrynth's M0 kernel is a fixed-address executable.
    NotExecutable,
    /// Not `EM_X86_64`.
    WrongArchitecture,
    /// A `PT_LOAD` segment declares `p_filesz > p_memsz`, which is malformed.
    BadSegmentSize,
    /// The image contains no loadable segments.
    NoLoadableSegments,
}

const EI_NIDENT: usize = 16;
const ELF_MAGIC: [u8; 4] = [0x7F, b'E', b'L', b'F'];
const ELFCLASS64: u8 = 2;
const ELFDATA2LSB: u8 = 1;
const ET_EXEC: u16 = 2;
const EM_X86_64: u16 = 62;
const PT_LOAD: u32 = 1;

/// One loadable segment, already resolved into a copy plan.
#[derive(Debug, Clone, Copy)]
pub struct LoadSegment {
    /// Virtual (at M0, physical) address at which this segment must be placed.
    pub vaddr: u64,
    /// Offset of the segment's bytes within the file.
    pub file_offset: u64,
    /// Number of bytes present in the file.
    pub file_size: u64,
    /// Size of the segment in memory; bytes beyond `file_size` must be zeroed.
    pub mem_size: u64,
}

/// A parsed ELF64 image.
pub struct ElfImage<'a> {
    data: &'a [u8],
    /// The image entry point address.
    pub entry: u64,
    phoff: u64,
    phentsize: u16,
    phnum: u16,
}

impl<'a> ElfImage<'a> {
    /// Parses and validates the ELF header of `data`.
    pub fn parse(data: &'a [u8]) -> Result<Self, ElfError> {
        if data.len() < 64 {
            return Err(ElfError::Truncated);
        }
        if data[0..4] != ELF_MAGIC {
            return Err(ElfError::BadMagic);
        }
        if data[4] != ELFCLASS64 || data[5] != ELFDATA2LSB {
            return Err(ElfError::NotElf64Le);
        }
        if read_u16(data, EI_NIDENT)? != ET_EXEC {
            return Err(ElfError::NotExecutable);
        }
        if read_u16(data, EI_NIDENT + 2)? != EM_X86_64 {
            return Err(ElfError::WrongArchitecture);
        }

        Ok(Self {
            data,
            entry: read_u64(data, 24)?,
            phoff: read_u64(data, 32)?,
            phentsize: read_u16(data, 54)?,
            phnum: read_u16(data, 56)?,
        })
    }

    /// Returns the loadable segments, in file order.
    ///
    /// `out` must be large enough for all `PT_LOAD` segments; excess segments are an error
    /// rather than a silent truncation, because a partially loaded kernel is worse than a
    /// refused boot.
    pub fn load_segments(&self, out: &mut [LoadSegment]) -> Result<usize, ElfError> {
        let mut count = 0usize;

        for index in 0..self.phnum as u64 {
            let base = (self.phoff + index * self.phentsize as u64) as usize;

            if read_u32(self.data, base)? != PT_LOAD {
                continue;
            }

            let file_offset = read_u64(self.data, base + 8)?;
            let vaddr = read_u64(self.data, base + 16)?;
            let file_size = read_u64(self.data, base + 32)?;
            let mem_size = read_u64(self.data, base + 40)?;

            if file_size > mem_size {
                return Err(ElfError::BadSegmentSize);
            }
            // Verify the segment's bytes are actually present in the file before the
            // caller is invited to copy them.
            let end = file_offset
                .checked_add(file_size)
                .ok_or(ElfError::BadSegmentSize)?;
            if end > self.data.len() as u64 {
                return Err(ElfError::Truncated);
            }
            if count >= out.len() {
                return Err(ElfError::BadSegmentSize);
            }

            out[count] = LoadSegment {
                vaddr,
                file_offset,
                file_size,
                mem_size,
            };
            count += 1;
        }

        if count == 0 {
            return Err(ElfError::NoLoadableSegments);
        }
        Ok(count)
    }

    /// Returns the bytes of a segment as they appear in the file.
    pub fn segment_bytes(&self, segment: &LoadSegment) -> &'a [u8] {
        let start = segment.file_offset as usize;
        let end = start + segment.file_size as usize;
        &self.data[start..end]
    }
}

/// Computes the inclusive address span covered by `segments`.
///
/// Returns `(lowest_vaddr, highest_end)`. The loader allocates this whole span as one
/// contiguous region so that a single `AllocateType::Address` request either succeeds or
/// fails cleanly, rather than leaving the image half-placed.
#[must_use]
pub fn image_extent(segments: &[LoadSegment]) -> (u64, u64) {
    let mut low = u64::MAX;
    let mut high = 0u64;
    for segment in segments {
        low = low.min(segment.vaddr);
        high = high.max(segment.vaddr + segment.mem_size);
    }
    (low, high)
}

fn read_u16(data: &[u8], offset: usize) -> Result<u16, ElfError> {
    let bytes = data.get(offset..offset + 2).ok_or(ElfError::Truncated)?;
    Ok(u16::from_le_bytes([bytes[0], bytes[1]]))
}

fn read_u32(data: &[u8], offset: usize) -> Result<u32, ElfError> {
    let b = data.get(offset..offset + 4).ok_or(ElfError::Truncated)?;
    Ok(u32::from_le_bytes([b[0], b[1], b[2], b[3]]))
}

fn read_u64(data: &[u8], offset: usize) -> Result<u64, ElfError> {
    let b = data.get(offset..offset + 8).ok_or(ElfError::Truncated)?;
    Ok(u64::from_le_bytes([
        b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7],
    ]))
}
