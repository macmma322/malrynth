# Executable Model

**Status:** PROPOSED.

## Decision: ELF64

Malrynth uses **ELF64** for executables and shared objects.

**Reasoning.** An executable format is a container specification, not an architecture. Rust
and LLVM already emit ELF; every debugger, profiler and analysis tool understands it; DWARF
integrates natively; and the M0 loader already parses it successfully. Inventing a format would
cost a loader, a linker backend, toolchain patches and a decade of tooling, and would buy
nothing that ELF's flexibility does not already provide.

PE was rejected: it carries Windows-specific structure Malrynth does not need, and Rust's
PE support is oriented toward MSVC conventions. It stays relevant only for UEFI, where the
firmware requires it — which is precisely why `malboot` is PE and the kernel is ELF.

## The distinction that matters most

> **Package format ≠ executable format.**

`.mpk` is a *distribution and identity* container: manifest, capabilities, signatures,
provenance, resources, and references to content-addressed blobs. Those blobs are ordinary
ELF files. Nothing about `.mpk` requires a new machine-code container, and conflating the two
is a common and expensive mistake.

```
package.mpk  →  manifest + signatures + capability declaration
                     └─> blob (ELF executable)
                     └─> blob (ELF shared object)
                     └─> blob (resource)
```

## Model

| Aspect | Decision | Reason |
|---|---|---|
| Executables | ELF64 `ET_DYN` (PIE) | ASLR requires position independence |
| Shared objects | ELF64 `ET_DYN` | standard |
| Kernel | ELF64 `ET_EXEC` (non-PIE) | loaded at a fixed address; no relocation in the loader (M0) — becomes PIE-capable when M1 introduces its own page tables |
| Relocations | standard x86-64 set; `RELR` where beneficial | `RELR` materially shrinks relocation tables |
| ASLR | mandatory for userspace | cheap, effective mitigation |
| TLS | ELF TLS, initial-exec and global-dynamic | standard, well-supported |
| Symbol versioning | supported from the start | retrofitting it is very painful |
| Constructors | `.init_array` / `.fini_array` | standard |
| Debug info | DWARF, separable | already used by `tools/symbolize` |
| Build ID | required | ties a crash dump to its binary and its package |

## W^X and code signing

Executable pages are **never** writable. The program loader maps segments with permissions
derived from `PT_LOAD` flags and refuses any segment that requests both.

Signing applies to the **package**, not the ELF file. Signing individual binaries would
duplicate the package signature and create two verification paths that can disagree. The chain
is: package signature → content-addressed blob hashes → the ELF being loaded. The loader
verifies the blob hash it was asked to map; it does not parse signatures.

JIT compilation (needed later by a browser or language runtime) requires a *deliberate,
capability-gated* mechanism for creating executable mappings. It is not a general permission
and is not granted by default. Recorded now so it is designed rather than discovered.

## Open

- **32-bit support** for Windows compatibility — an `i686` ELF path and loader support. Deferred, but the ABI must not make it impossible ([Q](../architecture/OPEN-QUESTIONS.md)).
- Whether the kernel becomes PIE at M1 for KASLR.
