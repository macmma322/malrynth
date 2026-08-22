# Toolchain Architecture

**Status:** ACCEPTED as direction. Extends [ADR-0003](../adr/ADR-0003-toolchain-and-targets.md),
which covers only how Malrynth itself is built at M0.

## Sources

- Rust *Target Tier Policy* and *Platform Support* — <https://doc.rust-lang.org/rustc/target-tier-policy.html>
- LLVM cross-compilation and sysroot documentation — <https://llvm.org/docs/>
- LLVM C Library — <https://libc.llvm.org/>
- musl libc — <https://musl.libc.org/>
- LLDB remote debugging (gdb-remote protocol) — <https://lldb.llvm.org/>

## The rule

> **"Malrynth custom OS" means our kernel, platform, ABI and runtime. It does not mean
> replacing LLVM.**

Writing a compiler is a separate multi-decade project that would compete with the operating
system for the same scarce engineers, and would produce worse code generation for years. This
is rejected outright — not deferred.

## Three distinct questions

### 1. What builds Malrynth kernel code?

**Settled and in use (M0):** pinned stable `rustc` + Cargo, `rust-lld`, targeting
`x86_64-unknown-none`. Zero external crates in the kernel. No system linker, no `clang`, no
`cmake`, no `ninja` required — the bootstrap is `rustup` alone.

### 2. What builds Malrynth userspace?

**Direction (M5):** the same Rust toolchain plus Clang for C/C++, targeting
`x86_64-unknown-malrynth` (see [`TARGET-TRIPLES.md`](TARGET-TRIPLES.md)) against a Malrynth
sysroot ([`SYSROOT-STRATEGY.md`](SYSROOT-STRATEGY.md)).

### 3. What is officially supported for third-party native development?

**Direction (M7):** Rust and C first-class; C++ immediately after. The `malrynth` CLI wraps
the underlying tools so a developer does not have to assemble a cross-toolchain by hand — but
the tools underneath are standard, so **Malrynth Studio is optional** and VS Code, JetBrains,
Vim, Emacs and plain CLI workflows are fully supported.

## Component decisions

| Tool | Decision | Reason |
|---|---|---|
| **rustc / Cargo** | Reuse, upstream | Primary implementation language |
| **LLVM / Clang** | Reuse, upstream | C/C++ support; already Rust's backend |
| **lld** | Reuse (bundled `rust-lld`) | Removes an entire class of host configuration drift |
| **LLDB** | Reuse | Client/server gdb-remote architecture is a natural early integration path |
| **LLVM libc** | **Candidate**, unresolved | Full build is static-only with no dynamic loader; many functions missing (verified 2026) |
| **musl** | **Candidate**, unresolved | Complete and permissive, but deeply Linux-syscall-shaped |
| **GCC** | Not a target | **Not an ABI decision.** Malrynth's binary contract is the platform-defined C ABI, which is compiler-independent ([`ABI-STRATEGY.md`](../runtime/ABI-STRATEGY.md)) — a second compiler would not create a second ABI. It would add compiler, codegen, testing and support burden for no capability Clang lacks |
| **binutils** | Not required | LLVM equivalents suffice |
| **CMake / Meson / Ninja** | Reuse, SDK support | Third-party C/C++ expects them; not used to build Malrynth itself |

## Language classification

| Language | Class | Notes |
|---|---|---|
| **Rust** | **First-class native** | Kernel, services, drivers, frameworks, apps |
| **Assembly** | **First-class native**, confined | Only inside `arch/`; boot, syscall entry, context switch |
| **C** | **First-class native (SDK)** | The stable ABI boundary; required for driver/vendor interop |
| **C++** | **Supported** | Shortly after C; needed for reused engines (browser, media, office) |
| **WebAssembly** | **Supported later** | Strong candidate for sandboxed plugins (Broadcast, extensions) |
| **Python** | **Compatibility** | Port the interpreter once POSIX/libc exists; developer tooling |
| **JavaScript / TypeScript** | **Compatibility** | Arrives with a browser engine |
| **Go** | **Possible later** | Its runtime assumes substantial OS surface; a real porting project |
| **C# / Java / Kotlin** | **Possible later** | Runtime ports; Kotlin/Java also relevant to Android compatibility |
| **Swift** | **Not a priority** | Small demand relative to porting cost |
| **Zig** | **Not a priority** | Self-hosted cross-compilation makes it a plausible community port |

**Nothing above is prevented.** The classification records where first-party effort goes, not
what is permitted — a language with a Malrynth target and a libc can be ported by anyone.

## What Malrynth must build itself

Reuse ends where our architecture begins:

- the **target definition** and sysroot layout;
- the **libc/runtime backend** that turns POSIX-shaped calls into Malrynth capabilities;
- the **linker configuration** (scripts, startup objects);
- the **`malrynth` CLI**, packaging, signing and capability inspection;
- the **debugger stub** in the kernel and runtime;
- the **DDK** driver authoring surface.

## Bootstrap and self-hosting

Malrynth cross-compiles from Linux for the foreseeable future. Self-hosting — Malrynth
building Malrynth — requires a filesystem, process model, POSIX facade and ported toolchain,
so it lands at **M5 at the earliest** and is a milestone worth naming: it is the point at
which the platform can sustain its own development.
