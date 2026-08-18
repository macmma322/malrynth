//! Architecture abstraction boundary.
//!
//! Malrynth is x86-64 first and ARM64 later. No ARM64 implementation exists yet, and none
//! is stubbed here — a stub that cannot run is indistinguishable from a lie. What this
//! module *does* guarantee is that architecture-specific code is reachable only through
//! this boundary, so adding `aarch64` later is an additive change rather than a rewrite.
//!
//! Rule: no module outside `arch::` may contain `asm!`, port I/O, or a
//! `#[cfg(target_arch)]`. Violations are how a "portable" kernel quietly becomes
//! single-architecture. See `docs/architecture/KERNEL-BOUNDARY.md`.

#[cfg(target_arch = "x86_64")]
pub mod x86_64;

#[cfg(not(target_arch = "x86_64"))]
compile_error!(
    "Malrynth M0 supports x86_64 only. ARM64 is planned but not implemented; \
     see docs/roadmap/M1.md. Build with --target x86_64-unknown-none."
);
