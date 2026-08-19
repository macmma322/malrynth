//! The Malrynth kernel — M0.
//!
//! # Scope of M0
//!
//! M0 proves exactly one thing: that firmware can hand control to Malrynth Boot, which can
//! load and enter a genuinely separate Malrynth kernel image on bare metal, and that the
//! kernel can validate the handoff and report diagnostics.
//!
//! There is deliberately **no** memory manager, allocator, interrupt handling, scheduler,
//! process model, filesystem, network stack or graphics here. Those are M1–M6. Adding any
//! of them now would be scaffolding without a specification behind it.
//!
//! # State on entry
//!
//! * Long mode (64-bit), CPL 0, interrupts disabled by the loader.
//! * Identity-mapped address space inherited from UEFI; the kernel runs at the physical
//!   address it was linked for. M1 replaces this with page tables Malrynth builds itself.
//! * `ExitBootServices` has been called; no firmware boot services remain callable.
//! * `rdi` holds a `*const BootInfo` per the SysV AMD64 calling convention.

#![no_std]
#![no_main]
#![forbid(unsafe_op_in_unsafe_fn)]
#![deny(missing_docs)]

mod arch;
mod debug;
mod serial;

use arch::x86_64::halt_forever;
use core::panic::PanicInfo;
use malrynth_abi::{BootInfo, KERNEL_PHYS_BASE, MemoryKind, PixelFormat};

/// Kernel version, sourced from the crate manifest so it cannot drift from Cargo.
const VERSION: &str = concat!(env!("CARGO_PKG_VERSION"), "-dev");

/// Emitted on the success path and asserted verbatim by the boot smoke test.
///
/// The test must never pass merely because QEMU exited. It passes only if this exact
/// string is observed on the serial console.
///
/// Gated out under `panic-test`, where the kernel is expected to panic and must never be
/// able to emit a success marker even by accident.
#[cfg(not(feature = "panic-test"))]
const BOOT_OK_MARKER: &str = "MALRYNTH_M0_BOOT_OK";

/// Emitted on any fault path so the smoke test can fail fast rather than wait for timeout.
const BOOT_FAIL_MARKER: &str = "MALRYNTH_M0_BOOT_FAIL";

unsafe extern "C" {
    /// Start of `.bss`, provided by the linker script.
    static __bss_start: u8;
    /// End of `.bss`, provided by the linker script.
    static __bss_end: u8;
    /// Start of the kernel image, provided by the linker script.
    static __kernel_start: u8;
    /// End of the kernel image, provided by the linker script.
    static __kernel_end: u8;
}

/// The Malrynth kernel entry point.
///
/// Placed in `.text.entry` so the linker script can guarantee it sits at the very start of
/// the text segment, keeping the entry address stable and easy to verify in a disassembly.
///
/// # Safety
///
/// Called exactly once by Malrynth Boot with a valid `BootInfo` pointer, on a single CPU,
/// with interrupts disabled. It never returns.
#[unsafe(no_mangle)]
#[unsafe(link_section = ".text.entry")]
pub unsafe extern "sysv64" fn _start(boot_info: *const BootInfo) -> ! {
    // The loader does not zero .bss, so the kernel must do it before touching any static.
    // SAFETY: single-threaded entry; the symbols come from the linker script and bound a
    // region that belongs exclusively to this image.
    unsafe { zero_bss() };

    // SAFETY: first code to touch the UART, on the single early-boot execution context.
    unsafe { serial::init() };

    println!();
    println!("MALRYNTH KERNEL");
    println!("version: {VERSION}");
    println!("arch: x86_64");
    println!("boot: UEFI");
    println!();

    // Refuse to proceed on a handoff we do not understand. A silent mismatch here would
    // produce a kernel reading arbitrary memory as structured data.
    if boot_info.is_null() {
        println!("FATAL: boot info pointer is null");
        println!("{BOOT_FAIL_MARKER}");
        halt_forever();
    }

    // SAFETY: the loader allocated this block in BootInfo-typed memory that survives
    // ExitBootServices, and guarantees it outlives the kernel. Non-null was just checked.
    let info = unsafe { &*boot_info };

    if !info.is_valid() {
        println!(
            "FATAL: boot info rejected (magic={:#018x} version={} size={})",
            info.magic, info.abi_version, info.struct_size
        );
        println!("{BOOT_FAIL_MARKER}");
        halt_forever();
    }

    // The kernel is not relocatable at M0; if the loader placed it elsewhere, every
    // absolute address in this image is wrong and continuing would corrupt memory.
    if info.kernel_phys_base != KERNEL_PHYS_BASE {
        println!(
            "FATAL: kernel loaded at {:#018x}, linked for {KERNEL_PHYS_BASE:#018x}",
            info.kernel_phys_base
        );
        println!("{BOOT_FAIL_MARKER}");
        halt_forever();
    }

    report_memory_map(info);
    report_framebuffer(info);

    // The loader calls ExitBootServices before entering the kernel, so reaching this point
    // at all is the proof. It is reported here because the kernel owns the console.
    println!("boot services exited");

    report_image_extent(info);

    println!("kernel entered successfully");

    // The panic path is a correctness-critical path that is never exercised by a healthy
    // boot, so it is tested deliberately rather than assumed to work. Enabled only by the
    // `panic-test` cargo feature, which is never set for a shipped kernel.
    #[cfg(feature = "panic-test")]
    {
        println!();
        println!("panic-test: deliberately panicking to exercise the panic path");
        provoke_panic();
    }

    // M0 terminates here by design. M1 replaces this with physical memory management,
    // paging, exceptions, interrupts, timers and SMP bring-up.
    #[cfg(not(feature = "panic-test"))]
    {
        println!();
        println!("{BOOT_OK_MARKER}");
        halt_forever();
    }
}

/// Reports the normalised memory map handed over by the loader.
fn report_memory_map(info: &BootInfo) {
    if info.regions_len == 0 {
        println!("memory map MISSING");
        return;
    }

    println!(
        "memory map received ({} regions, {} MiB usable)",
        info.regions_len,
        info.usable_bytes / (1024 * 1024)
    );

    // SAFETY: the loader guarantees `regions_phys` points to `regions_len` initialised
    // `MemoryRegion` values in BootInfo-typed memory, which survives ExitBootServices and
    // is identity-mapped. The count is bounded by the loader's own allocation.
    let regions = unsafe {
        core::slice::from_raw_parts(
            info.regions_phys as *const malrynth_abi::MemoryRegion,
            info.regions_len as usize,
        )
    };

    let mut usable = 0usize;
    let mut reserved = 0usize;
    for region in regions {
        match region.kind {
            MemoryKind::Usable => usable += 1,
            _ => reserved += 1,
        }
    }
    println!("  usable regions: {usable}, non-usable regions: {reserved}");

    // Largest usable region: the first thing M1's physical allocator will want.
    if let Some(largest) = regions
        .iter()
        .filter(|r| r.kind == MemoryKind::Usable)
        .max_by_key(|r| r.len)
    {
        println!(
            "  largest usable: {:#018x}..{:#018x} ({} MiB)",
            largest.start_phys,
            largest.end_phys(),
            largest.len / (1024 * 1024)
        );
    }
}

/// Reports the framebuffer, if the loader discovered one.
///
/// M0 reports and does not draw. Graphics belong to M6, and drawing here would create a
/// dependency on a framebuffer layout that has not been specified.
fn report_framebuffer(info: &BootInfo) {
    if info.framebuffer_present == 0 {
        println!("framebuffer NOT PRESENT");
        return;
    }

    let fb = &info.framebuffer;
    let format = match fb.format {
        PixelFormat::Bgrx8888 => "BGRX8888",
        PixelFormat::Rgbx8888 => "RGBX8888",
        PixelFormat::None => "none",
    };
    println!(
        "framebuffer discovered ({}x{}, stride {} px, {}, {:#018x})",
        fb.width, fb.height, fb.stride_px, format, fb.base_phys
    );
}

/// Reports where the kernel image actually landed, for size budgeting and symbolisation.
fn report_image_extent(info: &BootInfo) {
    // Only the addresses of these linker-defined symbols are taken, never their contents,
    // so no unsafe is required: `&raw const` does not read the (nonexistent) value.
    let (start, end) = (
        (&raw const __kernel_start) as u64,
        (&raw const __kernel_end) as u64,
    );
    println!(
        "kernel image: {:#018x}..{:#018x} ({} KiB, {} KiB loaded)",
        start,
        end,
        (end - start) / 1024,
        info.kernel_size / 1024
    );
}

/// Calls through two frames so the test backtrace has something to walk.
#[cfg(feature = "panic-test")]
#[inline(never)]
fn provoke_panic() -> ! {
    #[inline(never)]
    fn inner() -> ! {
        panic!("panic-test: this panic is intentional");
    }
    inner()
}

/// Zeroes the `.bss` section.
///
/// # Safety
///
/// Must be called exactly once, before any static is read, on the single early-boot CPU.
unsafe fn zero_bss() {
    // SAFETY: the linker script places `__bss_start`/`__bss_end` around a contiguous
    // region owned solely by this image. Writing zeroes over it is the defined
    // initialisation of `.bss`, and no static has been read yet per the fn contract.
    unsafe {
        let start = (&raw const __bss_start) as *mut u8;
        let end = &raw const __bss_end;
        let len = end as usize - start as usize;
        core::ptr::write_bytes(start, 0, len);
    }
}

/// Kernel panic handler.
///
/// Prints the panic location and message to serial, emits the failure marker so CI fails
/// immediately rather than on timeout, and halts. It must not allocate, must not unwind,
/// and must not itself panic.
#[panic_handler]
fn panic(info: &PanicInfo<'_>) -> ! {
    let backtrace = debug::capture();

    println!();
    println!("KERNEL PANIC");
    if let Some(location) = info.location() {
        println!(
            "  at {}:{}:{}",
            location.file(),
            location.line(),
            location.column()
        );
    }
    println!("  {}", info.message());

    // Captured at handler entry, before any printing perturbs the stack, so the trace
    // reflects the panic site rather than the panic handler's own frames.
    debug::print(&backtrace);

    println!("{BOOT_FAIL_MARKER}");
    halt_forever();
}
