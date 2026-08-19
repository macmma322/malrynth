# Founder Vision — Source Map

**Status:** LOCKED (this map); each requirement carries its own status.
**Date:** 2026-08-19

## Sources

| ID | Source |
|---|---|
| **B** | Founding engineering brief (task prompt, §0 product/architecture context) |
| **R** | *Malrynth OS: Architecture, Security, Compatibility, Ecosystem, and Production Roadmap for a Truly Custom Operating System* — founder-supplied research report, 3,821 lines |
| **H** | H0.5 platform-foundation brief |

Both founder documents were re-read for this pass; the previous summary was not treated as a
substitute for them.

## Status vocabulary

| Status | Meaning |
|---|---|
| **LOCKED** | Decided, implemented, and verified. Changing it requires a superseding ADR. |
| **ACCEPTED** | Decided as architectural direction. Not implemented; individual APIs not frozen. |
| **PROPOSED** | Recommended direction with reasoning. Expected to change. |
| **EXPERIMENTAL** | Being tried; may be abandoned. |
| **DEFERRED** | Deliberately not decided now; decision has an owner and a trigger. |
| **UNSOLVED** | Genuinely open. No credible answer yet. |

**Appearing in the founder vision does not confer LOCKED.** Only something built, measured
and attacked earns that. Currently LOCKED items are almost entirely M0 artifacts.

---

## 1. Non-negotiable product constraints

| Requirement | Source | Status | Related | Architecture affected | Horizon | Unresolved |
|---|---|---|---|---|---|---|
| Malrynth has its **own kernel**; Linux never underneath | B, R | **LOCKED** | ADR-0003, `KERNEL-BOUNDARY.md` | everything | M0 done | — |
| Capability-oriented **hybrid** microkernel | B, R | **ACCEPTED** | ADR-0004, `CAPABILITY-MODEL.md` | kernel, services, apps | M3 | which fast paths justify kernel residence |
| **No ambient authority** for native apps | B, R | **ACCEPTED** | ADR-0004, `APPLICATION-CAPABILITY-MODEL.md` | apps, services, compat | M3 | revocation; persistence |
| Rust-first, minimal asm, C only for interop | B, R | **LOCKED** | ADR-0003 | all code | M0 done | — |
| x86-64 first, ARM64 later | B, R | **ACCEPTED** | `arch/mod.rs` boundary | kernel, toolchain | ARM64 post-M4 | second-arch timing |
| User-space drivers by default; IOMMU-confined DMA | B, R | **ACCEPTED** | `DRIVER-MODEL.md`, `DDK-ARCHITECTURE.md` | drivers, kernel, security | M4 | no-IOMMU posture |
| High-performance IPC; shared memory for bulk | B, R | **ACCEPTED** | `IPC-MODEL.md` | everything above kernel | M3 | fast-path design; measured budgets |
| Vulkan-first graphics, native compositor | B, R | **ACCEPTED** | `GRAPHICS-STACK.md` | graphics, UI, media, gaming | M6 | GPU driver strategy |
| Transactional / rollbackable updates | B, R | **ACCEPTED** | `UPDATE-MODEL.md` | packages, storage, recovery | M5 | rollback vs anti-rollback tension |
| Offline-first; account optional | B, R | **ACCEPTED** | Constitution I, `ACCOUNT-ARCHITECTURE.md` | cloud, apps, products | M5+ | — |
| Sideloading and third-party stores legitimate | B, R | **ACCEPTED** | Constitution §5–6, `STORE-ARCHITECTURE.md` | packages, Store, policy | M7 | signing root vs sideload UX |
| First-party apps replaceable, not privileged | B, R | **ACCEPTED** | Constitution §7, `APPLICATION-FRAMEWORK.md` | apps, capabilities | M7 | verification mechanism |
| Compatibility above/beside, never underneath | B, R | **LOCKED** | `COMPATIBILITY-ARCHITECTURE.md` | compat, kernel | M7+ | — |
| One core, four products (no four kernels) | B, R | **ACCEPTED** | `PRODUCT-COMPOSITION.md` | everything | M7+ | variant boundary |
| Advertising profiles are not part of the OS | B, R | **ACCEPTED** | Constitution §13 | privacy, cloud | always | — |
| AI optional, provider-neutral, never final security authority | B, R | **ACCEPTED** | Constitution §15–16 | AI, Shield | post-M7 | — |

## 2. Kernel and execution

| Requirement | Source | Status | Related | Horizon | Unresolved |
|---|---|---|---|---|---|
| Kernel object namespace (`Job`…`ExceptionPort`) | R | **PROPOSED** | ADR-0004 | M3 | set completeness |
| Rights vocabulary, attenuation-only | R | **PROPOSED** | ADR-0004 | M3 | granularity |
| `mly_<object>_<verb>` syscalls; small ABI | R | **PROPOSED** | ADR-0004, `ABI-STRATEGY.md` | M3 | — |
| Three IPC classes: channel / memory object / shared ring | R | **PROPOSED** | `IPC-MODEL.md` | M3 | inline payload budget (benchmark) |
| Fair scheduler + capability-gated deadline reservations | R | **PROPOSED** | — | M2–M3 | profile delegation model |
| Virtualization primitives in kernel; VMM in user space | R | **PROPOSED** | `VIRTUALIZATION-ARCHITECTURE.md` | M5+ | exact kernel/VMM split — **constrains M1–M4** |
| Verified + measured boot, TPM | R | **DEFERRED** | `TRUST-BOUNDARIES.md` | M5 | owner-key model |
| Crash dumps + symbol server | R | **DEFERRED** | `debug/`, `tools/symbolize` | M5 | dump format |
| Entropy / RNG and crypto primitives API | R | **DEFERRED** | — | M4–M5 | source of entropy pre-driver |

## 3. Platform, runtime and developer surface

| Requirement | Source | Status | Related | Horizon | Unresolved |
|---|---|---|---|---|---|
| Reuse LLVM/Clang/rustc/lld/LLDB — do not write a compiler | R | **ACCEPTED** | `TOOLCHAIN-ARCHITECTURE.md` | M5 | — |
| `x86_64-unknown-malrynth` target triple | R | **PROPOSED** | `TARGET-TRIPLES.md` | M5 | vendor field; upstream timing |
| Sysroot with startup objects, libc, libm, headers, Rust std | R | **PROPOSED** | `SYSROOT-STRATEGY.md` | M5 | — |
| libc for Malrynth | R | **UNSOLVED** | `LIBC-STRATEGY.md` | M5 | musl-port vs LLVM-libc vs own — **decision by M4** |
| POSIX: native or facade | R | **PROPOSED** (facade) | `POSIX-STRATEGY.md` | M5 | conformance depth |
| Rust `std` port | R | **DEFERRED** | `RUST-STD-PORT.md` | M5 | depends on libc decision |
| Executable format | R | **PROPOSED** (ELF) | `EXECUTABLE-MODEL.md` | M5 | — |
| SDK + DDK + `malrynth` CLI | R | **PROPOSED** | `SDK-ARCHITECTURE.md`, `DDK-ARCHITECTURE.md` | M7 | — |
| Studio optional; VS Code/JetBrains/CLI fully supported | R | **ACCEPTED** | `SDK-ARCHITECTURE.md` | M7 | — |
| Package `.mpk`, content-addressed, capability manifest | R | **PROPOSED** | `PACKAGE-MODEL.md` | M5 | signing root |
| A/B system images, TUF, threshold signing | R | **ACCEPTED** | `UPDATE-MODEL.md` | M5 | key custody |
| SBOM + SLSA provenance | R | **DEFERRED** | `SUPPLY-CHAIN.md` | M5 | — |

## 4. Graphics, UI, media

| Requirement | Source | Status | Related | Horizon | Unresolved |
|---|---|---|---|---|---|
| User-space GPU driver + minimal kernel mediation | R | **PROPOSED** | `GRAPHICS-STACK.md` | M6 | vendor cooperation — **highest technical risk** |
| Native display protocol; Wayland as *compatibility* endpoint | R | **PROPOSED** | `GRAPHICS-STACK.md`, `UI-PLATFORM.md` | M6 | — |
| Custom UI toolkit with accessibility contract | R, B | **PROPOSED** | `UI-PLATFORM.md` | M6 | rendering strategy |
| Text: Unicode, shaping, fallback, bidi, variable fonts | R | **PROPOSED** | `TEXT-ARCHITECTURE.md` | M6 | reuse HarfBuzz/FreeType-class |
| Three-tier customization (declarative / sandboxed / developer) | R | **ACCEPTED** | `UI-PLATFORM.md` | M7 | — |
| Media graph; hardware encode/decode; HDR | R | **PROPOSED** | `MEDIA-FRAMEWORK.md` | M6 | codec licensing |
| Per-app audio routing without virtual-cable workarounds | R | **PROPOSED** | `AUDIO-GRAPH.md` | M6 | — |
| Broadcast: scenes, capture, multitrack, replay buffer, plugins out-of-process | R | **PROPOSED** | `BROADCAST-ARCHITECTURE.md` | post-M7 | plugin runtime choice |
| Files: enumerate → render → enrich asynchronously | R | **ACCEPTED** | `FILES-ARCHITECTURE.md` | M7 | index scope defaults |

## 5. Security, compatibility, cloud, enterprise

| Requirement | Source | Status | Related | Horizon | Unresolved |
|---|---|---|---|---|---|
| Shield: prevent / detect / contain / recover | R | **PROPOSED** | `SHIELD-ARCHITECTURE.md` | M7+ | engine dependencies |
| Kernel `SecurityEventStream` for EDR | R | **PROPOSED** | `SHIELD-ARCHITECTURE.md` | M7+ | event set — **constrains M2–M4** |
| Ransomware containment; snapshots not app-deletable | R | **PROPOSED** | `SHIELD-ARCHITECTURE.md`, `BACKUP-ARCHITECTURE.md` | M7+ | — |
| Linux: VM → personality → desktop compat | R | **ACCEPTED** | `LINUX-STRATEGY.md` | post-M7 | ioctl breadth |
| Windows: Wine/Proton/DXVK/vkd3d on the Linux personality | R | **ACCEPTED** | `WINDOWS-STRATEGY.md` | post-M7 | NT sync primitives in kernel |
| Android: VM first; personality only if justified | R | **ACCEPTED** | `ANDROID-STRATEGY.md` | far post-M7 | — |
| Gaming: Vulkan, latency, frame pacing; anti-cheat needs vendors | R | **PROPOSED** | `GAMING-PLATFORM.md` | post-M7 | anti-cheat — **not promised** |
| Account/Device/App/Publisher/Org identities kept distinct | R | **ACCEPTED** | `ACCOUNT-ARCHITECTURE.md` | post-M7 | — |
| Sync ≠ Backup; E2E encrypted; per-category | R | **ACCEPTED** | `SYNC-ARCHITECTURE.md`, `BACKUP-ARCHITECTURE.md` | post-M7 | key recovery — **UNSOLVED** |
| Link: QUIC, local-first, blind relay, cross-OS | R | **PROPOSED** | `LINK-PROTOCOL-ARCHITECTURE.md` | post-M7 | iOS platform limits |
| Store optional; alternative stores supported | R | **ACCEPTED** | `STORE-ARCHITECTURE.md` | M7+ | — |
| Organizations: RBAC, SSO/OIDC/SAML/SCIM, MDM, work profiles | R | **PROPOSED** | `ORGANIZATIONS-ARCHITECTURE.md` | far post-M7 | BYOD boundary enforcement |
| Company policy scoped to company-managed state only | H | **ACCEPTED** | `ORGANIZATIONS-ARCHITECTURE.md` | far post-M7 | technical enforcement |
| Open-core licensing | R | **DEFERRED** | `LICENSING-STATUS.md` | before any public release | codec patents |
| Monetization separated from surveillance | R | **DEFERRED** | — | far post-M7 | out of engineering scope |

## 6. Requirements the founder vision states that this map deliberately down-ranks

Recorded so they are visibly deferred rather than quietly dropped:

| Item | Why down-ranked |
|---|---|
| Illustrative calendar timeline | Dates on unstarted kernel work are guesses presented as plans; the roadmap is dependency-gated instead. |
| Named Shield engines (YARA-X, ClamAV, Suricata) | Post-M7 dependency choices; naming them now fixes decisions years early. |
| Mobile and Console products | Documented as compositions; no source, no manifests, until Desktop is real. |
| Full Android personality | The report itself says not to make it a 1.0 prerequisite. |
| Office file-format engines | Reuse is the plan; see `OFFICE-STRATEGY.md`. Writing OOXML parsers from zero is not. |
| Hosted Mail, cloud AI, Broadcast relay | Services, not platform. They cannot constrain M1–M4. |

## 7. What this map is for

When any planned component is named, this map answers *where the requirement came from,
what its current status is, which document owns it, and what must be decided before it can be
built.* If a component cannot be found here or in
[`PLATFORM-CAPABILITY-MAP.md`](../architecture/PLATFORM-CAPABILITY-MAP.md), it has not been
architected — and that is a finding, not an omission to paper over.
