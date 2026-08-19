# Effort and Risk

**Status:** PROPOSED. Planning estimates derived from scope, **not** sourced industry figures.
Ranges overlap substantially and should be treated as order-of-magnitude only.

## Why record this

An operating system with its own kernel is not a large application; it is a program of work.
Recording the scale early is what makes it possible to say "not yet" to a good idea without
that feeling like defeatism.

## Approximate effort

| Area | Rough effort (engineer-years) | Principal risk |
|---|---:|---|
| M0–M3 kernel | 8–15 | Concurrency and security defects |
| ACPI/PCI/IOMMU/platform | 8–15 | Firmware quirks |
| Core physical drivers | 20–40 | Hardware diversity |
| GPU/display stack | 25–60+ | Documentation and vendor dependencies |
| Network stack | 8–15 | Protocol correctness and performance |
| Audio/input/media core | 8–15 | Latency, device diversity |
| VFS and bootstrap storage | 8–15 | Data integrity |
| Production MalrynthFS | 20–40+ | Catastrophic data-loss defects |
| Package/update/recovery | 8–15 | Bricking, signing |
| Shield (consumer) | 15–30 | False positives, ongoing intelligence |
| Shield (EDR) | +15–30 | Telemetry, privacy, enterprise complexity |
| Linux personality | 20–40 | ABI breadth, `ioctl` surface |
| Windows/Wine/gaming | 20–50 | GPU, anti-cheat, edge cases |
| Android | 20–40 | Framework, Binder, graphics |
| Compositor/UI/Files | 15–30 | Polish, accessibility, performance |
| Store/Account/Sync | 15–30 | Security, reliability, operations |
| QA and hardware lab | continuous | Combinatorial matrix |

Indicative team shape: 3–6 engineers for M0–M1, 6–12 for M2–M3, 12–25 for M4, 20–50 for
M5–M6, 40–80 for M7, and 80–150+ for a consumer release including QA, security, applications,
cloud and support.

## Risk register

| Risk | Severity | Strategy |
|---|---|---|
| **Scope explosion** | **Extreme** | Milestones with explicit non-scope; release gates; this document |
| GPU support | Extreme | Narrow set of supported GPUs; vendor engagement; Vulkan CTS |
| Hardware breadth | Extreme | Certified hardware, not universal support |
| Filesystem correctness | Extreme | Delay MalrynthFS as default; exhaustive crash testing |
| Compatibility | Very high | VMs first, personalities incrementally |
| Power/suspend | Very high | Desktops first, laptops much later |
| Shield detection quality | Very high | Layered model, independent evaluation |
| Update signing | Very high | TUF, threshold signatures, offline root |
| IPC performance | High | Benchmark before freezing the API |
| ABI stability | High | Versioned APIs, compatibility CI |

## The dominant risk is scope, not any algorithm

Malrynth's vision currently contains enough scope for a desktop OS, a server OS, a mobile OS,
a console OS, an office suite, a mail client, a cloud provider, an MDM platform, an EDR
platform, a streaming suite, a developer suite, a sync platform and a game-compatibility
platform.

**None of those can be first-release requirements.** The mitigation is structural rather than
motivational: every milestone document states what is explicitly *out* of scope, and
`docs/apps/APPLICATION-MAP.md` deliberately records the application catalogue as documentation
rather than as directories.

## What this means for the current milestone

M0 is complete. It is the smallest milestone by a wide margin, and finishing it quickly says
nothing about M1–M7 — a point `docs/roadmap/M0.md` records explicitly so that early velocity
is not mistaken for a schedule.
