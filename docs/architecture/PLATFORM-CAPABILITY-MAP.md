# Platform Capability Map

**Status:** ACCEPTED as an inventory. Individual entries carry their own status.

This is the master inventory of Malrynth. It is not a feature list: every row exists to answer
a specific engineering question, and rows are included precisely because they are hard,
unglamorous or easy to forget.

## How to read a row

| Column | Meaning |
|---|---|
| **L** | Layer from [`PLATFORM-LAYERS.md`](PLATFORM-LAYERS.md). This also fixes **privilege** and **security boundary**: L2 = ring 0/TCB; L3 = unprivileged but highly trusted; L4 = unprivileged, capability-confined, untrusted; L5–L8 = unprivileged, per-process. |
| **Depends on** | What must exist first. Full chains are in [`DEPENDENCY-GRAPH.md`](DEPENDENCY-GRAPH.md). |
| **B/R** | **C**ustom · **R**euse · **P**ort · **W**rapper. Reasoning in [`BUILD-VS-REUSE-MATRIX.md`](BUILD-VS-REUSE-MATRIX.md). |
| **When** | Earliest credible milestone/horizon. |
| **Status** | Per the vocabulary in [`FOUNDER-VISION-SOURCE-MAP.md`](../research/FOUNDER-VISION-SOURCE-MAP.md). |

Default language is **Rust** unless stated. Anything at L2 is ring 0 and inside the TCB;
anything at L4 is explicitly outside it.

---

## Core kernel

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Boot handoff (`malrynth-abi`) | L1 | Versioned firmware→kernel contract | — | C | **M0** | **LOCKED** |
| Malrynth Boot (`malboot`) | L1 | Load, validate, place kernel; exit boot services | UEFI | C (uses `uefi` crate) | **M0** | **LOCKED** |
| Kernel entry + serial diagnostics | L2 | Bring-up, handoff validation, early console | boot handoff | C | **M0** | **LOCKED** |
| Panic + backtrace | L2 | Fault diagnosis | serial | C | **M0** | **LOCKED** |
| Physical memory manager | L2 | Frame allocation over the boot memory map | boot handoff | C | M1 | ACCEPTED |
| Virtual memory / page tables | L2 | Address spaces, W^X, higher-half kernel | phys mem | C | M1 | ACCEPTED |
| Kernel heap | L2 | Dynamic allocation in ring 0 | VM | C | M1 | ACCEPTED |
| Exceptions (GDT/IDT/TSS) | L2 | Fault handling, diagnostics | VM | C | M1 | ACCEPTED |
| Interrupts (APIC/IOAPIC) | L2 | Delivery and routing | exceptions, ACPI(MADT) | C | M1 | ACCEPTED |
| Time (TSC, monotonic clock, timers) | L2 | Scheduling, timeouts, measurement | interrupts | C | M1 | ACCEPTED |
| SMP bring-up + per-CPU state | L2 | Multi-core | interrupts, time, ACPI | C | M1 | ACCEPTED |
| Synchronisation primitives | L2 | Locks; retires M0's `static mut` console | SMP | C | M1 | ACCEPTED |
| Threads | L2 | Execution contexts | VM, time | C | M2 | ACCEPTED |
| Processes | L2 | Isolation units | threads, VM | C | M2 | ACCEPTED |
| Jobs | L2 | Hierarchical containment, limits, bulk kill | processes | C | M2–M3 | PROPOSED |
| Scheduler | L2 | Fair + capability-gated deadline classes | threads, time | C | M2 | ACCEPTED |
| Syscall entry/exit | L2 | Ring 3 ↔ ring 0 boundary | processes | C | M2 | ACCEPTED |
| Kernel objects + handle tables | L2 | The authority substrate | processes | C | **M3** | PROPOSED |
| Capability rights + attenuation | L2 | The core security invariant | objects | C | **M3** | PROPOSED |
| IPC: channels | L2 | Control plane + handle transfer | objects | C | **M3** | PROPOSED |
| IPC: memory objects | L2 | Bulk data without kernel copies | VM, objects | C | **M3** | PROPOSED |
| IPC: shared rings | L2/L3 | Sustained producer/consumer paths | memory objects | C | M3–M4 | PROPOSED |
| Ports / wait / events | L2 | Multiplexed waiting | objects | C | M3 | PROPOSED |
| Exception ports | L2 | Fault delivery to user space | objects, IPC | C | M3 | PROPOSED |
| Resource accounting | L2 | Per-job limits; DoS resistance | jobs | C | M3–M4 | PROPOSED |
| Entropy / RNG | L2 | Seed for all crypto | CPU RDRAND, later drivers | C+R (algorithms) | M4 | DEFERRED |
| Crypto primitives API | L3 | One audited implementation for the system | RNG | **R** | M5 | DEFERRED |
| Crash dumps | L2/L3 | Post-mortem beyond a backtrace | VM, storage | C | M5 | DEFERRED |
| Virtualization primitives (VMX/SVM) | L2 | Guest entry/exit, EPT/NPT | VM, SMP | C | M5 | PROPOSED |
| `SecurityEventStream` | L2→L3 | Structured EDR observability, not ad-hoc hooks | objects, IPC | C | M4–M7 | PROPOSED |

## Hardware and drivers

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| ACPI parser | L3 | Platform description (MADT, MCFG, DMAR…) | kernel, RSDP from M0 | C+R (tables) | M1(MADT)/M4 | ACCEPTED |
| PCIe enumeration | L3 | Device discovery and config | ACPI | C | M4 | ACCEPTED |
| IOMMU (VT-d / AMD-Vi) | L2+L3 | DMA confinement — **the driver model depends on it** | PCIe, ACPI | C | M4 | ACCEPTED |
| Device manager | L3 | Topology, binding, hotplug | PCIe, IOMMU | C | M4 | ACCEPTED |
| Driver manager | L3 | Lifecycle, restart, health | device mgr | C | M4 | ACCEPTED |
| Driver framework / host | L4 | Runtime every user-space driver links | IPC, caps | C | M4 | ACCEPTED |
| NVMe | L4 | Primary storage | driver fw, IOMMU | C | M4 | ACCEPTED |
| AHCI/SATA | L4 | Legacy storage | driver fw | C | post-M4 | DEFERRED |
| xHCI (USB) | L4 | USB host controller | driver fw, IOMMU | C | M4 | ACCEPTED |
| USB HID | L4 | Keyboard, mouse | xHCI | C | M4 | ACCEPTED |
| Input service | L3 | Event routing, focus, seats | HID | C | M4/M6 | PROPOSED |
| Ethernet (one family) | L4 | Wired networking | driver fw, IOMMU | C | M4 | ACCEPTED |
| Wi-Fi | L4 | Wireless — firmware-heavy, hard | driver fw, crypto | C or **bridge** | post-M5 | DEFERRED |
| Bluetooth | L4 | Peripherals, audio | driver fw | C or bridge | post-M5 | DEFERRED |
| GPU driver | L4 | The single highest-risk component | driver fw, IOMMU, VM | **P/R (Mesa-derived)** | M6 | UNSOLVED |
| Audio driver | L4 | HDA/USB audio | driver fw | C | M6 | PROPOSED |
| Camera | L4 | Capture devices | xHCI/PCIe | C | M6+ | DEFERRED |
| Sensors | L4 | Orientation, ambient, lid | ACPI/I²C | C | Mobile | DEFERRED |
| Printers / scanners | L3/L4 | IPP-first printing | net, storage | **R** (IPP, PDF) | post-M7 | DEFERRED |
| Firmware update | L3 | Signed device firmware | storage, update | C+R | post-M5 | DEFERRED |
| Power / thermal / battery | L3 | ACPI states, idle, throttling | ACPI, drivers | C | M5+ | DEFERRED |
| Suspend / resume | L2+L3 | The hardest laptop problem | power, all drivers | C | post-M5 | DEFERRED |
| Hibernate | L3 | Persist and restore RAM | suspend, storage | C | post-M5 | DEFERRED |
| Hardware error handling (MCE/AER) | L2/L3 | Fault reporting | ACPI, PCIe | C | certification | DEFERRED |

## Storage

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Block layer | L3 | Uniform block access, queues | storage drivers | C | M5 | ACCEPTED |
| Volume manager | L3 | Partitions (GPT), volumes | block | C | M5 | ACCEPTED |
| VFS protocol | L3 | Capability-oriented filesystem interface | IPC, caps | C | M5 | ACCEPTED |
| Bootstrap FS (read-only) | L3 | System image mounting | block, VFS | C | M5 | ACCEPTED |
| FAT / exFAT | L3 | ESP + removable interoperability | VFS | C or R | M5 | ACCEPTED |
| ext family (read-only first) | L3 | Linux volume interop | VFS | **P** | post-M5 | DEFERRED |
| NTFS (read-only first) | L3 | Windows volume interop | VFS | **P/R** | post-M5 | DEFERRED |
| MalrynthFS | L3 | Long-term native FS — **R&D, not a dependency** | VFS, block | C | research | EXPERIMENTAL |
| Full-disk encryption | L3 | Data at rest | block, crypto, Vault | C+R (crypto) | M5+ | PROPOSED |
| Snapshots | L3 | Rollback, ransomware defence | FS with COW | C | post-M5 | PROPOSED |
| Backup service | L3 | Independent of Sync | storage, crypto | C | post-M7 | PROPOSED |
| Recovery environment | L3 | Offline repair — **must not need network** | boot, storage | C | M5 | ACCEPTED |
| Network filesystems | L3 | SMB/NFS clients | net, VFS | **R/P** | post-M7 | DEFERRED |
| Removable media policy | L3 | Untrusted device handling | device mgr, policy | C | M5+ | PROPOSED |

## Network

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| NetStack core (IPv4/IPv6/TCP/UDP/ICMP) | L3 | Malrynth-owned user-space stack | NIC driver, IPC | C | M5 | ACCEPTED |
| ARP / NDP, routing | L3 | Link and route management | netstack | C | M5 | ACCEPTED |
| DHCP client | L3 | Address configuration | netstack | C | M5 | ACCEPTED |
| DNS resolver | L3 | Name resolution | netstack | C | M5 | ACCEPTED |
| mDNS / discovery | L3 | Local device discovery (Link) | netstack | C | post-M5 | DEFERRED |
| TLS | L3/L5 | Transport security | crypto | **R** | M5 | PROPOSED |
| QUIC | L3/L5 | Link transport; modern protocols | TLS, UDP | **R** | post-M5 | PROPOSED |
| Socket broker | L3 | Per-app network capability enforcement | netstack, caps | C | M5 | PROPOSED |
| Firewall / packet policy | L3 | Stateful filtering **after** capability denial | netstack | C | M5+ | PROPOSED |
| VPN provider interface | L3 | Routed tunnels as a capability | netstack | C | post-M7 | DEFERRED |

## Graphics and UI

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Kernel GPU mediation | L2 | Minimal privileged surface only | VM, IOMMU | C | M6 | PROPOSED |
| GPU system driver | L4 | Contexts, GPU VM, queues, fences | kernel mediation | **P** | M6 | UNSOLVED |
| Vulkan loader + ICD | L5 | Explicit graphics API | GPU driver | **R** | M6 | PROPOSED |
| OpenGL compatibility | L5 | Legacy API on Vulkan | Vulkan | **R** (Zink-class) | post-M6 | DEFERRED |
| Display service | L3 | Modes, outputs, HDR, VRR | GPU driver | C | M6 | PROPOSED |
| Compositor | L3 | Window composition, capture authority, input routing | display, GPU, input | C | M6 | PROPOSED |
| Native display protocol | L6 | Malrynth surface protocol | compositor | C | M6 | PROPOSED |
| Wayland compatibility endpoint | L7 | Runs Linux GUI apps — **compatibility, not our protocol** | compositor | C+R | post-M6 | PROPOSED |
| Text shaping + rasterisation | L6 | Unicode, shaping, fallback, bidi | fonts | **R** (HarfBuzz/FreeType-class) | M6 | PROPOSED |
| Font service | L6 | Discovery, fallback chains, variable fonts | storage | C+R | M6 | PROPOSED |
| UI toolkit | L6 | Controls, layout, animation | Vulkan, text, input | C | M6 | PROPOSED |
| Design system | L6 | Tokens, theming, adaptive UI | toolkit | C | M6 | PROPOSED |
| Accessibility tree + AT bus | L6 | Screen reader, magnifier, switch access | toolkit, compositor | C | M6 | PROPOSED |
| Input methods (IME) | L6 | CJK and complex-script input | input, toolkit | C+R | post-M6 | DEFERRED |
| Localisation | L6 | Locale data, formats, RTL | Unicode data | **R** (CLDR/ICU-class) | M6 | PROPOSED |

## Media

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Media graph | L6 | Shared pipeline for all media apps | IPC, memory objects | C | M6 | PROPOSED |
| Codecs | L6 | Decode/encode — **never written from scratch** | media graph | **R** | M6 | PROPOSED |
| Containers / muxers | L6 | MP4, Matroska, etc. | codecs | **R** | M6 | PROPOSED |
| Image decode | L6 | Untrusted-input parsers, sandboxed | media graph | **R** | M6 | PROPOSED |
| Audio graph | L6 | Routing, mixing, per-app streams | audio driver, sched | C | M6 | PROPOSED |
| Audio device service | L3 | Device enumeration, low-latency path | audio driver | C | M6 | PROPOSED |
| Video pipeline | L6 | Decode → process → present | codecs, GPU | C+R | M6 | PROPOSED |
| Hardware encode / decode | L4/L6 | GPU media engines | GPU driver | **R** (Vulkan Video) | M6+ | PROPOSED |
| HDR / colour management | L6 | Correct colour end to end | display, compositor | C | M6+ | PROPOSED |
| Capture (screen/window/app) | L3 | Compositor-authorised capture | compositor, caps | C | M6+ | PROPOSED |
| Camera service | L3 | Capture devices as capabilities | camera driver | C | M6+ | DEFERRED |
| Virtual devices (camera/audio) | L3 | Broadcast output as an input | media graph | C | post-M7 | DEFERRED |

## Application platform

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Executable format (ELF) | L5 | Machine-code container | — | **R** (standard) | M5 | PROPOSED |
| Program loader service | L3 | Load, relocate, map with W^X | VFS, VM, caps | C | M5 | ACCEPTED |
| Dynamic loader | L5 | Shared objects, symbol resolution, TLS | executable fmt | C | M5 | PROPOSED |
| Native runtime API | L5 | The real Malrynth API surface | syscalls, IPC | C | M5 | PROPOSED |
| libc | L5 | C standard library | native runtime | **P/C** | M5 | **UNSOLVED** |
| POSIX facade | L5 | Unix source compatibility | libc, services | C | M5 | PROPOSED |
| Rust `std` port | L5 | Rust ecosystem access | libc/native runtime | **P** | M5 | DEFERRED |
| Component manager | L3 | Topology, lifecycle, capability routing | IPC, caps, packages | C | M5 | ACCEPTED |
| Package format `.mpk` | L6 | Identity, content, capabilities, provenance | crypto, storage | C | M5 | PROPOSED |
| Package store (content-addressed) | L3 | Dedup, integrity, atomic activation | storage, crypto | C | M5 | PROPOSED |
| Update service (A/B) | L3 | Transactional, rollbackable | packages, boot, storage | C | M5 | ACCEPTED |
| App identity + sandbox | L3/L8 | Per-app isolation and authority | caps, component mgr | C | M5–M7 | PROPOSED |
| Capability broker / portals | L3 | User-mediated grants (file picker etc.) | UI, caps | C | M7 | PROPOSED |
| Application framework | L6 | Lifecycle, settings, l10n, a11y, storage | runtime, UI | C | M7 | PROPOSED |
| Notifications | L3/L6 | System notification service | UI, caps | C | M7 | PROPOSED |
| Clipboard | L3 | Compositor-mediated, capability-gated | compositor | C | M6–M7 | PROPOSED |
| Share / URI handlers / associations | L3/L6 | Inter-app routing without ambient authority | component mgr, packages | C | M7 | PROPOSED |
| Background work / scheduling | L3 | Deferred jobs with budgets | component mgr, sched | C | M7 | PROPOSED |
| Settings service | L3 | Typed, per-app and system settings | storage, caps | C | M7 | PROPOSED |
| Vault (secrets) | L3 | Hardware-backed credential storage | crypto, TPM | C+R | M5+ | PROPOSED |
| Logging / tracing | L3 | Structured diagnostics, profiling source | IPC, storage | C | M5 | PROPOSED |

## Developer platform

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Compiler toolchain | host | rustc, Clang, lld | — | **R** | M0 done / M5 extend | **LOCKED** (M0 scope) |
| Target triple + sysroot | host | `x86_64-unknown-malrynth` | libc, runtime | C (config) | M5 | PROPOSED |
| SDK | host | APIs, headers, crates, templates, tooling | runtime, frameworks | C | M7 | PROPOSED |
| DDK | host | Driver authoring surface | driver framework | C | M4–M7 | PROPOSED |
| `malrynth` CLI | host | new/build/test/run/package/sign/inspect | SDK | C | M7 | PROPOSED |
| Debugger | host+target | LLDB via gdb-remote | runtime, kernel stub | **R+C** | M5–M7 | PROPOSED |
| Profiler / trace | L3+host | System and app profiling | tracing service | C | M7 | PROPOSED |
| Emulator / VM tooling | host | `malrynth run --qemu` | QEMU | **R+W** | M0 partial | ACCEPTED |
| Package signing tooling | host | Development and release signing | crypto | C+R | M5 | PROPOSED |

## Compatibility

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| VM manager (VMM) | L3 | User-space VMM over kernel virt primitives | virt primitives, IOMMU | C | M5+ | PROPOSED |
| virtio device models | L3 | Paravirtual guest devices | VMM | C+R (spec) | M5+ | PROPOSED |
| Linux VM | L7 | Correctness-first Linux compatibility | VMM, virtio | **R** (Linux guest) | post-M7 | ACCEPTED |
| Linux personality | L7 | Native Linux syscall translation | processes, POSIX, VFS | C | far post-M7 | PROPOSED |
| Wine | L7 | Windows API implementation | Linux personality/POSIX, Vulkan | **R** | far post-M7 | ACCEPTED |
| Proton / DXVK / vkd3d | L7 | D3D→Vulkan translation for games | Wine, Vulkan | **R** | far post-M7 | ACCEPTED |
| 32-bit support | L5/L7 | Required by much Windows software | loader, ABI | C | far post-M7 | DEFERRED |
| Android VM / runtime | L7 | Android applications | VMM, graphics bridge | **R** | far post-M7 | DEFERRED |
| Web runtime | L7 | Web apps as first-class citizens | browser engine | **R** | post-M7 | DEFERRED |

## Products and online

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Desktop composition | L9 | Shell, services, policy, package set | M7 platform | C | M7 | PROPOSED |
| Server composition | L9 | Headless, remote management | M5 platform | C | post-M7 | DEFERRED |
| Mobile composition | L9 | Touch shell, power, cellular | Mobile hardware | C | far post-M7 | DEFERRED |
| Console composition | L9 | Gamepad shell, fixed hardware | gaming stack | C | far post-M7 | DEFERRED |
| Account service | L3 | Optional identity | net, crypto, Vault | C | post-M7 | PROPOSED |
| Store | L6/L8 | Optional distribution channel | packages, account | C | M7+ | PROPOSED |
| Sync | L3 | E2E-encrypted, per-category | account, crypto, storage | C | post-M7 | PROPOSED |
| Device restore | L3 | Restore intent, not stale binaries | backup, packages | C | post-M7 | PROPOSED |
| Link | L3/L8 | Local-first cross-device protocol | QUIC, crypto, discovery | C | post-M7 | PROPOSED |
| Organizations / MDM / EDR | L3/L8 | Enterprise management | account, policy, Shield | C | far post-M7 | DEFERRED |

## Security (Shield)

| Component | L | Purpose | Depends on | B/R | When | Status |
|---|---|---|---|---|---|---|
| Verified boot | L1 | Signature-checked boot chain | crypto, TPM | C+R | M5 | DEFERRED |
| Measured boot | L1/L3 | Record what actually booted | TPM | C+R | M5 | DEFERRED |
| Package integrity | L3 | Signed, content-addressed packages | crypto, packages | C | M5 | PROPOSED |
| Sandbox enforcement | L2/L3 | The capability model in practice | caps, component mgr | C | M3–M7 | PROPOSED |
| Static scanner | L3 | Signature/rule scanning, **sandboxed** | media/file parsers | **R** | M7+ | DEFERRED |
| Behaviour engine | L3 | Consumes `SecurityEventStream` | event stream | C | M7+ | PROPOSED |
| Network shield / IDS | L3 | Filtering, anomaly detection | netstack | C+R | M7+ | DEFERRED |
| Ransomware containment | L3 | Freeze, revoke, protect snapshots | caps, snapshots, events | C | M7+ | PROPOSED |
| Credential protection | L3 | Vault isolation | Vault, caps | C | M7+ | PROPOSED |
| Recovery | L3 | The last line of defence | recovery env, snapshots | C | M5 | ACCEPTED |

## First-party applications

All L8, all **replaceable**, all `C` unless noted. Unprivileged, except where an application holds
one of the enumerated **privileged system roles** — in this table, Shield containment and Recovery
— which are role-based, narrow and auditable, and are never conferred by being first-party
([`NATIVE-APPLICATION-MODEL.md`](../apps/NATIVE-APPLICATION-MODEL.md)). Per-app detail — purpose,
priority, privileges, offline behaviour, replaceability, build-vs-reuse — is in
[`APPLICATION-MAP.md`](../apps/APPLICATION-MAP.md).

| Group | Applications | Earliest |
|---|---|---|
| System | Files, Settings, Search, Terminal, Monitor, Devices, Store, Shield, Recovery, Backup, Vault | M7 (first six) |
| Communication | Browser (**R** engine), Mail, Calendar, Contacts, Tasks, Link | post-M7 |
| Media | Photos, Video, Music, Camera, Recorder, Capture, Canvas, Broadcast | post-M7 |
| Productivity | Notes, PDF (**R** engine), Write, Sheets, Present (**R** format engines) | post-M7 |
| Developer | Studio, Data, API, Profiler | M7 (tooling), post-M7 (GUI) |

## Coverage note

Of roughly 150 components inventoried, **9 exist** — all M0, all LOCKED. Everything else is
specification. That ratio is the honest state of the project and is the reason
[`DESIGN-NOW-BUILD-LATER.md`](../roadmap/DESIGN-NOW-BUILD-LATER.md) exists: to stop
architecture work from becoming implementation scope creep.
