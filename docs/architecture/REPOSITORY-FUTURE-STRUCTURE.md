# Repository Future Structure

**Status:** ACCEPTED. [ADR-0001](../adr/ADR-0001-repository-topology.md) is unchanged: **one
repository**.

## The rule

> **Source directories appear when real source appears.**

H0.5 produced a large amount of architecture documentation. It produced **no** source
directories, because a directory for unwritten code is scaffolding that must be maintained,
searched and eventually deleted. Documentation directories are different: they hold
substantive documents that exist today.

## Current structure

```
malrynth/
├── docs/          ← grew substantially in H0.5; every directory holds real documents
├── manifests/
├── tools/
└── core/
    ├── abi/        malrynth-abi
    ├── boot/uefi/  malboot
    └── kernel/     malrynth-kernel
```

## Anticipated structure

Recorded so future boundaries are visible, **not created**:

```
core/        kernel, boot, ABI, low-level libraries          exists
services/    component mgr, device mgr, VFS, netstack…       appears at M4-M5
drivers/     framework, virtual, physical                    appears at M4
runtime/     native API, libc, POSIX facade, loader          appears at M5
sdk/         public API surface, headers, crates, tooling    appears at M5-M7
ui/          compositor, toolkit, design system, text        appears at M6
apps/        first-party application workspace               appears at M7
compat/      Linux/Windows/Android compatibility             appears post-M7
products/    Desktop/Server/Mobile/Console compositions      appears at M7
```

Each is a **directory**, not a repository. ADR-0001's split criteria (two demonstrable criteria
required) govern any future extraction, and `git subtree split --prefix=<dir>` makes it
mechanical with history preserved.

## Where things live before their directory exists

| Concern | Today |
|---|---|
| Driver framework design | `docs/architecture/DRIVER-MODEL.md`, `docs/sdk/DDK-ARCHITECTURE.md` |
| Runtime and libc | `docs/runtime/` |
| UI and graphics | `docs/ui/`, `docs/graphics/` |
| Applications | `docs/apps/` |
| Products | `docs/products/`, `manifests/products/` |
| Compatibility | `docs/compatibility/` |

## What would violate this

Creating `apps/photos/src/`, `sdk/rust/src/`, `ui/compositor/src/` or similar because
documentation now describes them. **Documentation describing a component is not permission to
create its directory.** The trigger is real source, and nothing else.
