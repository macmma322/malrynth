# Unsafe Rust Policy

**Status:** LOCKED. Enforced in M0 code.

## Why a policy

Rust's safety guarantees hold only for safe code. A kernel cannot be written entirely in safe
Rust — page tables, MMIO, context switching and FFI have no safe expression. The risk is not
that `unsafe` exists; it is that `unsafe` **spreads**, until "written in Rust" implies a
guarantee the code does not provide.

Malrynth does not claim safety from its language. It claims a *small, audited* unsafe surface.

## Rules

**1. Safe by default.** `unsafe` is permitted only where no safe construct expresses the
operation.

**2. Confined to audited locations.** `unsafe` may appear in:

- `core/kernel/src/arch/**` — instructions, port I/O, CPU state
- page-table and MMIO code (M1)
- DMA buffer management (M4)
- syscall and exception entry (M2)
- context switching (M2)
- allocator internals (M1)
- FFI boundaries
- `malboot` — firmware calls and image placement

Anywhere else, `unsafe` requires an ADR. This list grows only by ADR.

**3. Every `unsafe` block carries a `SAFETY:` comment** stating the invariants that make it
sound and who guarantees them. A block without one is a defect regardless of correctness —
an unjustified block cannot be reviewed, only re-derived.

**4. Every `unsafe fn` documents a `# Safety` section** stating the caller's obligations.

**5. `unsafe_op_in_unsafe_fn` is forbidden crate-wide.** An `unsafe fn` body is not
implicitly an unsafe block; each operation is delimited and justified separately. Enforced
by `#![forbid(unsafe_op_in_unsafe_fn)]` in every Malrynth crate.

**6. Blocks are minimal.** Wrap the operation, not the surrounding logic.

**7. Never `#![allow(unsafe_code)]` globally**, and never silence a soundness lint to make a
build pass. If a lint is wrong, document why in the `SAFETY:` comment.

**8. `unsafe` in a PR is a review trigger.** Once review exists, an `unsafe` diff is never
approved on skim.

## Current inventory (M0)

| Location | Purpose | Justification |
|---|---|---|
| `kernel/src/arch/x86_64/mod.rs` | `in`/`out`/`cli`/`hlt` | No safe expression for CPU instructions |
| `kernel/src/serial/mod.rs` | UART register access; `static mut` COM1 | Single-threaded early boot; must work before locks exist |
| `kernel/src/main.rs` | `.bss` zeroing; `BootInfo` deref; region slice | Linker symbols and the loader contract |
| `boot/uefi/src/main.rs` | Image placement, `ExitBootServices`, kernel entry | Firmware interaction and control transfer |

`boot/uefi/src/elf.rs` contains **no `unsafe`** — deliberately. It parses untrusted input,
which is precisely where unsafe code is least acceptable, so every field is read by
bounds-checked little-endian extraction rather than by casting the buffer.

## Known M0 debts

- `static mut COM1` is sound only while exactly one execution context exists. **It must
  become a proper lock in M1 when SMP starts additional CPUs.** Recorded in-source and here
  so it is not discovered by a race.

## Verification

`tools/test` runs `clippy -D warnings` for every crate on its real target. Planned:
`cargo-geiger`-style accounting so the unsafe surface is a tracked metric that can regress
visibly, rather than a number nobody measures.
