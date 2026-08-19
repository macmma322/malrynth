# Naming Specification

**Status:** LOCKED for the identifiers in use; PROPOSED for those not yet implemented.

Consistency matters more than elegance. The rule throughout: **no clever abbreviations.**
`malrynth-kernel`, not `mkrn`. Names are read far more often than typed.

## GitHub repositories

`malrynth` for the superproject; `malrynth-<component>` for any future extraction
(`malrynth-core`, `malrynth-sdk`). Lowercase, hyphenated. Today only `malrynth` exists.

## Rust crates

`malrynth-<component>`, matching the directory name, with one deliberate exception:
**`malboot`**, whose name is a product name (Malrynth Boot) rather than a component path.
It is spelled the same everywhere: crate, binary, and prose.

| Crate | Path | Role |
|---|---|---|
| `malrynth-abi` | `core/abi` | Boot handoff contract |
| `malboot` | `core/boot/uefi` | UEFI loader |
| `malrynth-kernel` | `core/kernel` | Kernel |

Crate names use hyphens; the Rust identifier uses underscores (`malrynth_abi`). Modules are
`snake_case` and singular where they name a concept (`capability`, not `capabilities`).

## Architecture and platform

Architectures use their standard names: `x86_64`, `aarch64` — never `amd64` or `arm64` in
source paths, so directory names match Rust's `target_arch` exactly and no mapping table is
needed. Rust target triples are used verbatim (`x86_64-unknown-none`).

## Branches and tags

Branches: `main`, `feature/<topic>`, `fix/<topic>`, `research/<topic>`, `release/<version>`.
Tags: `v<major>.<minor>.<patch>-<milestone>`, annotated, e.g. `v0.0.1-m0`. See ADR-0002.

## Syscalls (PROPOSED — see [ADR-0004](../adr/ADR-0004-kernel-object-model.md))

`mly_<object>_<verb>`, e.g. `mly_channel_write`, `mly_memory_seal`, `mly_dma_map`.

`mly_` is the **one sanctioned abbreviation** in Malrynth. It is short because it prefixes
every syscall in the system; everything after it is spelled out.

## Package format (PROPOSED)

Package files use the extension **`.mpk`**. Installed application state is partitioned by
lifetime, so that uninstall can offer meaningful choices instead of one destructive button:

| Path | Lifetime |
|---|---|
| `/package` | read-only, content-addressed |
| `/config` | private, persistent |
| `/data` | private, persistent |
| `/cache` | disposable at any time |
| `/temp` | session |
| `/secrets` | Vault handles, never plaintext |

## Identifiers not yet implemented (PROPOSED)

Recorded now so they are chosen once rather than invented per subsystem:

- **Package IDs** — reverse-DNS: `com.malrynth.files`. Globally unique, delegable, familiar.
- **Application IDs** — equal to the package ID of the providing package.
- **Capability identifiers** — `malrynth.<subsystem>.<object>.<right>`, e.g.
  `malrynth.storage.volume.read`. Hierarchical so policy can express prefixes.
- **Protocol/interface names** — `malrynth.<domain>.<Interface>/<Version>`, e.g.
  `malrynth.io.Stream/1`. The version is part of the name because an unversioned interface
  becomes unversionable.
- **Products** — `malrynth-desktop`, `malrynth-server`, `malrynth-mobile`, `malrynth-console`.

## Prose

The system is **Malrynth**. The loader is **Malrynth Boot**. The kernel is the **Malrynth
kernel** (lowercase `kernel`). "MalrynthOS" is not used.

## Reserved markers

`MALRYNTH_M0_BOOT_OK` and `MALRYNTH_M0_BOOT_FAIL` are asserted verbatim by the boot test.
Milestone markers follow `MALRYNTH_<MILESTONE>_<EVENT>_<RESULT>`. These strings are part of
the test contract and must not be reworded casually.
