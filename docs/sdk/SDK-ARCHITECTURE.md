# SDK Architecture

**Status:** PROPOSED. Target: M7. Nothing exists.

## Principle

> **Malrynth Studio is optional.** A developer using VS Code, JetBrains, Vim, Emacs or plain
> command-line tooling must be fully supported.

The SDK is a set of libraries, headers, tools and specifications — not an IDE. Anything only
achievable inside a first-party IDE is a platform defect.

## Contents

| Area | Contents |
|---|---|
| **Specifications** | Syscall ABI, IPC protocols, capability vocabulary, package format, manifest schema |
| **Headers** | `malrynth/*.h` — the stable C ABI surface |
| **Rust crates** | Idiomatic wrappers over the C boundary ([`ABI-STRATEGY.md`](../runtime/ABI-STRATEGY.md)) |
| **Libraries** | `libmalrynth`, UI, media, storage clients, notifications |
| **Sysroot** | [`SYSROOT-STRATEGY.md`](../toolchain/SYSROOT-STRATEGY.md) |
| **Tooling** | `malrynth` CLI, packaging, signing, capability inspection |
| **Templates** | Application, service, CLI, driver skeletons |
| **Examples** | Small, complete, buildable, capability-correct |
| **Test harness** | Unit, integration, QEMU-based |
| **Documentation** | Versioned API reference; offline-installable |

## The CLI

```bash
malrynth new app hello          malrynth build
malrynth test                   malrynth run --qemu
malrynth debug                  malrynth package
malrynth sign --development     malrynth inspect-capabilities
```

`inspect-capabilities` matters more than it looks: it shows a developer *exactly* what their
application can do, which is what makes least-authority achievable in practice rather than
aspirationally.

## Versioning

The SDK is versioned with the platform ABI, multiple versions install side by side, and
documentation is versioned with it — a developer targeting Malrynth 4 must not accidentally
read Malrynth 7 behaviour.

## What lives in this repository today

Nothing but this document and the specifications it references. `sdk/` as a source directory
appears when there is a real API to publish — which requires M3 capabilities and M5 runtime
([`REPOSITORY-FUTURE-STRUCTURE.md`](../architecture/REPOSITORY-FUTURE-STRUCTURE.md)).
