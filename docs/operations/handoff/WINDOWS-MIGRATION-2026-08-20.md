# Malrynth — Windows Migration Handoff, 2026-08-20

**Status:** LOCKED (a point-in-time migration record).
**Purpose:** be **self-contained**. A fresh Claude/Codex session on Windows must be able to
understand the project and resume safely from this document alone, with no access to prior
conversations.

**This document changes no architecture.** It records state. Where something is unresolved it
says so; where something is proposed it is not promoted to decided.

---

## A. Malrynth identity

Malrynth is a **genuinely independent custom operating system with its own kernel**.

It is **not** a Linux distribution, not a Linux kernel product, not a Linux desktop
environment, and not a Windows skin.

Production architecture:

```
Firmware
   ↓
Malrynth Boot
   ↓
MALRYNTH KERNEL
   ↓
Malrynth system services
   ↓
Malrynth runtime / platform
   ↓
applications
```

Linux **may** be: a development host, a compatibility target, a future guest VM, an optional
isolated driver domain, and an architectural reference.

Linux **must not** become Malrynth's production host kernel. This is the invariant the whole
project rests on. Any design that puts Malrynth on top of a Linux kernel is rejected by
definition, however convenient.

---

## B. Core architectural direction

Accurate as of this migration. **PROPOSED items are not LOCKED.**

| Direction | Status |
|---|---|
| x86-64 first; ARM64 later | ACCEPTED |
| Rust-first; narrow Assembly confined to `arch/`; C/C++ for compatibility, SDK and vendor integration | LOCKED (M0 practice) |
| Capability-oriented **hybrid** microkernel | ACCEPTED |
| Explicit kernel objects / handles / rights | PROPOSED (ADR-0004) |
| **No ambient authority** for native applications | ACCEPTED |
| High-performance IPC | ACCEPTED |
| Shared memory and descriptor rings for bulk transfer | PROPOSED |
| User-space drivers where practical | ACCEPTED |
| IOMMU-confined DMA | ACCEPTED |
| Native Malrynth runtime (`libmalrynth`) | PROPOSED |
| **POSIX as a compatibility facade, not native identity** | PROPOSED |
| ELF64 native executable direction | PROPOSED |
| **Package format separate from executable format** | PROPOSED |
| Reuse LLVM / rustc / Clang / lld | ACCEPTED |
| **A custom compiler is explicitly NOT required** | ACCEPTED |
| Vulkan-first future graphics path | PROPOSED |
| Native Malrynth compositor | PROPOSED |
| Transactional updates with rollback | ACCEPTED |
| Local / offline-first | ACCEPTED (Constitution) |
| Malrynth Account optional; cloud optional | ACCEPTED |
| First-party apps replaceable, with no private API | ACCEPTED |
| Sideloading allowed; third-party stores allowed | ACCEPTED |
| AI optional and provider-neutral; never the final security authority | ACCEPTED |

---

## C. Current implementation — what ACTUALLY exists

Distinguish carefully. Most of Malrynth is **specified**, not built.

### IMPLEMENTED (real, running, tested)

**M0 boot path only.** Roughly 851 lines of Rust across three crates, plus ~1,720 lines of
tooling.

- `malboot` — UEFI loader for `x86_64-unknown-uefi`. Reads `kernel.elf` from the ESP,
  validates and places it, discovers the GOP framebuffer and ACPI RSDP, allocates the handoff
  block **before** `ExitBootServices`, normalises the UEFI memory map, enters the kernel.
- `malrynth-abi` — versioned `#[repr(C)]` boot handoff contract with host unit tests asserting
  exact layout (`BootInfo` = 112 bytes/align 8, `MemoryRegion` = 24, `Framebuffer` = 32,
  magic = `"MALRYNTH"`).
- `malrynth-kernel` — `#![no_std]`, `x86_64-unknown-none`. Zeroes `.bss`, initialises a 16550
  UART, validates the handoff on three independent checks, reports the memory map and
  framebuffer, emits `MALRYNTH_M0_BOOT_OK`, halts.
- Panic handler with a **validated frame-pointer backtrace**; symbolisation happens on the
  host via `tools/symbolize` (a DWARF parser is deliberately kept out of ring 0).
- **The kernel has zero external dependencies.** `uefi = "0.39"` is the only external crate in
  the whole tree and is confined to the loader.
- The ELF parser in `core/boot/uefi/src/elf.rs` contains **no `unsafe`** — verified.

**Measured facts (not estimates):**

| Fact | Value |
|---|---|
| Loader image | 40,960 bytes |
| Kernel image | 130,688 bytes |
| Kernel loaded extent | 16 KiB across three `PT_LOAD` segments |
| Reproducibility | **byte-identical across build directories**, enforced by `tools/check-reproducible` |
| Boot validation | 3 consecutive QEMU q35 + OVMF boots asserting the exact marker |
| Panic path | tested by `tools/check-panic-path` (8 properties, incl. that the success marker is NOT emitted) |
| CI on `main` | passed, 1m23s under TCG |

The kernel grew 116,208 → 130,688 bytes when the backtrace and `-C force-frame-pointers=yes`
were added. That was recorded deliberately as a trade, not absorbed silently.

### SPECIFIED (documents only, zero code)

Everything H0.5 produced — ~60 architecture documents. `core/` contains only `abi/`,
`boot/uefi/` and `kernel/`; **no source directory exists for unwritten code**, and that is a
deliberate, verified property.

All performance release gates are labelled *"PROPOSED — none of these is measured, and none is
a claim."*

### RESEARCHED (study, no production dependency)

`docs/research/` and the separate R0 reference-hardware branch (§F). MalrynthFS is classed
**RESEARCH ONLY**; no milestone may depend on it.

### FUTURE

M1–M7 and horizons H1–H11. Zero code.

### What M0 explicitly does NOT provide

No image authenticity (an attacker who can write to the ESP can replace the kernel — accepted
and documented), no distributable `.img` (QEMU virtual FAT only; `mtools` deliberately not
installed), no boot timing, no physical hardware bring-up, no relocatable kernel, no lock on
the serial port, no reclaimed boot-services memory, no cross-host reproducibility proof.

---

## D. Milestones

| ID | Objective | Status |
|---|---|---|
| **M0** | Boot and diagnostics | **COMPLETE** (2026-08-19), 13/13 exit criteria, 8 limitations carried into M1 |
| **H0.5** | Platform architecture foundation (checkpoint, no implementation) | **COMPLETE** (2026-08-19), 14/14 exit criteria — **on branch `docs/platform-foundation`, NOT merged** |
| **M1** | Memory, Interrupts and Time | **NOT STARTED** — the next milestone |
| M2 | User mode, processes, threads, scheduler, syscalls | NOT STARTED |
| M3 | Objects, handles, capabilities, IPC, shared memory | NOT STARTED — "the milestone that determines whether Malrynth is architecturally what it claims" |
| M4 | ACPI, PCIe, IOMMU, device/driver managers, NVMe, xHCI, HID, Ethernet | NOT STARTED |
| M5 | VFS, filesystems, loader, libc subset, netstack, packages, updates, recovery | NOT STARTED |
| M6 | GPU, Vulkan, compositor, input, audio, media, accessibility | NOT STARTED |
| M7 | Developer desktop, first applications, SDK/DDK | NOT STARTED |

**M1 scope, verbatim from `DESIGN-NOW-BUILD-LATER.md`:** *memory, paging, exceptions,
interrupts, time and SMP. Nothing else.* M1 also retires two M0 debts — the fixed
non-relocatable load address (`0x1000_0000` → higher half) and the `static mut` serial port
(must become a lock before SMP) — and delivers the calibrated timer that makes the first real
boot-time budget possible.

### Horizons (dependency-gated, no calendar dates)

| Horizon | Contents | Exit gate |
|---|---|---|
| **H0** | M0 + H0.5 | Kernel boots and verified; platform architecture specified end to end — **MET** |
| H1 | M1–M3 | Malrynth owns memory, CPU, scheduling and authority; capability invariants hold under adversarial test |
| H2 | M4 | Real hardware runs; a malicious driver cannot DMA outside its domain |
| H3 | M5 | Self-hosting text-mode system |
| H4 | M6 | Compositor at refresh rate; Vulkan conformance; audio latency met |
| H5 | M7 | Usable daily dev machine for its own developers |
| H6 | App ecosystem | Third-party apps exist that we did not write |
| H7 | Compatibility & gaming | A meaningful corpus of existing software runs |
| H8 | Account, Store, Link | Everything remains fully usable offline |
| H9 | Server & enterprise | Server product runs real workloads |
| H10 | Mobile | Shares one core; no second kernel |
| H11 | Console | Shares one core; no second kernel |

Release artifacts: **Malrynth Kernel Developer Preview** (H1–H2) → **Malrynth Developer OS**
(H3–H5) → **Malrynth Desktop 1.0** (H6+). The first public artifact is deliberately **not**
called 1.0.

---

## E. Important H0.5 decisions

All on branch `docs/platform-foundation`. Status labels are load-bearing.

| Area | Decision | Status |
|---|---|---|
| **Platform layering** | Ten layers L0 firmware → L1 malboot → L2 kernel (ring 0, the TCB) → L3 system services (unprivileged but highly trusted) → L4 driver domains (untrusted, capability-confined) → L5 runtime → L6 frameworks → L7 compatibility → L8 applications → L9 products. Every boundary states privilege, trust, mechanism, stability and failure isolation. | ACCEPTED |
| **Capability map** | ~150 components inventoried; **9 exist**, all M0. | ACCEPTED |
| **Toolchain** | Reuse rustc/LLVM/Clang/lld/LLDB. A custom compiler is rejected outright, not deferred. | ACCEPTED |
| **Target triples** | `x86_64-unknown-malrynth`, entering Rust as **Tier 3**. No environment suffix initially. | PROPOSED |
| **Sysroot** | startup objects, libc, libm, `libmalrynth`, dynamic loader, Rust `std`, headers, linker specs. **Not faked** — none exists. | PROPOSED |
| **ABI** | **Eight** distinct contracts separated. Load-bearing rule: *the syscall ABI is not the platform contract* — apps bind to `libmalrynth`. Long-term binary stability uses the **C ABI** because Rust has none. | PROPOSED |
| **Executable model** | **ELF64**. `.mpk` is a distribution container referencing ordinary ELF blobs — package format ≠ executable format. | PROPOSED |
| **libc** | **UNSOLVED (Q1)** — highest-leverage open decision. LLVM libc's full build is static-only with no dynamic loader; musl is complete but Linux-syscall-shaped. Inclination: port musl's upper layers onto a Malrynth bottom layer. | **UNSOLVED** |
| **POSIX** | **Facade, not native personality** (Q2). POSIX presumes ambient authority; making it native would adopt Unix's security model as Malrynth's. Consequence accepted: some software will never run unmodified. | PROPOSED |
| **Rust std** | Add a `sys` backend, do not fork `std`. `std::process::Command` must express *which capabilities a child receives*. | DEFERRED (blocked on Q1) |
| **Native app model** | An app starts with **minimal authority**. Running "as the user" does not mean it can read everything the user owns. | PROPOSED |
| **App capabilities** | Portal pattern is primary: **picking is the grant**, so no prompt is needed. Manifest / runtime / one-shot / user-picked / directory / policy grant kinds. Revocation must actually work. | PROPOSED |
| **Package model** | Identity, content, authority and state kept separate. A signature proves who published bytes, not that the app may read everything. **Installation is declarative** — no install-time scripts with elevated authority. | PROPOSED |
| **SDK / DDK** | Malrynth Studio is **optional**; VS Code / JetBrains / Vim / CLI fully supported. DDK is a product decision — vendors need users, contracts, tooling and support. | PROPOSED |
| **Graphics / UI** | Kernel GPU role deliberately tiny. **Wayland is a compatibility endpoint, not the native protocol.** Compositor owns **capture authorisation**. Text shaping/rasterisation/Unicode reused. Accessibility designed in, never retrofitted. | PROPOSED |
| **Storage / Files** | Kernel **never** parses on-disk structures from untrusted volumes. Capability-relative path resolution makes traversal structurally impossible. Files invariant: **enumerate → render immediately → enrich asynchronously**. | PROPOSED |
| **Media / Broadcast** | Codecs, containers and image decoders reused and sandboxed; graph/routing/capabilities custom. Per-app audio routing without virtual-cable workarounds. Broadcast **consumes** platform capabilities, never builds parallel plumbing. | PROPOSED |
| **Shield** | Prevent → detect → contain → recover. *If Shield is doing the heavy lifting, the architecture has failed.* Kernel `SecurityEventStream` must be designed **at M3**, not retrofitted. Applications never hold authority to delete protected snapshots. | PROPOSED |
| **Compatibility** | Always above/beside, never underneath. Staged VM → personality → desktop. Wine and gaming sit at the confluence of **two** long chains. | ACCEPTED |
| **Gaming** | Technically-solvable separated from vendor-dependent. **Anti-cheat is explicitly not promised.** Overlays are a compositor capability, not code injection. | PROPOSED |
| **Virtualization** | Kernel holds only privileged primitives; the VMM is user-space. Driver-bridge VMs never load foreign modules into the Malrynth kernel. | PROPOSED — **earliest deadline (Q14)** |
| **Account / Sync / Backup** | Six identities kept distinct. **Sync ≠ Backup** — deletion propagates through one, not the other. Device restore restores **intent, not stale binaries**. | PROPOSED |
| **Link** | QUIC, local-first, per-feature authorisation, blind relay that never holds content keys. | PROPOSED |
| **Store** | **Optional.** Sideloading and third-party stores are legitimate and use the same format, signatures and capability model. | PROPOSED |
| **Organizations** | Company policy scoped to company-managed state. Enforcing that *technically* is **unsolved (Q12)**. | PROPOSED |
| **Privacy** | Mechanical, not policy: a calculator cannot exfiltrate because it cannot create a socket. No advertising identifiers, structurally. | PROPOSED |
| **Product composition** | One kernel, four compositions. **If a product needs a kernel change, that change belongs to every product.** | ACCEPTED |

### Open questions and decision deadlines

**Do not convert these into conclusions.** Full text: `docs/architecture/OPEN-QUESTIONS.md`.

| # | Question | Decide by |
|---|---|---|
| **Q14** | Virtualization kernel/VMM split | **End of M3 — earliest; constrains M1–M4** |
| **Q1** | Which libc (musl port / LLVM libc / own / relibc-style) | End of M4 — gates everything downstream |
| **Q2** | POSIX: native personality or facade | End of M4 |
| Q4 | Initial production filesystem | Start of M5 |
| Q5 | Native stable ABI mechanism | M5 |
| Q6 | Package signing root and key custody | Before first signed release (M5) |
| **Q3** | GPU driver strategy — highest technical risk | Start of M6 |
| Q7 | UI toolkit rendering strategy | Start of M6 |
| Q8 | Browser engine | Post-M7 |
| Q9 | Office document engines | Post-M7 |
| Q11 | Cloud key recovery (E2E vs recoverability) | Before Sync ships |
| Q12 | Organization identity / BYOD boundary | Before Organizations ships |
| Q10 | Codec licensing and patents | Before shipping any media app |
| Q13 | Malrynth's own licence | Before public release or external contribution |
| Q15 | Anti-cheat | **Not solvable by us** — tracked as a known limitation |

---

## F. Reference hardware research (R0)

**Branch:** `research/reference-hardware-r0` @ **`1ec8b02`** — pushed, **NOT merged**.
**Also:** `research/reference-hardware-r0-polish` @ **`f497605`** — an earlier iteration of the
same research, preserved (see §G).

The directory states up front that it is *"research proposal, not architecture, implementation,
procurement approval, or certification."* **Research stays research.** Nothing here has been
promoted into architecture.

### Proposed findings

| Area | Proposed finding |
|---|---|
| **Platform** | **Intel-first**, controlled desktop: non-F, homogeneous six-core 10th-gen Comet Lake-S/Embedded Core i5 with UHD 630 on **Q470/Q470E** — homogeneous cores, iGPU, VT-d, industrial serial/debug, Intel Ethernet, without hybrid cores, laptop ECs or discrete GPUs |
| **Excluded from R0** | F-suffix CPUs (no iGPU), Pentium/Celeron, Xeon/ECC, hybrid-core Intel parts, laptops, servers |
| **Baseline discipline** | Kernel baseline kept deliberately *below* the reference hardware — long mode + local APIC only; AVX, VMX/SVM, x2APIC, invariant TSC, TSC-deadline and SMT all detected-and-fallback-tested, never assumed |
| **Firmware** | 64-bit UEFI only; self-contained loader handoff; bounded map-key retry on `ExitBootServices`; never call Boot Services afterwards |
| **ACPI** | Every table and AML program treated as **untrusted input**; adopt a reviewed external AML engine (**uACPI, MIT** preferred candidate; ACPICA as a host-side oracle) rather than growing a partial interpreter |
| **Graphics** | **GOP-only** for R0 — a UEFI linear framebuffer plus a CPU-rendered console. Native modesetting, Vulkan, compute and video are separately gated later claims |
| **GPU ordering** | Two *distinct* rankings: Intel → AMD → NVIDIA as the R0 **platform** order (the iGPU supplies GOP with no extra device); **AMD → Intel → NVIDIA** as the future **native-acceleration** order (amdgpu's OS-agnostic Display Core plus RADV/ACO give the strongest open seam) |
| **NVIDIA** | **Excluded from R0** and expansion-only — open kernel modules are Linux modules needing signed GSP firmware and release-matched proprietary userspace |
| **IOMMU** | A working IOMMU is **mandatory before any DMA-capable device is granted to an unprivileged driver**. Assignable unit is an empirically validated isolation group, not a function. Default domain **blocked**, never identity |
| **Storage** | **NVMe first** — one controller, one namespace, written natively against the specification; AHCI/SATA deferred to R1; VMD/RST/RAID remapping must be disabled in firmware |
| **USB** | **xHCI first** — exactly one standards-conforming PCI xHCI controller, no EHCI/UHCI/OHCI; includes the BIOS/OS legacy ownership handoff |
| **Input** | **Wired USB HID boot-protocol** keyboard and mouse; PS/2 only as an optional debug fallback, and only when ACPI flags advertise an 8042. Bind by class/protocol and parsed descriptors, never a VID:PID allowlist |
| **Ethernet** | Discrete **Intel I210/I211** (`8086:1533` / `8086:1539`) or I350 as the preferred first native target |
| **Wi-Fi / Bluetooth** | **Later** — not part of R0 |
| **Audio** | **UAC1 (USB Audio Class 1) before complex audio** — HDA and codec complexity deferred |
| **Linux driver domains** | Secondary / bootstrap mechanism only — never a path by which Linux ends up beneath the Malrynth kernel |

### Named hardware are RESEARCH CANDIDATES, not architecture

Specific model numbers — i5-10500/10500E/10500TE, Q470/Q470E boards, Intel I210/I211/I350,
the Coffee Lake/Q370 (i5-9500, i5-8500) cost fallback, and the AMD AM4 B550 + Ryzen 5
5600G/PRO 5650G cross-vendor control — are **acquisition candidates for evaluation**. They are
explicitly *not* a permanent architectural commitment and *not* procurement approval.

The existing Acer Nitro AN515-52 laptop is a later secondary/negative target only.

---

## G. Repository and branch state

**Repository:** `macmma322/malrynth` — **PRIVATE** (verified). Default branch `main`.
**Remote:** `https://github.com/macmma322/malrynth.git`

| Branch | Local = Remote SHA | Purpose | Status | Validation | Merged? | Next action |
|---|---|---|---|---|---|---|
| `main` | `7a421b4` | Accepted baseline: M0 complete | **Untouched by this migration** | Full suite green (previous session), CI success | — | Leave alone |
| `docs/platform-foundation` | `a3ce182` | H0.5 platform architecture (~60 docs) + the non-PIE fix | Complete | **Full suite green this session** (see §H) | **NO — deliberate** | Review, then merge only on explicit approval |
| `research/reference-hardware-r0` | `1ec8b02` | Codex R0 hardware research (23 docs) | Complete | Docs-only; clean | **NO — deliberate** | Keep as research |
| `research/reference-hardware-r0-polish` | `f497605` | **Earlier iteration** of the same R0 research | Superseded but preserved | Secret-scanned, whitespace-clean, JSON valid | **NO** | Keep or delete after R0 is settled |
| `handoff/windows-migration-2026-08-20` | *this branch* | These two handoff documents only | Migration record | Docs-only | **NO — must not be merged** | Read on Windows |

**Tags**

| Tag | Points at | Purpose |
|---|---|---|
| `v0.0.1-m0` | `46f4af9` | M0 milestone release tag (unsigned — no signing key exists) |
| `archive/orphaned-r0-drafts-2026-08-20` | `b051e2f` | **Not a release tag.** Makes previously-unreachable orphaned R0 drafts reachable so they are backed up rather than destroyed by `git gc`. May be deleted once R0 is settled. |

### Relationship between branches — preserve this

```
                 1ec8b02  research/reference-hardware-r0        (7 commits)
                /
7a421b4 main ──┼── f497605  research/reference-hardware-r0-polish (5 commits, earlier iteration)
                \
                 a3ce182  docs/platform-foundation              (10 commits)
                 └─ handoff/windows-migration-2026-08-20        (branched from main)
```

All four working branches descend from `main` and are **parallel and unmerged by design**.
`r0` and `r0-polish` are two iterations of the same research with **identical file sets** —
`r0` is the refined version (+390/−214 lines relative to polish).

**Integration is a deliberate future decision to be made from Windows. Migration did not
authorize it and none was performed.**

---

## H. Worktree state on the Linux laptop (historical after migration)

| Path | Branch | State |
|---|---|---|
| `/media/Data/Malrynth` | `docs/platform-foundation` (restored after handoff work) | Clean; holds `target/` 243 MB, `esp/`, `build/` — all git-ignored |
| `/media/Data/Malrynth-Codex-R0` | `research/reference-hardware-r0` | Clean, 843 KB, no untracked files |

`Malrynth-Codex-Identity` was mentioned as a possibility but **does not exist**.

Worktrees live inside `.git` and **never travel with a clone**. A Windows checkout gets one
worktree; the second must be recreated deliberately (§ bootstrap document).

### Validation performed during this migration

On `docs/platform-foundation` @ `a3ce182`:

```
tools/doctor                exit 0
git diff --check            clean
tools/test --boots 3        ALL CHECKS PASSED
  fmt · clippy ×4 (incl. panic-test cfg) · ABI unit tests · build
  3× QEMU boot asserting MALRYNTH_M0_BOOT_OK
  panic path (8 properties) · reproducibility (both images byte-identical)
tools/scan-secrets --history   clean (covers all local refs, incl. unpushed commits)
git fsck --full --strict    healthy
```

**CI note:** the dispatched run on `docs/platform-foundation` shows **cancelled**. It hit the
workflow's 30-minute job timeout during `apt-get install qemu-system-x86 ovmf` —
**infrastructure, not a code failure**. Every step before it, including the secret scan,
succeeded. `main` has green CI. Re-running on Windows is optional.

---

## I. Important documents

| Path | Governs |
|---|---|
| `docs/constitution/MALRYNTH-CONSTITUTION-DRAFT.md` | What Malrynth is *for*; 22 principles |
| `docs/adr/ADR-0001-repository-topology.md` | **One repository**, with split criteria |
| `docs/adr/ADR-0002-branching-and-release-model.md` | Branching, releases, protected-by-policy `main` |
| `docs/adr/ADR-0003-toolchain-and-targets.md` | Pinned stable Rust, built-in targets, non-PIE kernel |
| `docs/adr/ADR-0004-kernel-object-model.md` | Object namespace, rights vocabulary, `mly_` syscalls |
| `docs/architecture/PLATFORM-LAYERS.md` | L0–L9 and every boundary contract |
| `docs/architecture/PLATFORM-CAPABILITY-MAP.md` | **Master inventory** — where any component belongs |
| `docs/architecture/DEPENDENCY-GRAPH.md` | **What must exist before X** |
| `docs/architecture/BUILD-VS-REUSE-MATRIX.md` | Build/reuse/port/wrap with licence and trust |
| `docs/architecture/OPEN-QUESTIONS.md` | 15 unresolved decisions with deadlines |
| `docs/roadmap/MASTER-ROADMAP.md` | Horizons H0–H11 |
| `docs/roadmap/DESIGN-NOW-BUILD-LATER.md` | What may be built when; **the M1 scope rule** |
| `docs/apps/APPLICATION-MAP.md` | Every planned first-party application |
| `docs/toolchain/TOOLCHAIN-ARCHITECTURE.md` | What builds Malrynth and what third parties use |
| `docs/security/THREAT-MODEL.md` | Threats and what is honestly *not* mitigated |
| `docs/security/UNSAFE-RUST-POLICY.md` | Where `unsafe` is permitted; `SAFETY:` requirement |
| `docs/operations/DEVELOPMENT-ENVIRONMENT.md` | Linux reference host and NTFS constraints |
| `research/reference-hardware-r0/README.md` | R0 research entry point *(on the R0 branch)* |
| `research/reference-hardware-r0/REFERENCE-R0-RECOMMENDATION.md` | The R0 recommendation *(on the R0 branch)* |

---

## J. Repository topology

**One Malrynth repository.** Not a submodule per application, product or subsystem.

A component earns its own repository only when a **real** boundary justifies it: independent
release lifecycle, security/access boundary, restricted developer access, independent
contributor community, multiple unrelated consumers, history that would damage the main
repository, differing licence/governance, or exact-version pinning.

None applies today. Splitting later is cheap and lossless (`git subtree split --prefix=<dir>`
preserves history); merging later is expensive. Directory boundaries in `core/` already mirror
the future repository boundaries. Full reasoning: `docs/adr/ADR-0001-repository-topology.md`.

---

## K. Development principles

- **No fake implementations.** No empty architecture scaffolding. Source directories appear
  when real source appears.
- **Research → specify invariants → implement the smallest mechanism → test the failure paths.**
- **"Custom OS" does not mean everything handwritten.** Reuse proven compilers, codecs, crypto,
  Unicode, shaping and rasterisation. Never hand-roll cryptography, TLS, codecs or text shaping.
- **Never reuse** the kernel, capability enforcement, IPC, component manager, package system or
  compositor authority — that would mean adopting someone else's security model.
- **Security by architecture before antivirus.**
- **Performance measured, not marketed.** Nothing is claimed without a number and a method.
- **First-party applications must not gain hidden competitive APIs** (Constitution §7).
- **Privileged system roles are different from ordinary first-party apps** — a system app is an
  ordinary app with a bigger manifest, not a privileged one.
- **Sync ≠ Backup.**
- **Desktop / Server / Mobile / Console share one core.** Never four kernels. Mobile and
  Console remain later horizons.
- Every document declares a status; no present tense for unbuilt systems.

---

## L. Next task

**One recommendation: finalise and review the H0.5 branch, merge only after explicit approval,
then begin M1.**

Precisely:

1. **`docs/platform-foundation` @ `a3ce182` remains unmerged and is complete.** No H0.5
   corrections are outstanding — the branch is validated, green, and pushed. It is waiting only
   on your review.
2. **`research/reference-hardware-r0` @ `1ec8b02` remains unmerged research.** Decide separately
   whether any of it is promoted into architecture. Promotion is a deliberate act requiring an
   ADR; migration did not perform it.
3. **Then, and only then, begin M1 — Memory, Interrupts and Time.**

**M1 was not started during this migration, and must not be started before the above.**

### Two documentation discrepancies found during migration (recorded, deliberately NOT fixed)

Fixing these would be development work, which migration does not authorise. They are small and
belong to whoever next touches those branches:

1. `docs/roadmap/M0.md` contains an "Observed output" transcript still showing
   `kernel.elf loaded, 116208 bytes` — the *pre-backtrace* size. The correct measured figure is
   **130,688 bytes**, as recorded in `PERFORMANCE-CONSTITUTION.md` and confirmed on disk. The
   transcript is stale; the measurement is right.
2. `docs/operations/DEVELOPMENT-ENVIRONMENT.md` records the reference host kernel as
   `7.0.0-29-generic`; the laptop now runs `7.0.0-30-generic`. Everything else in that table
   still matches.
