//! Testable kernel subsystems shared by the bare-metal entry point and host validation.

#![no_std]
#![forbid(unsafe_op_in_unsafe_fn)]
#![deny(missing_docs)]

/// Physical-memory ownership and allocation.
pub mod memory;
