# Malrynth Roadmap

Milestones are **dependency-ordered, not date-ordered.** No dates are given, because a date
on unstarted kernel work is a guess presented as a plan.

| # | Milestone | Status |
|---|---|---|
| [M0](M0.md) | Boot and diagnostics | **COMPLETE** |
| [H0.5](H0.5.md) | Platform architecture foundation (checkpoint, no implementation) | **COMPLETE** |
| [M1](M1.md) | Memory, paging, exceptions, interrupts, timers, SMP | NOT STARTED |
| [M2](M2.md) | User mode, processes, threads, scheduler, syscalls | NOT STARTED |
| [M3](M3.md) | Objects, handles, capabilities, IPC, shared memory | NOT STARTED |
| [M4](M4.md) | ACPI, PCIe, IOMMU, device/driver management, core drivers | NOT STARTED |
| [M5](M5.md) | VFS, filesystems, loader, libc subset, netstack, packages, updates, recovery | NOT STARTED |
| [M6](M6.md) | GPU, Vulkan, compositor, input, audio, media, accessibility | NOT STARTED |
| [M7](M7.md) | Developer desktop, first applications, SDK/DDK, compatibility previews | NOT STARTED |

Beyond M7: gaming, deeper Wine/Proton, the Linux personality, Broadcast, a broad application
set, account and sync, organisations, Server productisation, Mobile, Console.

## Release artifacts

Naming matters, because a name sets expectations that engineering then has to meet:

| Artifact | Contents | Honest claim |
|---|---|---|
| **Malrynth Kernel Developer Preview** | M0–M4 | A real custom kernel with capabilities, IPC, user-space drivers and IOMMU confinement. Not a usable OS. |
| **Malrynth Developer OS** | + M5–M7 | Self-hosting text-mode system, then a developer desktop. |
| **Malrynth Desktop 1.0** | + certification, GPU, audio, gaming corpus, Shield, recovery, accessibility | A daily driver on certified hardware. |

The first public artifact is **not** called 1.0. Calling an early kernel "1.0" would commit to
guarantees nothing has earned.

## Horizons

M0–M7 sit inside broader horizons H0–H11 so that post-M7 work has a home. See
[`MASTER-ROADMAP.md`](MASTER-ROADMAP.md).

## Supporting documents

- [Subsystem coverage](SUBSYSTEM-COVERAGE.md) — power, time, text, input, printing, accessibility and the other subsystems that decide whether an OS is trustworthy
- [Master roadmap](MASTER-ROADMAP.md) — horizons H0–H11, dependency-gated
- [Design now, build later](DESIGN-NOW-BUILD-LATER.md) — what is specified vs implemented, per subsystem
- [Effort and risk](EFFORT-AND-RISK.md) — scale of the programme, and why scope explosion is the top risk

Every milestone document states objective, dependencies, scope, **explicit non-scope**, exit
criteria, tests, performance gates, security gates, and required documentation. The non-scope
section is the one that keeps milestones finite.
