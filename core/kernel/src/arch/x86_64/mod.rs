//! x86-64 architecture support.
//!
//! This module is one of the narrow, audited boundaries where `unsafe` is permitted by
//! [`docs/security/UNSAFE-RUST-POLICY.md`]. Everything here wraps a raw CPU instruction
//! that has no safe equivalent. Each `unsafe` block carries a `SAFETY:` justification.

use core::arch::asm;

/// Writes a byte to an x86 I/O port.
///
/// # Safety
///
/// The caller must ensure that `port` is a valid I/O port for this platform and that
/// writing `value` to it is architecturally meaningful and free of side effects the caller
/// has not accounted for. Port I/O can reconfigure or disable hardware.
#[inline]
pub unsafe fn outb(port: u16, value: u8) {
    // SAFETY: `out` with a `u8` operand is well-defined for any port number; the caller
    // has taken responsibility for the port being the intended device (see fn contract).
    unsafe {
        asm!(
            "out dx, al",
            in("dx") port,
            in("al") value,
            options(nomem, nostack, preserves_flags),
        );
    }
}

/// Reads a byte from an x86 I/O port.
///
/// # Safety
///
/// The caller must ensure `port` is a valid I/O port and that reading it has no unintended
/// side effects; some device registers mutate state on read.
#[inline]
pub unsafe fn inb(port: u16) -> u8 {
    let value: u8;
    // SAFETY: `in` with a `u8` operand is well-defined for any port number; the caller has
    // taken responsibility for the port being the intended device (see fn contract).
    unsafe {
        asm!(
            "in al, dx",
            out("al") value,
            in("dx") port,
            options(nomem, nostack, preserves_flags),
        );
    }
    value
}

/// Disables maskable interrupts on the current CPU.
///
/// # Safety
///
/// Disabling interrupts affects global system state. The caller must ensure that no code
/// depending on interrupt delivery (timers, preemption) is running concurrently.
#[inline]
pub unsafe fn disable_interrupts() {
    // SAFETY: `cli` is always encodable at CPL 0, which is where the kernel runs. The
    // caller has accepted the global consequences per the fn contract.
    unsafe {
        asm!("cli", options(nomem, nostack));
    }
}

/// Halts this CPU permanently with interrupts disabled and never returns.
///
/// Used for the M0 idle terminus and for the panic path. The `hlt` runs in a loop because
/// a non-maskable interrupt or System Management Interrupt can resume execution past a
/// single `hlt` even with interrupts masked.
pub fn halt_forever() -> ! {
    // SAFETY: the function's entire purpose is to stop this CPU; there is no subsequent
    // code whose correctness could depend on interrupts remaining enabled.
    unsafe { disable_interrupts() };
    loop {
        // SAFETY: `hlt` at CPL 0 merely parks the CPU until the next interrupt. It has no
        // memory effects and cannot violate any Rust invariant.
        unsafe {
            asm!("hlt", options(nomem, nostack, preserves_flags));
        }
    }
}
