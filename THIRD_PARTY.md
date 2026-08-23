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

## Anticipated reuse (H0.5) — NOT YET IMPORTED

Recorded because [`BUILD-VS-REUSE-MATRIX.md`](docs/architecture/BUILD-VS-REUSE-MATRIX.md) makes
reuse recommendations that carry legal consequences. **None of the following is present in the
repository, and no code has been copied.** Each requires a full ledger entry and licence review
*before* import.

| Anticipated component | Expected licence family | Use | Legal review required |
|---|---|---|---|
| libc (musl or LLVM libc) | MIT / Apache-2.0 w/ LLVM exception | Ported into the runtime | Attribution; modification disclosure |
| Cryptographic primitives | Permissive (varies) | Linked into privileged services | Export/crypto considerations |
| TLS / QUIC implementations | Permissive (varies) | Network stack | — |
| Text shaping (HarfBuzz-class) | MIT | Text engine | Attribution |
| Font rasterisation (FreeType-class) | FTL or GPL dual | Text engine | **Licence choice matters** |
| Unicode / CLDR data | Unicode licence | Text, locale | Attribution |
| Media codecs | Varies | Media framework | **PATENT REVIEW REQUIRED** — obligations are independent of source licence ([Q10](docs/architecture/OPEN-QUESTIONS.md)) |
| Mesa-derived GPU driver | MIT-ish | Ported GPU driver | Attribution; modification tracking |
| Vulkan loader | Apache-2.0 | Graphics | — |
| Browser engine (Chromium / WebKit) | BSD / LGPL | Browser | **Significant review**; LGPL implications |
| Office/PDF format engines | Varies | Productivity | Review per engine |
| Wine | LGPL | Windows compatibility | **Separate process** — must remain non-derivative |
| DXVK / vkd3d-proton | zlib / LGPL | D3D translation | Same |
| Linux guest kernel | GPL-2.0 | Compatibility VM guest | **Guest only** — never beneath Malrynth; must remain non-derivative |
| virtio specification | Spec | Paravirtual devices | — |

**Unresolved legal review**, tracked in [`LICENSING-STATUS.md`](docs/legal/LICENSING-STATUS.md):

1. **Codec patents** — the single largest legal risk to shipping media applications.
2. **LGPL boundaries** for Wine, vkd3d and possibly a browser engine: process separation must
   be verified, not assumed.
3. **GPL-2.0 guest isolation** — a Linux VM guest must not create a derivative-work argument.
4. **Malrynth's own licence** ([Q13](docs/architecture/OPEN-QUESTIONS.md)) constrains which of
   the above are compatible, so it interacts with every row here.

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
