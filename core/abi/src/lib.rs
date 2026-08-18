//! Malrynth boot handoff ABI.
//!
//! This crate defines the **only** contract between the Malrynth loader (`malboot`,
//! running under UEFI) and the Malrynth kernel (running on bare metal after
//! `ExitBootServices`). It is deliberately tiny, `#[repr(C)]`, and free of pointers to
//! firmware-owned memory that does not survive the handoff.
//!
//! # Stability
//!
//! Status: **EXPERIMENTAL**. This ABI is versioned by [`BOOT_ABI_VERSION`] and will change
//! freely until M3. The kernel *must* reject a [`BootInfo`] whose magic or version does not
//! match, because a silent mismatch here produces a corrupt kernel with no diagnostic.
//!
//! # Design rules
//!
//! * `#[repr(C)]` everywhere; no `Option<T>`, no enums without an explicit `repr`, no
//!   niche-optimised layouts. Presence is expressed with explicit count/flag fields.
//! * Fixed-width integers only. `usize` is banned in the handoff structs so the layout
//!   does not silently change if a 32-bit loader is ever added.
//! * All addresses are physical and 64-bit. At M0 the kernel runs identity-mapped, so
//!   physical and virtual coincide; from M1 the kernel builds its own page tables and this
//!   distinction becomes load-bearing. Fields are named `*_phys` to keep that honest.

#![cfg_attr(not(test), no_std)]
#![forbid(unsafe_op_in_unsafe_fn)]
#![deny(missing_docs)]

/// Magic value identifying a Malrynth boot handoff block: ASCII `"MALRYNTH"`, big-endian.
///
/// The kernel checks this first. A wrong value means the loader and kernel disagree about
/// the world and the only safe action is to stop.
pub const BOOT_MAGIC: u64 = 0x4D_41_4C_52_59_4E_54_48;

/// Version of the handoff ABI. Bumped on **any** layout change until the ABI is LOCKED.
pub const BOOT_ABI_VERSION: u32 = 1;

/// Physical address at which the loader places the kernel image.
///
/// M0 runs identity-mapped under the page tables UEFI left in place, so the kernel is
/// linked for, and loaded at, a fixed physical address. The loader requests exactly this
/// address from the firmware and fails loudly if the firmware refuses, rather than
/// silently relocating a non-relocatable image.
///
/// This constant disappears in M1, when the kernel moves to the higher half
/// (`0xFFFF_FFFF_8000_0000`) under page tables Malrynth builds itself.
pub const KERNEL_PHYS_BASE: u64 = 0x0000_0000_1000_0000;

/// Classification of a physical memory region, normalised from the UEFI memory map.
///
/// The loader collapses the ~15 UEFI memory types into the few distinctions the kernel
/// actually acts on. Anything the kernel must not touch becomes [`MemoryKind::Reserved`].
#[repr(u32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MemoryKind {
    /// Free for the kernel's physical allocator to claim.
    Usable = 0,
    /// Firmware-, hardware- or ACPI-reserved. Never allocate from this.
    Reserved = 1,
    /// Holds the loaded kernel image. Reserved until the kernel accounts for itself.
    KernelImage = 2,
    /// Holds the boot information block and the memory-region array.
    BootInfo = 3,
    /// UEFI runtime services code/data. Must be preserved if runtime services are kept.
    UefiRuntime = 4,
    /// ACPI tables that may be reclaimed after the kernel has parsed them.
    AcpiReclaimable = 5,
}

/// A single contiguous physical memory region.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct MemoryRegion {
    /// Physical start address, page-aligned.
    pub start_phys: u64,
    /// Length in bytes, a multiple of 4096.
    pub len: u64,
    /// What this region is.
    pub kind: MemoryKind,
    /// Explicit padding so the struct is 24 bytes with no implicit tail padding.
    pub _reserved: u32,
}

impl MemoryRegion {
    /// Physical address one past the end of this region.
    #[must_use]
    pub const fn end_phys(&self) -> u64 {
        self.start_phys + self.len
    }
}

/// Pixel encoding of the linear framebuffer, normalised from the UEFI GOP pixel format.
#[repr(u32)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PixelFormat {
    /// No framebuffer was available; all other framebuffer fields are zero.
    None = 0,
    /// 32-bit little-endian, byte order B, G, R, reserved.
    Bgrx8888 = 1,
    /// 32-bit little-endian, byte order R, G, B, reserved.
    Rgbx8888 = 2,
}

/// A linear framebuffer discovered via the UEFI Graphics Output Protocol.
///
/// Present only when [`BootInfo::framebuffer_present`] is non-zero. M0 discovers and
/// reports the framebuffer but deliberately does **not** draw to it; graphics belong to M6.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct Framebuffer {
    /// Physical base address of the framebuffer.
    pub base_phys: u64,
    /// Total size in bytes.
    pub size: u64,
    /// Visible width in pixels.
    pub width: u32,
    /// Visible height in pixels.
    pub height: u32,
    /// Pixels per scanline, which may exceed `width` due to padding.
    pub stride_px: u32,
    /// Pixel encoding.
    pub format: PixelFormat,
}

/// The boot information block handed from `malboot` to the Malrynth kernel.
///
/// The loader allocates this in memory typed [`MemoryKind::BootInfo`], which survives
/// `ExitBootServices`, and passes a pointer to it in `rdi` per the SysV AMD64 ABI.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct BootInfo {
    /// Must equal [`BOOT_MAGIC`].
    pub magic: u64,
    /// Must equal [`BOOT_ABI_VERSION`].
    pub abi_version: u32,
    /// `size_of::<BootInfo>()`, so a future kernel can detect a shorter/longer block.
    pub struct_size: u32,

    /// Physical address of an array of [`MemoryRegion`] of length [`Self::regions_len`].
    pub regions_phys: u64,
    /// Number of entries in the memory-region array.
    pub regions_len: u64,
    /// Sum of the lengths of all [`MemoryKind::Usable`] regions, in bytes.
    pub usable_bytes: u64,

    /// Non-zero if [`Self::framebuffer`] is valid.
    pub framebuffer_present: u32,
    /// Explicit padding to keep the following `u64` naturally aligned.
    pub _pad0: u32,
    /// Framebuffer description; meaningful only when [`Self::framebuffer_present`] is set.
    pub framebuffer: Framebuffer,

    /// Physical base address at which the kernel image was loaded.
    pub kernel_phys_base: u64,
    /// Size in bytes of the loaded kernel image.
    pub kernel_size: u64,

    /// Physical address of the UEFI system table, or 0 if unavailable.
    ///
    /// Retained for later ACPI/RSDP discovery. M0 records it and does not dereference it.
    pub uefi_system_table_phys: u64,
    /// Physical address of the ACPI 2.0+ RSDP, or 0 if it was not found.
    pub acpi_rsdp_phys: u64,
}

impl BootInfo {
    /// Returns `true` if the magic, version and struct size all match this build.
    ///
    /// The kernel calls this before touching any other field. Returning `false` means the
    /// loader and kernel were built from incompatible sources.
    #[must_use]
    pub fn is_valid(&self) -> bool {
        self.magic == BOOT_MAGIC
            && self.abi_version == BOOT_ABI_VERSION
            && self.struct_size as usize == core::mem::size_of::<Self>()
    }
}

/// The signature of the Malrynth kernel entry point.
///
/// `extern "sysv64"` is stated explicitly rather than relying on the target default, so the
/// calling convention is part of the contract and cannot drift with a target change.
///
/// The function is `unsafe` because calling it transfers permanent control of the machine:
/// the caller must guarantee that `boot_info` is valid and outlives the call, that
/// `ExitBootServices` has completed, and that no other CPU is running.
pub type KernelEntry = unsafe extern "sysv64" fn(boot_info: *const BootInfo) -> !;

#[cfg(test)]
mod tests {
    use super::*;

    // These assertions are the point of the crate: if the handoff layout changes by
    // accident, the build must fail rather than produce a kernel that reads garbage.

    #[test]
    fn magic_is_ascii_malrynth() {
        assert_eq!(&BOOT_MAGIC.to_be_bytes(), b"MALRYNTH");
    }

    #[test]
    fn layout_is_stable() {
        assert_eq!(core::mem::size_of::<MemoryRegion>(), 24);
        assert_eq!(core::mem::align_of::<MemoryRegion>(), 8);
        assert_eq!(core::mem::size_of::<Framebuffer>(), 32);
        assert_eq!(core::mem::size_of::<BootInfo>(), 112);
        assert_eq!(core::mem::align_of::<BootInfo>(), 8);
    }

    #[test]
    fn validity_check_rejects_wrong_magic() {
        let mut bi = zeroed_boot_info();
        assert!(bi.is_valid());
        bi.magic = 0;
        assert!(!bi.is_valid());
    }

    #[test]
    fn validity_check_rejects_wrong_version() {
        let mut bi = zeroed_boot_info();
        bi.abi_version = BOOT_ABI_VERSION + 1;
        assert!(!bi.is_valid());
    }

    #[test]
    fn region_end_is_start_plus_len() {
        let r = MemoryRegion {
            start_phys: 0x1000,
            len: 0x2000,
            kind: MemoryKind::Usable,
            _reserved: 0,
        };
        assert_eq!(r.end_phys(), 0x3000);
    }

    fn zeroed_boot_info() -> BootInfo {
        BootInfo {
            magic: BOOT_MAGIC,
            abi_version: BOOT_ABI_VERSION,
            struct_size: core::mem::size_of::<BootInfo>() as u32,
            regions_phys: 0,
            regions_len: 0,
            usable_bytes: 0,
            framebuffer_present: 0,
            _pad0: 0,
            framebuffer: Framebuffer {
                base_phys: 0,
                size: 0,
                width: 0,
                height: 0,
                stride_px: 0,
                format: PixelFormat::None,
            },
            kernel_phys_base: KERNEL_PHYS_BASE,
            kernel_size: 0,
            uefi_system_table_phys: 0,
            acpi_rsdp_phys: 0,
        }
    }
}
