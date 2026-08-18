//! Minimal 16550-compatible UART driver for early kernel diagnostics.
//!
//! This is the kernel's **only** output device at M0 and the mechanism by which the boot
//! smoke test observes success. It is deliberately polled and lock-free: it must work
//! before memory management, interrupts, scheduling or any allocator exists, and it must
//! keep working from inside a panic handler when kernel invariants are already broken.
//!
//! Status: **EXPERIMENTAL**. This driver moves to a proper user-space serial driver once
//! the driver framework exists (M4); it stays in the kernel only as a debug facility.

use crate::arch::x86_64::{inb, outb};
use core::fmt::{self, Write};

/// I/O port base of COM1 on IBM-PC-compatible hardware, including QEMU's `q35` machine.
const COM1_BASE: u16 = 0x3F8;

// Register offsets from the port base. With DLAB clear unless noted.
const REG_DATA: u16 = 0; // Transmit/receive buffer; divisor low when DLAB=1.
const REG_INT_ENABLE: u16 = 1; // Interrupt enable; divisor high when DLAB=1.
const REG_FIFO_CTRL: u16 = 2; // FIFO control (write).
const REG_LINE_CTRL: u16 = 3; // Line control, including the DLAB bit.
const REG_MODEM_CTRL: u16 = 4; // Modem control.
const REG_LINE_STATUS: u16 = 5; // Line status (read).

/// Line Status Register bit 5: transmit holding register empty.
const LSR_THR_EMPTY: u8 = 1 << 5;
/// Line Control Register bit 7: Divisor Latch Access Bit.
const LCR_DLAB: u8 = 1 << 7;
/// Line Control Register value for 8 data bits, no parity, 1 stop bit.
const LCR_8N1: u8 = 0x03;

/// A polled 16550 UART.
pub struct SerialPort {
    base: u16,
}

impl SerialPort {
    /// Creates a handle to the UART at `base` without touching the hardware.
    ///
    /// # Safety
    ///
    /// `base` must be the I/O port base of an actual 16550-compatible UART, and the caller
    /// must ensure no other code is driving the same UART concurrently.
    pub const unsafe fn new(base: u16) -> Self {
        Self { base }
    }

    /// Initialises the UART for 38400 baud, 8N1, FIFOs enabled, interrupts disabled.
    ///
    /// The divisor is 3 because the 16550 input clock is 115200 Hz: 115200 / 3 = 38400.
    pub fn init(&mut self) {
        // SAFETY: every write below targets a documented 16550 register at `self.base`,
        // which the constructor's contract guarantees is a real UART owned by us. The
        // sequence is the standard initialisation order: mask interrupts, program the
        // divisor behind DLAB, clear DLAB while setting the line format, enable FIFOs.
        unsafe {
            outb(self.base + REG_INT_ENABLE, 0x00); // Mask all UART interrupts.
            outb(self.base + REG_LINE_CTRL, LCR_DLAB); // Expose the divisor latch.
            outb(self.base + REG_DATA, 0x03); // Divisor low  = 3 -> 38400 baud.
            outb(self.base + REG_INT_ENABLE, 0x00); // Divisor high = 0.
            outb(self.base + REG_LINE_CTRL, LCR_8N1); // 8N1, clears DLAB.
            outb(self.base + REG_FIFO_CTRL, 0xC7); // Enable+clear FIFOs, 14-byte trigger.
            outb(self.base + REG_MODEM_CTRL, 0x03); // Assert DTR and RTS.
        }
    }

    /// Writes one byte, spinning until the transmit holding register is free.
    ///
    /// This blocks indefinitely if no UART is present. That is the correct trade for M0:
    /// a machine with no serial port has no way to report a fault anyway, and silently
    /// dropping diagnostics would make boot failures undiagnosable.
    pub fn write_byte(&mut self, byte: u8) {
        // SAFETY: reads the documented Line Status Register and writes the transmit
        // register of the UART this handle owns; neither has side effects beyond the UART.
        unsafe {
            while inb(self.base + REG_LINE_STATUS) & LSR_THR_EMPTY == 0 {
                core::hint::spin_loop();
            }
            outb(self.base + REG_DATA, byte);
        }
    }

    /// Writes a string, translating `\n` to CRLF so terminals render it correctly.
    pub fn write_str_raw(&mut self, s: &str) {
        for byte in s.bytes() {
            if byte == b'\n' {
                self.write_byte(b'\r');
            }
            self.write_byte(byte);
        }
    }
}

impl Write for SerialPort {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        self.write_str_raw(s);
        Ok(())
    }
}

/// The kernel's early-boot COM1 handle.
///
/// M0 is strictly single-CPU with interrupts disabled, so a `static mut` is sound here and
/// avoids requiring a spinlock before synchronisation primitives exist. **This must be
/// replaced with a proper lock in M1**, when SMP brings up additional CPUs; until then the
/// single-writer invariant is enforced by the absence of any other execution context.
static mut COM1: SerialPort = unsafe { SerialPort::new(COM1_BASE) };

/// Initialises COM1. Call exactly once, before any [`print!`] or [`println!`].
///
/// # Safety
///
/// Must be called only from the single-threaded early-boot path, before other CPUs or any
/// interrupt handler can run.
pub unsafe fn init() {
    // SAFETY: the caller guarantees single-threaded early boot, so this pointer cannot
    // alias any other access to COM1.
    unsafe {
        let port = &raw mut COM1;
        (*port).init();
    }
}

/// Writes formatted output to COM1. Used by the [`print!`] macro; not called directly.
///
/// # Safety
///
/// Must only be reached from the single-threaded early-boot path or the panic handler.
pub unsafe fn _print(args: fmt::Arguments<'_>) {
    // SAFETY: as above -- M0 has exactly one execution context, so this pointer cannot
    // alias. Errors are ignored because a UART write cannot meaningfully fail and the
    // panic path must not itself panic.
    unsafe {
        let port = &raw mut COM1;
        let _ = (*port).write_fmt(args);
    }
}

/// Writes formatted output to the kernel serial console, without a trailing newline.
#[macro_export]
macro_rules! print {
    ($($arg:tt)*) => {{
        // Formatting happens outside the unsafe block so that caller-supplied expressions
        // are never silently granted unsafe context.
        let args = format_args!($($arg)*);
        // SAFETY: M0 is single-threaded with interrupts disabled; see serial::_print.
        unsafe { $crate::serial::_print(args) }
    }};
}

/// Writes formatted output to the kernel serial console, followed by a newline.
#[macro_export]
macro_rules! println {
    () => { $crate::print!("\n") };
    ($($arg:tt)*) => {{
        $crate::print!($($arg)*);
        $crate::print!("\n");
    }};
}
