# Malrynth Roadmap

Milestones are **dependency-ordered, not date-ordered.** No dates are given, because a date
on unstarted kernel work is a guess presented as a plan.

| # | Milestone | Status |
|---|---|---|
| [M0](M0.md) | Boot and diagnostics | **COMPLETE** |
| [M1](M1.md) | Memory, paging, exceptions, interrupts, timers, SMP | NOT STARTED |
| [M2](M2.md) | User mode, processes, threads, scheduler, syscalls | NOT STARTED |
| [M3](M3.md) | Objects, handles, capabilities, IPC, shared memory | NOT STARTED |
| [M4](M4.md) | ACPI, PCIe, IOMMU, device/driver management, core drivers | NOT STARTED |
| [M5](M5.md) | VFS, filesystems, loader, libc subset, netstack, packages, updates, recovery | NOT STARTED |
| [M6](M6.md) | GPU, Vulkan, compositor, input, audio, media, accessibility | NOT STARTED |
| [M7](M7.md) | Developer desktop, first applications, SDK/DDK, compatibility previews | NOT STARTED |

Beyond M7: gaming, deeper Wine/Proton, the Linux personality, Broadcast, a broad application
set, account and sync, organisations, Server productisation, Mobile, Console.

Every milestone document states objective, dependencies, scope, **explicit non-scope**, exit
criteria, tests, performance gates, security gates, and required documentation. The non-scope
section is the one that keeps milestones finite.
