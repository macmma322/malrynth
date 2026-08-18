# ADR-0003 — Toolchain, Targets and Language Policy

- **Status:** LOCKED (accepted 2026-08-19)
- **Depends on:** [ADR-0001](ADR-0001-repository-topology.md)
- **Review triggers:** the kernel needs an ABI the built-in targets cannot express; ARM64 bring-up.

## Context

Malrynth is Rust-first with minimal architecture-specific assembly, and C/C++ only where
interoperability or imported code requires it. M0 must choose a toolchain channel, a target
strategy, and a linker — decisions that are expensive to reverse once a kernel exists.

The conventional choice for a hobby Rust kernel is **nightly + a custom JSON target +
`-Z build-std`**. It is worth stating why Malrynth does not start there.

## Decision

### 1. Pin the exact stable toolchain: `1.97.1`

`rust-toolchain.toml` pins the exact version, not `stable`. An operating system must build
identically for years; "it worked yesterday" must be falsifiable, and a toolchain bump must
be a reviewable commit rather than an invisible event that makes a bisect meaningless.

### 2. Use stable Rust, not nightly

Both required targets ship precompiled `core`/`alloc` through rustup, so `-Z build-std` —
and therefore nightly — is not required. Depending on nightly would tie the kernel's ability
to build at all to unstable compiler features, which is an avoidable long-term liability for
a project measured in years.

This is revisited only when a concrete, named requirement forces it. The realistic triggers
are a custom target JSON (see 3) or a feature such as `naked_functions` for exception entry.

### 3. Use built-in targets now; custom target JSON when earned

| Component | Target | Why |
|---|---|---|
| `malboot` | `x86_64-unknown-uefi` | Tier 2 with host tools; produces PE/COFF as UEFI requires; precompiled `core`/`alloc`. |
| `malrynth-kernel` | `x86_64-unknown-none` | Tier 2, freestanding ELF, SSE/MMX disabled and soft-float enabled, red zone disabled — exactly the constraints a kernel needs. |
| `malrynth-abi` | host + both above | Pure `#[repr(C)]` data, so its layout assertions are unit-testable on the host. |

A custom target JSON becomes necessary when Malrynth needs an ABI these cannot express —
most likely `code-model = "kernel"` when the kernel moves to the higher half in M1, or a
distinct user-space target once M2 introduces a Malrynth userland. That change requires
nightly for `-Z build-std`, and will get its own ADR. Adopting it now would buy nothing and
cost the stability guarantee above.

### 4. Kernel images are non-PIE with a static relocation model

`x86_64-unknown-none` defaults to a position-independent executable (`ET_DYN`). `malboot`
performs no relocation processing, so a PIE kernel would be loaded with unresolved
`R_X86_64_RELATIVE` entries and would execute garbage. Rather than teaching the M0 loader to
apply relocations, the kernel is built with `-C relocation-model=static -C link-arg=--no-pie`
to produce `ET_EXEC`, and **the loader verifies `e_type` and the link address and refuses to
boot on mismatch.** The check is the important half: the failure mode this prevents is silent.

### 5. Link with the bundled `rust-lld`

No system linker, `clang`, `lld`, `cmake` or `ninja` is required. `rust-lld` ships inside the
Rust toolchain and is the default linker for both targets, which removes an entire class of
host-configuration drift and shrinks the bootstrap to "install rustup".

### 6. Language policy

- **Rust** for everything unless there is a stated reason otherwise.
- **Assembly** only inside `core/kernel/src/arch/<arch>/`, only where no Rust construct
  expresses the operation (port I/O, `hlt`, later context switching and exception entry).
- **C/C++** only to interoperate with imported code, never for new first-party work. Nothing
  in M0 requires it, and none is present.
- **No external dependency in the kernel.** M0's kernel has zero. The loader has exactly one
  (`uefi`), justified in `THIRD_PARTY.md`, and it stops executing at `ExitBootServices`.

## Alternatives considered

- **Nightly + custom target + `build-std`** — rejected: unnecessary today and permanently
  couples buildability to unstable features. Adopted only when a named requirement forces it.
- **Loading a flat binary instead of ELF** — rejected: discards symbols and section
  permissions, and would have to be undone in M1 for W^X mapping.
- **Linking the kernel into the loader as one binary** — rejected: it would erase the
  loader/kernel boundary that is the entire point of M0.
- **A relocatable (PIE) kernel** — deferred: viable, and likely correct once KASLR is wanted,
  but it requires relocation processing in the loader that M0 does not need.

## Consequences

**Positive:** bootstrap is `rustup` alone; builds are reproducible from a pinned toolchain;
no nightly breakage; the loader actively verifies its assumptions about the kernel image.

**Negative:** the kernel is fixed-address, so no KASLR and a hard dependency on the firmware
honouring an exact allocation address. Both end in M1 with Malrynth-owned page tables.

**Neutral:** moving to a custom target later is a contained change — a JSON file, a channel
switch, and a `build-std` flag — because nothing in the tree assumes the built-in targets.
