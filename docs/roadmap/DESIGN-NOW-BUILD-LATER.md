# Design Now, Build Later

**Status:** ACCEPTED.

## Purpose

H0.5 produced a large body of architecture. This document is what stops that from becoming
implementation scope creep: it states, per subsystem, **what is being designed now and what
must not be built yet.**

## Classes

| Class | Meaning |
|---|---|
| **DESIGN NOW** | Specify in H0.5 because it constrains M1–M4 |
| **IMPLEMENT M1–M3** | Kernel ownership |
| **IMPLEMENT M4–M5** | Hardware and system platform |
| **IMPLEMENT M6–M7** | Graphical platform and developer desktop |
| **POST-M7** | After a usable developer OS exists |
| **RESEARCH ONLY** | Study; no production dependency |
| **PROBABLY REUSE** | Do not build; select and integrate |
| **REQUIRES VENDOR** | Not solvable by engineering effort alone |

## Assignment

| Subsystem | Class |
|---|---|
| Kernel object model, rights, IPC shape | **DESIGN NOW** (ADR-0004) — constrains M1–M3 |
| Virtualization kernel/VMM split | **DESIGN NOW** — [Q14](../architecture/OPEN-QUESTIONS.md), constrains M1–M4 |
| Security event stream | **DESIGN NOW** — must land with M3 objects |
| Capability/portal model | **DESIGN NOW** — M2 must not create ambient-authority syscalls |
| Platform layering and ABI layering | **DESIGN NOW** |
| Memory, paging, exceptions, interrupts, time, SMP | IMPLEMENT M1 |
| Threads, processes, scheduler, syscalls | IMPLEMENT M2 |
| Objects, handles, capabilities, IPC | IMPLEMENT M3 |
| ACPI, PCIe, IOMMU, device/driver managers | IMPLEMENT M4 |
| NVMe, xHCI, HID, Ethernet | IMPLEMENT M4 |
| VFS, block, volume, loader, packages, updates, recovery | IMPLEMENT M5 |
| libc, POSIX facade, Rust std | IMPLEMENT M5 — **blocked on [Q1](../architecture/OPEN-QUESTIONS.md)** |
| Netstack, DNS, DHCP, TLS | IMPLEMENT M5 |
| GPU driver, Vulkan, compositor, display | IMPLEMENT M6 — **REQUIRES VENDOR** in part |
| UI toolkit, design system, text, accessibility | IMPLEMENT M6 |
| Audio graph, media framework, capture | IMPLEMENT M6 |
| Files, Settings, Search, Monitor, Terminal | IMPLEMENT M7 |
| SDK, DDK, `malrynth` CLI, debugger | IMPLEMENT M7 |
| Shield baseline | IMPLEMENT M7 |
| Store, Account, Sync, Backup, Link | POST-M7 |
| Linux personality, Wine, Proton, gaming | POST-M7 |
| Android compatibility | POST-M7 |
| Broadcast, Canvas, media applications | POST-M7 |
| Organizations, MDM, EDR | POST-M7 |
| Server, Mobile, Console compositions | POST-M7 |
| **MalrynthFS** | **RESEARCH ONLY** — no milestone may depend on it |
| Codecs, crypto, TLS, text shaping, Unicode, fonts | **PROBABLY REUSE** |
| Browser engine, office format engines, PDF | **PROBABLY REUSE** |
| Wine, Proton, DXVK, vkd3d | **PROBABLY REUSE** |
| Anti-cheat | **REQUIRES VENDOR** — may never be available |
| GPU vendor drivers | **REQUIRES VENDOR** |

## The stopping rule for H0.5

H0.5 is complete when every subsystem above has a class, a home document, and its dependencies
recorded. **It does not require any of them to be implemented**, and implementing one would be
a scope violation regardless of how easy it looked.

## The rule for M1

M1 implements **memory, paging, exceptions, interrupts, time and SMP**. Nothing else.

If M1 finds itself designing a package format, a UI toolkit or a compatibility layer, the
milestone boundary has failed — and this document is the reference that says so.
