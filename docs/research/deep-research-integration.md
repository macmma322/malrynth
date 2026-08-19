# Deep Research Report — Integration Record

**Status:** LOCKED (this record); the decisions it feeds are individually labelled.
**Date:** 2026-08-19
**Source:** *Malrynth OS: Architecture, Security, Compatibility, Ecosystem, and Production
Roadmap for a Truly Custom Operating System* — founder-supplied research report, 3,821 lines.

This document records what the report changed, what it confirmed, what was deliberately not
adopted, and where it conflicts with what is already built. It exists so that a future reader
can tell which decisions came from evidence and which came from a document.

---

## 1. Where the report and the existing foundation independently agreed

The repository's architecture was written before this report was supplied. The two converged
on the following without contact, which is the strongest signal in the report:

| Decision | Both reached |
|---|---|
| Kernel shape | Capability-oriented **hybrid** microkernel, not pure micro, not monolithic |
| Language | Rust-first, minimal assembly, C only for interop; "Rust ≠ secure" stated explicitly |
| Authority | No ambient authority; explicit handles with per-handle rights |
| Drivers | User-space by default; IOMMU-confined DMA; in-kernel drivers require written justification |
| Linux | Development host, compatibility target, possible driver VM — **never** the production kernel |
| Boot | UEFI application loader; no legacy BIOS; owner-controlled Secure Boot later |
| Graphics | Vulkan-first, native compositor, user-space GPU service |
| Updates | A/B slots, signed, transactional, rollback-gated |
| Compatibility | Linux/Windows/Android staged VM → personality, always *above* the kernel |
| Packages | Immutable, signed, content-addressed, explicit capability manifests |
| Supply chain | Pinned toolchain, TUF-style repository, SLSA provenance, reproducible builds |
| Filesystem | MalrynthFS is R&D; must not be the default for years |
| Governance | Written constitution predating commercial pressure |

Convergence is evidence, not proof — both derivations share the founder's premises. But the
agreement means the architecture in `docs/architecture/` is not an accident of one pass.

---

## 2. Genuine gaps the report exposed — now closed

The report's own M0 checklist listed two items the implementation did not have. Both were
in scope for M0 and both are now implemented and tested.

### 2.1 "basic symbolized stack trace" — was missing, now implemented

A kernel that panics without saying where is a kernel that cannot be debugged.

Implemented as `core/kernel/src/debug/` (frame-pointer walk, every frame validated) plus
`tools/symbolize` (host-side ELF symbol resolution). Symbolisation is deliberately **not** in
the kernel: it would put a DWARF parser in ring 0 and tens of kilobytes in every shipped image
to serve a case only a developer reads.

Verified by `tools/check-panic-path`, which builds a `panic-test` kernel, boots it, and asserts
the panic is reported with a source location, a multi-frame backtrace is printed, the failure
marker is emitted, the success marker is **not**, and `tools/symbolize` resolves frames.

### 2.2 "deterministic build" — was measurably failing, now verified

Previously recorded honestly as *"verified NOT to hold"*: the same commit built at two paths
produced kernels differing by the embedded build-path length.

Three distinct causes were found and fixed:

| Cause | Fix |
|---|---|
| Absolute source/registry/sysroot paths in DWARF | `--remap-path-prefix` for all three roots |
| PE `TimeDateStamp` stamped with wall-clock time | `/Brepro` (content hash instead) |
| PE debug directory CodeView GUID derived from a PDB embedding path-dependent object paths | `/DEBUG:NONE` for the loader; the kernel keeps full DWARF |

Both images are now byte-identical across build directories, enforced by
`tools/check-reproducible` in `tools/test` and CI. A reproducibility claim without a test is a
wish — that is now a test.

---

## 3. Adopted into the architecture (documentation only, no code)

| Adopted | Where recorded | Status |
|---|---|---|
| Kernel object namespace (`Job`…`ExceptionPort`) | [ADR-0004](../adr/ADR-0004-kernel-object-model.md) | PROPOSED |
| Rights vocabulary (12 rights, attenuation-only) | ADR-0004, `CAPABILITY-MODEL.md` | PROPOSED |
| `mly_<object>_<verb>` syscall naming | ADR-0004, `specs/naming.md` | PROPOSED |
| Three IPC classes incl. **shared rings** as a first-class third class | `IPC-MODEL.md` | PROPOSED |
| `.mpk` package format; `/package /config /data /cache /temp /secrets` layout | `specs/naming.md` | PROPOSED |
| Proposed performance gates (IPC, context switch, boot, idle, app launch…) | `performance/PERFORMANCE-CONSTITUTION.md` | PROPOSED |
| "Boring subsystems" coverage (power, thermal, time, text, input, locale, printing, firmware, secrets, multi-user, diagnostics, virtualization) | `roadmap/SUBSYSTEM-COVERAGE.md` | PROPOSED |
| Release artifact naming (Kernel Developer Preview → Developer OS → Desktop 1.0) | `roadmap/README.md` | PROPOSED |
| Effort estimates and risk register | `roadmap/EFFORT-AND-RISK.md` | PROPOSED |
| Standards versions (UEFI 2.11, ACPI 6.6, NVMe 2.3, Vulkan 1.4, SLSA 1.2, NIST SP 800-218) | relevant docs | reference |

### The single most useful non-technical item

> **Scope explosion is rated the highest management risk — above every technical risk.**

The report observes that Malrynth currently contains enough ideas for a desktop OS, server OS,
mobile OS, console OS, office suite, mail client, cloud provider, MDM platform, EDR platform,
streaming suite, developer suite, sync platform and game-compatibility platform. This is
recorded in `roadmap/EFFORT-AND-RISK.md` because it is the risk most likely to actually
materialise, and the one a repository structure can genuinely help control.

---

## 4. Deliberately NOT adopted

| Not adopted | Why |
|---|---|
| The illustrative Gantt timeline (M0 Oct 2026 + 5 months, …) | Dates on unstarted kernel work are guesses presented as plans. The roadmap stays dependency-ordered. The report itself calls it "not a promise". |
| Creating `products/`, `ui/`, `apps/`, `sdk/`, `compat/` trees | ADR-0001 is unchanged by this report: no component satisfies a split criterion, and empty trees are not architecture. |
| The open-core licensing recommendation as a *decision* | Recorded as an input in `legal/LICENSING-STATUS.md`. Licensing remains UNRESOLVED; a license granted cannot be revoked, and nothing forces the choice yet. |
| Monetization model | Out of scope for an engineering foundation. Recorded as context only. |
| Specific Shield engine choices (YARA-X, ClamAV, Suricata) | Post-M7. Naming engines now would be a dependency decision made years before the requirement exists. |
| Zircon's full object set | ADR-0004 adopts the subset with a stated role; the rest can be added when something needs them. |

---

## 5. Conflicts and corrections

### 5.1 M0 scope: the report's M0 is larger than what was built in one session

This matters for honesty about pace. The report estimates M0 at roughly five months for
three to six experienced engineers. The M0 completed here was finished far faster because it
is **narrower**, not because it was done faster:

| Report M0 item | Status here |
|---|---|
| `malboot.efi`, kernel loader, kernel entry, serial console | done |
| UEFI memory map capture, `ExitBootServices`, panic handler | done |
| GOP framebuffer | **discovered and reported, deliberately not drawn to** (drawing is M6) |
| Basic symbolized stack trace | done (§2.1) |
| Deterministic build | done (§2.2) |
| QEMU CI boot test | done |

The remaining difference is real: this M0 has no physical-hardware bring-up, no
symbol-server or crash-dump infrastructure, and one virtual reference platform rather than a
selected physical one. `roadmap/M0.md` records this explicitly rather than implying parity.

### 5.2 Third IPC class: "asynchronous notification" → "shared rings"

`IPC-MODEL.md` originally listed the third mechanism as asynchronous notification. The report
is right that **shared descriptor rings** are the architecturally significant third class:
they are what makes sustained networking, audio and device queues viable, and they have
different lifetime and backpressure properties from either channels or one-shot notifications.
Notification remains, but as a signalling primitive rather than a bulk-transport class.

### 5.3 Rights vocabulary was under-specified

`CAPABILITY-MODEL.md` listed a shorter, ad-hoc rights list. Replaced by ADR-0004's vocabulary.

### 5.4 The report's success banner differs cosmetically

The report shows `Malrynth Kernel 0.0.1 / CPU: x86_64 / Memory map received / …`; the
implementation emits the format from the founding brief. **No change made** — the brief is the
governing specification for M0 output, and the machine-checked contract is the exact marker
`MALRYNTH_M0_BOOT_OK`, not the banner text.

---

## 6. What this record does not do

It does not promote any architecture document from PROPOSED to LOCKED. Nothing in the report
is *evidence* about Malrynth — it is a well-reasoned design argument. Promotion requires
something built, measured, and attacked.

The two items that changed status did so because they were **implemented and tested**, not
because the report described them.
