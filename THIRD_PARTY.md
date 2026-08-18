# Third-Party Components

**Status:** LOCKED. Updated with every dependency change.

This is the complete ledger of third-party code in Malrynth, maintained from day zero because
reconstructing provenance later is unreliable and sometimes impossible.

## Policy summary

The kernel has **zero** external dependencies, and defending that property is the primary
supply-chain control. See [THIRD_PARTY_POLICY.md](THIRD_PARTY_POLICY.md) and
[docs/security/SUPPLY-CHAIN.md](docs/security/SUPPLY-CHAIN.md).

## Privilege summary

| Component | External dependencies | Privilege |
|---|---|---|
| `malrynth-kernel` | **none** | ring 0, permanent |
| `malrynth-abi` | **none** | linked into both loader and kernel |
| `malboot` | `uefi` and its tree (below) | firmware-time only; ceases to exist at `ExitBootServices` |

The distinction matters: loader dependencies stop executing at `ExitBootServices` and are not
part of the runtime trusted computing base. A kernel dependency would be.

## Direct dependency

### `uefi`

| | |
|---|---|
| **Version** | 0.39.0 |
| **Source** | crates.io — <https://github.com/rust-osdev/uefi-rs> |
| **License** | MIT OR Apache-2.0 |
| **Used by** | `malboot` only |
| **Privileged?** | Yes while it runs (firmware-time), no at runtime |
| **Relationship** | Dependency. **No code copied.** |

**Purpose:** safe Rust bindings to UEFI boot services, protocols and types — the system
table, `SimpleFileSystem`, `GraphicsOutput`, memory allocation, the memory map, and
`ExitBootServices`.

**Why necessary:** the alternative is hand-written FFI definitions for firmware structures.
A subtly wrong field offset or calling convention in a hand-rolled UEFI binding produces
memory corruption during boot with no diagnostic — a far worse risk than depending on a
maintained, widely used standards binding for code that stops running at `ExitBootServices`.
The project brief's own guidance applies: *"custom operating system" does not mean "rewrite
the UEFI specification."*

**Why it is confined to the loader:** UEFI is a boot environment, not part of Malrynth's
architecture. Keeping every firmware type inside `malboot` is what allows a non-UEFI boot
path to be added later without touching the kernel
(`docs/architecture/KERNEL-BOUNDARY.md`).

## Transitive dependencies

All are pulled in by `uefi`, all are loader-only, and all carry permissive licenses
compatible with every licensing option still open to Malrynth
(`docs/legal/LICENSING-STATUS.md`).

| Crate | Purpose |
|---|---|
| `uefi-raw` | Raw UEFI type and protocol definitions |
| `uefi-macros` | `#[entry]` and related proc macros |
| `uguid` | GUID type and parsing |
| `ucs2` | UCS-2 conversion, required by UEFI string APIs |
| `bitflags` | Typed flag sets |
| `bit_field` | Bit-range accessors |
| `ptr_meta` / `ptr_meta_derive` | Pointer metadata for DSTs |
| `log` | Logging facade used by the `uefi` logger |
| `cfg-if` | Conditional compilation helper |
| `proc-macro2`, `quote`, `syn`, `unicode-ident` | Build-time only (proc-macro machinery); **not linked into any Malrynth binary** |

Exact resolved versions are pinned in the committed `Cargo.lock`.

## Copied code

**None.** No third-party source has been copied into Malrynth.

Architecture from Fuchsia, seL4, Redox, SerenityOS, Haiku and Linux has been **studied** and
is cited in `docs/research/`. Studying an architecture is research; copying an implementation
creates a derivative work with license obligations. Any future copy must be recorded here
with exact source, exact license, obligations, and modifications — **before** it is committed.

## Firmware and tools (not distributed)

OVMF, QEMU and the Rust toolchain are development and test dependencies obtained from the
host system. **They are never committed** (`docs/operations/ARTIFACT-POLICY.md`) and are not
redistributed as part of Malrynth.
