# Subsystem Coverage

**Status:** PROPOSED. Nothing here is implemented.

## Why this document exists

Feature brainstorming reliably produces compositors, security suites and streaming tools, and
reliably omits the subsystems that actually decide whether people can trust a machine with
their work. Time zones, printing and suspend/resume are not polish — a desktop without them is
a demo.

This is the checklist that keeps those subsystems from being discovered late. Every row needs
a named owner and a specification before Malrynth can call itself a daily-driver OS.

## Coverage

| Subsystem | What it requires | Earliest |
|---|---|---|
| **Power** | ACPI states, CPU idle/frequency, device power, suspend/resume, hibernate | M4–M5 |
| **Thermal** | Sensors, fan and power policy, emergency throttling | M4–M5 |
| **Battery** | Health, cycle counts, charge limits where firmware permits | post-M5 |
| **Time** | RTC, monotonic clock, high-resolution timers, network time sync, **time zones and DST** | M1 (clock), M5 (zones/sync) |
| **Text** | Unicode, shaping, font fallback, bidirectional text, variable fonts | M6 |
| **Input** | Keyboard, mouse, touch, pen, **IME**, controller, accessibility switch | M4 (HID), M6 (IME) |
| **Locale** | Languages, formats, time zones, keyboard layouts, RTL | M6–M7 |
| **Printing** | IPP-first printing, PDF pipeline, scanning | post-M7 |
| **Firmware updates** | Signed firmware packages, rollback/recovery where the device allows | post-M5 |
| **Secrets** | Hardware-backed credential Vault | M5 |
| **Multi-user** | Sessions, login, fast switching, guest, work-profile boundaries | M7 |
| **Diagnostics** | Crash dumps, **symbol server**, hardware error logs, event timeline | M0 (backtrace) → M5 |
| **Virtualization** | VMX/SVM, virtual devices, driver bridge, compatibility VMs | M5–M7 |
| **Installer** | Installation, partitioning, multiboot coexistence | pre-consumer |
| **Hardware errors** | MCE/PCIe AER handling and reporting | certification |
| **Accessibility** | Screen reader, magnification, contrast, switch access — **designed in, never retrofitted** | M6 |
| **Certificates** | Trust store, revocation, enterprise roots | M5 |
| **Removable media** | Policy for untrusted USB storage and devices | M4–M5 |

## Status today

**Only one row has any implementation.** Diagnostics has a kernel panic backtrace
(`core/kernel/src/debug/`) and a host symbolizer (`tools/symbolize`), delivered in M0. Crash
dumps and a symbol server do not exist.

Everything else is unimplemented and unowned. Listing them is not the same as having them, and
this document exists specifically so nobody mistakes the list for progress.
