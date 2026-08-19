//! Kernel debug facilities: stack backtrace capture.
//!
//! # What this provides
//!
//! When the kernel panics, the single most valuable piece of information is *where it came
//! from*. This module walks the frame-pointer chain and reports the return addresses, which
//! `tools/symbolize` resolves to function names and source locations against the kernel ELF.
//!
//! # Why symbolisation happens on the host, not in the kernel
//!
//! Resolving an address to a function name requires a symbol table, and resolving it to a
//! file and line requires DWARF. Embedding either in the kernel image would add tens of
//! kilobytes to every shipped kernel and a DWARF parser to the trusted computing base, to
//! serve a case that only a developer ever reads. The kernel therefore prints raw addresses
//! and the host resolves them. This is what production kernels do, and it keeps the parser
//! -- untrusted-input-handling code -- out of ring 0 entirely.
//!
//! # Why this can degrade, and why it says so
//!
//! Walking frame pointers requires the compiler to emit them. `tools/lib.sh` builds the
//! kernel with `-C force-frame-pointers=yes` for exactly this reason. If the kernel is built
//! some other way, the chain is nonsense -- so every frame is validated, and an implausible
//! chain is reported as such rather than printed as plausible-looking garbage. A backtrace
//! that lies is worse than no backtrace.

use core::arch::asm;

/// Maximum frames captured. Deep enough to be useful, bounded so a corrupted chain cannot
/// spin forever inside a panic handler.
pub const MAX_FRAMES: usize = 16;

/// Largest plausible distance between two consecutive stack frames, in bytes.
///
/// Frames are usually tens to hundreds of bytes apart. A gap larger than this means the
/// chain has left the stack and is following garbage, so the walk stops.
const MAX_FRAME_GAP: u64 = 64 * 1024;

/// Why a backtrace walk stopped. Reported so a short trace is never mistaken for a shallow
/// call stack.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StopReason {
    /// The chain terminated normally (null saved frame pointer).
    ChainEnd,
    /// [`MAX_FRAMES`] was reached; the stack is deeper than reported.
    Truncated,
    /// A frame pointer was misaligned, moved the wrong way, or jumped implausibly far.
    /// Most commonly this means the kernel was built without frame pointers.
    Implausible,
}

/// A captured backtrace: return addresses, innermost first.
pub struct Backtrace {
    frames: [u64; MAX_FRAMES],
    len: usize,
    stop: StopReason,
}

impl Backtrace {
    /// Return addresses, innermost first.
    #[must_use]
    pub fn frames(&self) -> &[u64] {
        &self.frames[..self.len]
    }

    /// Why the walk stopped.
    #[must_use]
    pub fn stop_reason(&self) -> StopReason {
        self.stop
    }
}

/// Captures a backtrace from the caller's frame.
///
/// Safe to call from a panic handler: it performs no allocation, takes no lock, and reads
/// only addresses that passed the plausibility checks described above.
#[inline(never)]
pub fn capture() -> Backtrace {
    let mut frames = [0u64; MAX_FRAMES];
    let mut len = 0usize;

    let mut rbp: u64;
    // SAFETY: reading RBP has no side effects and cannot violate any Rust invariant. The
    // value is treated as untrusted below and every dereference is guarded.
    unsafe {
        asm!("mov {}, rbp", out(reg) rbp, options(nomem, nostack, preserves_flags));
    }

    let stop = loop {
        if len == MAX_FRAMES {
            break StopReason::Truncated;
        }
        // A frame pointer must be non-null and 8-byte aligned. Anything else means we are
        // no longer following a real frame chain.
        if rbp == 0 || !rbp.is_multiple_of(8) {
            break if len == 0 {
                StopReason::Implausible
            } else {
                StopReason::ChainEnd
            };
        }

        // A standard x86-64 frame is [saved_rbp][return_address].
        //
        // SAFETY: `rbp` has been checked non-null and 8-aligned, and on entry it came from
        // the register itself. On every subsequent iteration it came from a previous frame
        // that passed the same checks plus the monotonicity and gap bounds below, so it
        // points into the same stack region. M0 is single-threaded with interrupts
        // disabled, so no concurrent writer can invalidate the frame mid-read.
        let (saved_rbp, return_addr) = unsafe {
            let frame = rbp as *const u64;
            (frame.read_volatile(), frame.add(1).read_volatile())
        };

        if return_addr == 0 {
            break StopReason::ChainEnd;
        }
        frames[len] = return_addr;
        len += 1;

        if saved_rbp == 0 {
            break StopReason::ChainEnd;
        }
        // The stack grows downward, so each caller's frame must sit at a HIGHER address,
        // and only modestly higher. Either violation means the chain has left the stack.
        if saved_rbp <= rbp || saved_rbp - rbp > MAX_FRAME_GAP {
            break StopReason::Implausible;
        }
        rbp = saved_rbp;
    };

    Backtrace { frames, len, stop }
}

/// Prints a captured backtrace to the kernel console.
///
/// Output is deliberately machine-parsable so `tools/symbolize` can consume it directly:
///
/// ```text
/// backtrace:
///   #0  0x0000000010000abc
///   #1  0x0000000010001234
/// ```
pub fn print(backtrace: &Backtrace) {
    if backtrace.frames().is_empty() {
        crate::println!("backtrace: unavailable (no plausible frame chain)");
        crate::println!("  the kernel may have been built without -C force-frame-pointers=yes;");
        crate::println!("  build with tools/build, which sets it.");
        return;
    }

    crate::println!("backtrace:");
    for (index, address) in backtrace.frames().iter().enumerate() {
        crate::println!("  #{index}  {address:#018x}");
    }

    match backtrace.stop_reason() {
        StopReason::ChainEnd => {}
        StopReason::Truncated => {
            crate::println!("  ... truncated at {MAX_FRAMES} frames");
        }
        StopReason::Implausible => {
            crate::println!("  ... chain became implausible; frames above may be wrong");
        }
    }
    crate::println!("  resolve with: tools/symbolize <address>...");
}
