# Malrynth

**An independent operating system with its own kernel.**

Malrynth is not a Linux distribution, a Linux fork, or a desktop environment. It is a new
operating-system family built on its own kernel, with a capability-oriented hybrid
microkernel architecture, user-space drivers, and no ambient authority for native
applications.

```
        firmware (UEFI)
              |
        Malrynth Boot
              |
        MALRYNTH KERNEL
              |
        Malrynth system services
              |
        Malrynth runtime/platform
              |
        applications
```

Linux is a development host, a compatibility target, and a source of architectural lessons.
**It is never Malrynth's production host kernel.**

---

## Status: M0 complete

Malrynth currently boots and prints diagnostics. That is all, and the documentation is
careful never to claim more.

```
MALRYNTH KERNEL
version: 0.0.1-dev
arch: x86_64
boot: UEFI

memory map received (123 regions, 975 MiB usable)
framebuffer discovered (1280x800, stride 1280 px, BGRX8888, 0x0000000080000000)
boot services exited
kernel entered successfully

MALRYNTH_M0_BOOT_OK
```

**Implemented:** a UEFI loader that validates and places an ELF64 kernel image, a versioned
`#[repr(C)]` boot handoff ABI, `ExitBootServices`, memory-map normalisation, framebuffer and
ACPI RSDP discovery, a kernel entry point with a 16550 UART console, and a deterministic
QEMU boot test whose failure detection is itself verified.

**Not implemented:** memory management, paging, interrupts, scheduling, user mode, processes,
capabilities, IPC, drivers, filesystems, networking, graphics, and every application. See the
[roadmap](docs/roadmap/README.md).

## Quick start

Malrynth has two validated development environments. Native Windows is the canonical one;
Linux is the reference one. Both are described in
[Development Environment](docs/operations/DEVELOPMENT-ENVIRONMENT.md).

**Native Windows** — no WSL2 required. Needs Python 3.10+:

```powershell
python tools\windows\malrynth.py doctor   # read-only: report what is present and missing
python tools\windows\malrynth.py build    # build loader + kernel, assemble the ESP
python tools\windows\malrynth.py test     # fmt, clippy, unit tests, build, boot, panic path
python tools\windows\malrynth.py run      # boot it under supervised QEMU
```

**Linux:**

```bash
./tools/bootstrap   # user-local rustup toolchain + targets, and git hooks
./tools/doctor      # read-only: report what is present and what is missing
./tools/build       # build loader + kernel, assemble the ESP
./tools/test        # fmt, clippy, unit tests, and 3x QEMU boot
```

Watch it boot:

```bash
./tools/run-qemu --interactive
```

Requirements: Rust (via rustup — the version is pinned), QEMU, and OVMF. No `clang`, `lld`,
`cmake` or `ninja` is needed; the Rust toolchain ships its own linker. Either doctor reports
anything missing and how to get it, and never installs anything itself.

## Repository layout

```
docs/       constitution, architecture, ADRs, research, roadmap,
            security, performance, compatibility, specs, operations, legal
manifests/  component inventory, product compositions, release records
tools/      bootstrap doctor build test run-qemu status
            symbolize check-panic-path check-reproducible scan-secrets + git hooks
tools/windows/  native Windows developer CLI (malrynth.py), no WSL2 required
core/       abi/  boot/uefi/ (malboot)  kernel/
tests/windows-tooling/  test suite for the native Windows CLI
```

If the kernel panics, it prints a validated frame-pointer backtrace; resolve it with:

```bash
./tools/run-qemu | ./tools/symbolize
```

**One repository, deliberately.** Not seven. The reasoning — and the explicit, testable
criteria for when a component earns its own repository — is in
[ADR-0001](docs/adr/ADR-0001-repository-topology.md).

## Where to start reading

| If you want to know | Read |
|---|---|
| What Malrynth is for | [The Constitution](docs/constitution/MALRYNTH-CONSTITUTION-DRAFT.md) |
| How it is structured | [System Overview](docs/architecture/SYSTEM-OVERVIEW.md) |
| Why one repository | [ADR-0001](docs/adr/ADR-0001-repository-topology.md) |
| What is actually secure today | [Threat Model](docs/security/THREAT-MODEL.md) |
| What happens next | [Roadmap](docs/roadmap/README.md) · [Master roadmap](docs/roadmap/MASTER-ROADMAP.md) |
| How M0 works | [M0](docs/roadmap/M0.md) |
| **How to set up a machine to build it** | [Development Environment](docs/operations/DEVELOPMENT-ENVIRONMENT.md) |
| **How the whole platform fits together** | [Platform layers](docs/architecture/PLATFORM-LAYERS.md) |
| **Where any component belongs** | [Platform capability map](docs/architecture/PLATFORM-CAPABILITY-MAP.md) |
| **What must exist before X** | [Dependency graph](docs/architecture/DEPENDENCY-GRAPH.md) |
| **What we build vs reuse** | [Build vs reuse matrix](docs/architecture/BUILD-VS-REUSE-MATRIX.md) |
| **What is still undecided** | [Open questions](docs/architecture/OPEN-QUESTIONS.md) |

## A note on documentation

Every document labels itself **LOCKED**, **PROPOSED**, **EXPERIMENTAL**, **DEFERRED** or
**UNSOLVED**, and no document describes an unbuilt system in the present tense. Most of the
architecture here is PROPOSED. Saying so is the point: a project that overstates its own
state in its own documentation cannot be engineered.

## Licensing

**None yet, deliberately.** Malrynth is private and unreleased; all rights are reserved. See
[LICENSING-STATUS.md](docs/legal/LICENSING-STATUS.md) for why the choice is being deferred
and what it is constrained by.
