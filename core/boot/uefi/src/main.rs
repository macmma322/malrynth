//! Malrynth Boot (`malboot`) — the UEFI loader.
//!
//! # Responsibility
//!
//! `malboot` is the only Malrynth component permitted to call UEFI boot services. It:
//!
//! 1. reads the kernel ELF image from the EFI System Partition,
//! 2. places it at the fixed physical address the kernel was linked for,
//! 3. discovers the framebuffer and the ACPI RSDP,
//! 4. allocates the [`BootInfo`] handoff block in memory that survives the handoff,
//! 5. calls `ExitBootServices`, taking ownership of the machine from the firmware,
//! 6. normalises the final UEFI memory map into the Malrynth memory-region format,
//! 7. enters the kernel and never returns.
//!
//! # Boundary
//!
//! Everything firmware-shaped stops here. The kernel never sees a UEFI type, a UEFI
//! calling convention, or a UEFI memory-type number — only [`malrynth_abi`]. That is what
//! makes UEFI a *supported boot environment* rather than part of Malrynth's architecture,
//! and it is what will let a non-UEFI boot path be added later without touching the kernel.
//!
//! # Ordering constraint
//!
//! All allocation must happen **before** `ExitBootServices`. After that call, no firmware
//! service exists, so the `BootInfo` block and the memory-region array are allocated in
//! advance and only *filled in* afterwards.

#![no_main]
#![no_std]

extern crate alloc;

mod elf;

use alloc::vec::Vec;
use core::mem::size_of;
use malrynth_abi::{
    BOOT_ABI_VERSION, BOOT_MAGIC, BootInfo, Framebuffer, KERNEL_PHYS_BASE, KernelEntry, MemoryKind,
    MemoryRegion, PixelFormat,
};
use uefi::boot::{self, AllocateType, MemoryType};
use uefi::mem::memory_map::MemoryMap;
use uefi::prelude::*;
use uefi::proto::console::gop::{GraphicsOutput, PixelFormat as GopFormat};
use uefi::{Status, cstr16};

/// Where the kernel image is expected on the EFI System Partition.
const KERNEL_PATH: &uefi::CStr16 = cstr16!("\\malrynth\\kernel.elf");

/// Upper bound on `PT_LOAD` segments. The Malrynth kernel has three (text, rodata, data).
const MAX_LOAD_SEGMENTS: usize = 16;

/// Upper bound on normalised memory regions handed to the kernel.
///
/// QEMU/OVMF typically reports 30–60 descriptors. The array is allocated for this many
/// before `ExitBootServices` because it cannot be grown afterwards; overflow is reported
/// rather than silently truncating the kernel's view of physical memory.
const MAX_MEMORY_REGIONS: usize = 256;

#[entry]
fn main() -> Status {
    uefi::helpers::init().expect("UEFI helper initialisation failed");

    uefi::println!("Malrynth Boot v{} (UEFI x86_64)", env!("CARGO_PKG_VERSION"));

    match boot_malrynth() {
        // `Infallible` is uninhabited: this arm is unreachable by construction.
        Ok(never) => match never {},
        Err(status) => {
            uefi::println!("malboot: FATAL: {status:?}");
            uefi::println!("MALRYNTH_M0_BOOT_FAIL");
            status
        }
    }
}

/// Loads and enters the kernel. Returns only on failure.
fn boot_malrynth() -> Result<core::convert::Infallible, Status> {
    // ---- 1. Read the kernel image from the ESP ------------------------------------
    let kernel_bytes = read_kernel_image()?;
    uefi::println!("malboot: kernel.elf loaded, {} bytes", kernel_bytes.len());

    // ---- 2. Parse and place the kernel --------------------------------------------
    let image = elf::ElfImage::parse(&kernel_bytes).map_err(|e| {
        uefi::println!("malboot: ELF rejected: {e:?}");
        Status::LOAD_ERROR
    })?;

    let mut segments = [elf::LoadSegment {
        vaddr: 0,
        file_offset: 0,
        file_size: 0,
        mem_size: 0,
    }; MAX_LOAD_SEGMENTS];
    let segment_count = image.load_segments(&mut segments).map_err(|e| {
        uefi::println!("malboot: bad program headers: {e:?}");
        Status::LOAD_ERROR
    })?;
    let segments = &segments[..segment_count];

    let (low, high) = elf::image_extent(segments);
    if low != KERNEL_PHYS_BASE {
        uefi::println!(
            "malboot: kernel linked at {low:#x}, expected {KERNEL_PHYS_BASE:#x} -- \
             loader and kernel disagree"
        );
        return Err(Status::LOAD_ERROR);
    }

    let image_size = high - low;
    let page_count = pages_for(image_size);

    // The kernel is not relocatable at M0, so this must be the exact address or nothing.
    // AllocateType::Address makes the firmware refuse rather than quietly relocate.
    boot::allocate_pages(
        AllocateType::Address(low),
        MemoryType::LOADER_DATA,
        page_count,
    )
    .map_err(|e| {
        uefi::println!(
            "malboot: firmware refused {page_count} pages at {low:#x}: {:?}",
            e.status()
        );
        e.status()
    })?;

    // SAFETY: the firmware just granted exclusive ownership of `page_count` pages starting
    // at `low`, and every segment lies inside `[low, high)` by construction of
    // `image_extent`. The destination cannot overlap `kernel_bytes`, which the firmware
    // allocated separately.
    unsafe {
        core::ptr::write_bytes(low as *mut u8, 0, page_count * 4096);
        for segment in segments {
            let src = image.segment_bytes(segment);
            core::ptr::copy_nonoverlapping(src.as_ptr(), segment.vaddr as *mut u8, src.len());
            // Bytes between file_size and mem_size (.bss) are already zero from above.
        }
    }
    uefi::println!(
        "malboot: kernel placed at {low:#x}..{high:#x} ({} KiB), entry {:#x}",
        image_size / 1024,
        image.entry
    );

    // ---- 3. Discover firmware-provided facts --------------------------------------
    let framebuffer = discover_framebuffer();
    let rsdp = find_acpi_rsdp();

    // ---- 4. Pre-allocate the handoff block (must precede ExitBootServices) ---------
    let regions_ptr = allocate_zeroed::<MemoryRegion>(MAX_MEMORY_REGIONS)?;
    let info_ptr = allocate_zeroed::<BootInfo>(1)?;

    let system_table = uefi::table::system_table_raw().map_or(0, |p| p.as_ptr() as u64);

    uefi::println!("malboot: exiting boot services");

    // ---- 5. Point of no return ----------------------------------------------------
    // After this call no UEFI service exists: no allocation, no console, no `println!`.
    // Everything below operates only on memory allocated above.
    //
    // SAFETY: all firmware-owned resources this loader opened have been dropped, and no
    // further boot service is invoked after this point.
    let memory_map = unsafe { boot::exit_boot_services(Some(MemoryType::LOADER_DATA)) };

    // ---- 6. Normalise the memory map ----------------------------------------------
    // SAFETY: `regions_ptr` was allocated for MAX_MEMORY_REGIONS entries and zeroed; it
    // lives in LOADER_DATA, which survives ExitBootServices.
    let regions = unsafe { core::slice::from_raw_parts_mut(regions_ptr, MAX_MEMORY_REGIONS) };
    let (region_count, usable_bytes) = normalise_memory_map(&memory_map, regions, low, high);

    // ---- 7. Fill the handoff block and enter the kernel ---------------------------
    let info = BootInfo {
        magic: BOOT_MAGIC,
        abi_version: BOOT_ABI_VERSION,
        struct_size: size_of::<BootInfo>() as u32,
        regions_phys: regions_ptr as u64,
        regions_len: region_count as u64,
        usable_bytes,
        framebuffer_present: u32::from(framebuffer.is_some()),
        _pad0: 0,
        framebuffer: framebuffer.unwrap_or(Framebuffer {
            base_phys: 0,
            size: 0,
            width: 0,
            height: 0,
            stride_px: 0,
            format: PixelFormat::None,
        }),
        kernel_phys_base: low,
        kernel_size: image_size,
        uefi_system_table_phys: system_table,
        acpi_rsdp_phys: rsdp,
    };

    // SAFETY: `info_ptr` is a valid, zeroed, correctly aligned allocation for one
    // `BootInfo` in LOADER_DATA memory, which outlives this loader.
    unsafe { core::ptr::write(info_ptr, info) };

    // SAFETY: `image.entry` is the entry address of an ELF the firmware confirmed we placed
    // at exactly `low`, and the kernel declares this exact signature via
    // `malrynth_abi::KernelEntry`. The kernel never returns.
    let entry: KernelEntry = unsafe { core::mem::transmute(image.entry as *const ()) };
    unsafe { entry(info_ptr) }
}

/// Reads `\malrynth\kernel.elf` from the volume this loader was booted from.
fn read_kernel_image() -> Result<Vec<u8>, Status> {
    let fs = boot::get_image_file_system(boot::image_handle()).map_err(|e| {
        uefi::println!("malboot: cannot open boot filesystem: {:?}", e.status());
        e.status()
    })?;

    uefi::fs::FileSystem::new(fs)
        .read(uefi::fs::Path::new(KERNEL_PATH))
        .map_err(|e| {
            uefi::println!("malboot: cannot read {KERNEL_PATH}: {e:?}");
            Status::NOT_FOUND
        })
}

/// Allocates `count` zeroed, aligned `T` in memory that survives `ExitBootServices`.
fn allocate_zeroed<T>(count: usize) -> Result<*mut T, Status> {
    let bytes = size_of::<T>() * count;
    let ptr = boot::allocate_pages(
        AllocateType::AnyPages,
        MemoryType::LOADER_DATA,
        pages_for(bytes as u64) as usize,
    )
    .map_err(|e| {
        uefi::println!(
            "malboot: allocation of {bytes} bytes failed: {:?}",
            e.status()
        );
        e.status()
    })?;

    // SAFETY: the firmware granted at least `bytes` bytes at `ptr`. Page allocations are
    // 4096-byte aligned, which satisfies the alignment of every type used here.
    unsafe {
        core::ptr::write_bytes(ptr.as_ptr(), 0, pages_for(bytes as u64) as usize * 4096);
    }
    Ok(ptr.as_ptr().cast())
}

/// Number of 4 KiB pages required to hold `bytes`.
const fn pages_for(bytes: u64) -> usize {
    bytes.div_ceil(4096) as usize
}

/// Converts the final UEFI memory map into Malrynth memory regions.
///
/// Runs **after** `ExitBootServices`, so it must not allocate, log, or call any service.
/// Returns the number of regions written and the total usable byte count.
fn normalise_memory_map(
    memory_map: &impl MemoryMap,
    out: &mut [MemoryRegion],
    kernel_start: u64,
    kernel_end: u64,
) -> (usize, u64) {
    let mut count = 0usize;
    let mut usable_bytes = 0u64;

    for descriptor in memory_map.entries() {
        if count >= out.len() {
            break; // Reported by the kernel as a region count at the cap.
        }

        let start = descriptor.phys_start;
        let len = descriptor.page_count * 4096;

        // Classify. The kernel image sits inside a LOADER_DATA range we allocated, so it is
        // reclassified here to stop the kernel's future allocator from handing out the
        // memory it is executing from.
        let kind = if start < kernel_end && (start + len) > kernel_start {
            MemoryKind::KernelImage
        } else {
            match descriptor.ty {
                MemoryType::CONVENTIONAL => MemoryKind::Usable,
                // Boot-services code/data become free once the firmware is gone, but M0
                // does not reclaim them: doing so requires knowing that nothing retained a
                // pointer into them. Reclamation is an M1 decision with a test behind it.
                MemoryType::BOOT_SERVICES_CODE | MemoryType::BOOT_SERVICES_DATA => {
                    MemoryKind::Reserved
                }
                MemoryType::LOADER_CODE | MemoryType::LOADER_DATA => MemoryKind::BootInfo,
                MemoryType::RUNTIME_SERVICES_CODE | MemoryType::RUNTIME_SERVICES_DATA => {
                    MemoryKind::UefiRuntime
                }
                MemoryType::ACPI_RECLAIM => MemoryKind::AcpiReclaimable,
                _ => MemoryKind::Reserved,
            }
        };

        if kind == MemoryKind::Usable {
            usable_bytes += len;
        }

        out[count] = MemoryRegion {
            start_phys: start,
            len,
            kind,
            _reserved: 0,
        };
        count += 1;
    }

    (count, usable_bytes)
}

/// Queries the Graphics Output Protocol for a linear framebuffer.
///
/// Returns `None` if no GOP is present, which is a legitimate configuration (a headless
/// server, or QEMU with `-display none`). M0 reports the framebuffer and never draws to it.
fn discover_framebuffer() -> Option<Framebuffer> {
    let handle = boot::get_handle_for_protocol::<GraphicsOutput>().ok()?;
    let mut gop = boot::open_protocol_exclusive::<GraphicsOutput>(handle).ok()?;

    let mode = gop.current_mode_info();
    let (width, height) = mode.resolution();
    let format = match mode.pixel_format() {
        GopFormat::Bgr => PixelFormat::Bgrx8888,
        GopFormat::Rgb => PixelFormat::Rgbx8888,
        // BitMask and BltOnly have no linear layout Malrynth can describe yet.
        _ => return None,
    };

    let mut fb = gop.frame_buffer();
    Some(Framebuffer {
        base_phys: fb.as_mut_ptr() as u64,
        size: fb.size() as u64,
        width: width as u32,
        height: height as u32,
        stride_px: mode.stride() as u32,
        format,
    })
}

/// Locates the ACPI 2.0+ RSDP in the UEFI configuration table.
///
/// M0 records the address and does not parse it; ACPI enumeration is M4. Capturing it now
/// costs nothing and avoids needing the firmware alive later to find it.
fn find_acpi_rsdp() -> u64 {
    uefi::system::with_config_table(|entries| {
        entries
            .iter()
            .find(|entry| entry.guid == uefi::table::cfg::ConfigTableEntry::ACPI2_GUID)
            .map_or(0, |entry| entry.address as u64)
    })
}
