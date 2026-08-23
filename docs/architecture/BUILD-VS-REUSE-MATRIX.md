# Build vs Reuse Matrix

**Status:** ACCEPTED as direction. Individual rows carry their own status and several are
UNSOLVED.

## The principle

> **Be custom where ownership of the architecture matters. Do not reinvent mathematics,
> standards and mature libraries to satisfy a purity test.**

UEFI can boot Malrynth. ACPI can describe its hardware. NVMe can define its storage protocol.
Vulkan can define its graphics API. LLVM can compile its C++. QUIC can transport Link. TUF can
secure its repository. **None of that makes Malrynth less custom** — those are standards and
interfaces, not host operating systems.

What makes Malrynth independent is that when firmware calls into it, the machine runs
Malrynth's scheduler, memory manager, object model, capability enforcement, IPC, driver
isolation, services, compositor and policy.

## The test applied to every row

**Build custom when** the component *is* the architecture (authority, isolation, scheduling,
composition), or when reuse would import a foreign security model.

**Reuse when** the component is a standard, a mathematical primitive, or a mature body of
work whose correctness is expensive and whose replacement carries no architectural benefit —
especially anything that parses untrusted input, where a hand-rolled version is a
vulnerability.

**Port when** existing work encodes hardware knowledge we cannot re-derive (GPU drivers,
filesystem formats) but whose host assumptions must be replaced.

**Wrap when** we need a foreign component's behaviour behind a Malrynth-shaped boundary.

---

## Kernel and core platform — CUSTOM, without exception

| Component | Decision | Reason | Licence | Trust impact | Replaceable later? |
|---|---|---|---|---|---|
| Kernel (memory, sched, objects, caps, IPC) | **Custom** | This *is* Malrynth. Reuse means being another OS. | ours | TCB | no |
| Boot loader (`malboot`) | **Custom** (uses `uefi` crate) | Owns handoff and boot policy; firmware bindings reused | MIT/Apache-2.0 | boot-time only | yes |
| Driver framework | **Custom** | Encodes the capability/IOMMU model | ours | defines TCB edge | no |
| Component manager | **Custom** | Capability routing is the security architecture | ours | high | no |
| Package + update system | **Custom** | Integrates identity, capabilities, A/B, rollback | ours | high | no |
| Native shell, Files, Settings | **Custom** | Product identity; benchmark for quality | ours | unprivileged | yes |
| Scheduler policy | **Custom** | Determines latency character | ours | TCB | no |

## Toolchain — REUSE, without exception

| Component | Decision | Reason | Licence | Notes |
|---|---|---|---|---|
| rustc / Cargo | **Reuse** | Writing a compiler is a separate decade-long project | Apache-2.0/MIT | Tier-3 target is the integration path |
| LLVM / Clang | **Reuse** | Same, plus C/C++ support comes free | Apache-2.0 w/ LLVM exception | |
| lld | **Reuse** | Already bundled with Rust; no system linker needed | Apache-2.0 w/ exception | in use at M0 |
| LLDB | **Reuse** | gdb-remote protocol is a clean integration point | Apache-2.0 w/ exception | |
| CMake / Meson / Ninja | **Reuse** | Third-party C/C++ expects them | permissive | SDK support, not Malrynth's own build |

**A custom compiler is explicitly rejected.** "Custom OS" means our kernel, platform, ABI and
runtime — not replacing LLVM.

## Runtime — the hardest column

| Component | Decision | Reason | Licence | Trust | Status |
|---|---|---|---|---|---|
| libc | **Port or custom** | See [Q1](OPEN-QUESTIONS.md). musl is complete but Linux-shaped; LLVM libc's full build is static-only with no dynamic loader | MIT (musl) / Apache-2.0 (LLVM) | in every process | **UNSOLVED** |
| POSIX facade | **Custom** | Must hold capabilities on the program's behalf — no existing implementation does this | ours | per-process | PROPOSED |
| Rust `std` port | **Port** | Upstream `std` with a Malrynth backend | Apache-2.0/MIT | per-process | DEFERRED |
| Dynamic loader | **Custom** | Must integrate W^X, capabilities and package layout | ours | per-process | PROPOSED |
| ELF format | **Reuse (standard)** | Inventing a binary container buys nothing | spec | — | PROPOSED |
| Crypto primitives | **Reuse** | Hand-rolled crypto is a vulnerability. Full stop. | varies | high | PROPOSED |
| TLS | **Reuse** | Same reasoning; protocol complexity is extreme | varies | high | PROPOSED |
| QUIC | **Reuse** | Mature Rust implementations exist | permissive | medium | PROPOSED |

## Graphics — where reuse is unavoidable and uncomfortable

| Component | Decision | Reason | Licence | Trust | Status |
|---|---|---|---|---|---|
| GPU driver | **Port (Mesa-derived)** | Vendor hardware knowledge cannot be re-derived; the cost is untangling Linux DRM/KMS assumptions | MIT-ish | unprivileged (L4) | **UNSOLVED** |
| Vulkan loader | **Reuse** | Khronos standard component | Apache-2.0 | per-process | PROPOSED |
| Vulkan ICD | **Port** | Ships with the driver | MIT-ish | per-process | UNSOLVED |
| OpenGL | **Reuse** (Zink-class over Vulkan) | Not worth a native implementation | MIT | per-process | DEFERRED |
| Compositor | **Custom** | Owns display, input routing and **capture authority** — a security boundary | ours | L3 | PROPOSED |
| Display protocol | **Custom** | Capability-oriented; Wayland is a *compatibility endpoint*, not our protocol | ours | L6 | PROPOSED |

## Text, i18n, media — reuse strongly favoured

| Component | Decision | Reason | Licence |
|---|---|---|---|
| Unicode data | **Reuse** | It is a data standard | Unicode licence |
| Text shaping (HarfBuzz-class) | **Reuse** | Complex scripts are a research field; getting this wrong breaks languages | MIT |
| Font rasterisation (FreeType-class) | **Reuse** | Decades of hinting and format edge cases | FTL/GPL dual |
| Locale data (CLDR/ICU-class) | **Reuse** | Data standard | Unicode licence |
| Codecs | **Reuse** | Enormous, patent-encumbered, security-critical. **Never write from scratch.** | varies — **patent review required** |
| Containers/muxers | **Reuse** | Format complexity, low architectural value | varies |
| Image decoders | **Reuse**, sandboxed | Classic exploit surface; run out-of-process | varies |
| Media graph | **Custom** | Routing, capabilities and per-app audio are the architecture | ours |
| Audio graph | **Custom** | Per-app routing without virtual-cable workarounds is a product differentiator | ours |

## Storage

| Component | Decision | Reason | Status |
|---|---|---|---|
| VFS protocol | **Custom** | Capability-oriented; no existing VFS is | ACCEPTED |
| Block/volume layer | **Custom** | Small, tied to driver model | ACCEPTED |
| FAT/exFAT | **Custom or reuse** | Simple, well-documented; ESP requirement | ACCEPTED |
| ext / NTFS | **Port**, read-only first | Format knowledge is real; run **in user space**, never in the kernel | DEFERRED |
| MalrynthFS | **Custom** | Long-term native FS matching Malrynth semantics | EXPERIMENTAL |
| Full-disk encryption | **Custom** integration, **reused** crypto | Algorithms reused, policy ours | PROPOSED |

## Compatibility — reuse is the entire strategy

| Component | Decision | Reason | Licence |
|---|---|---|---|
| Wine | **Reuse** | Reimplementing the Win32 API is not viable | LGPL — **obligations to review** |
| Proton / DXVK / vkd3d | **Reuse** | Mature D3D→Vulkan translation | zlib / LGPL |
| Linux guest kernel (VM) | **Reuse** | Correctness-first compatibility path | GPL-2.0 — **guest only, never underneath** |
| virtio | **Reuse (spec)** | Standard paravirtual interface | spec |
| Linux personality | **Custom** | Translation into Malrynth capabilities | ours |
| VMM | **Custom** | Small, integrates with our IOMMU and capability model | ours |

**Licence caution:** Wine is LGPL and the Linux guest is GPL-2.0. Neither infects Malrynth as
long as they remain separate processes or guests — but this must be reviewed before
distribution, not after, and it interacts with [Q13](OPEN-QUESTIONS.md).

## Applications

| Component | Decision | Reason |
|---|---|---|
| Files, Settings, Search, Monitor, Terminal | **Custom** | Product identity and quality benchmark |
| Browser | **Custom UI over a reused engine** | Writing a modern engine is out of scope; see [`BROWSER-STRATEGY.md`](../apps/browser/BROWSER-STRATEGY.md) |
| PDF | **Custom UI over a reused engine** | Format complexity, security surface |
| Write / Sheets / Present | **Custom UI over reused format engines** | Never write OOXML/ODF parsers from zero |
| Photos / Video / Music | **Custom UI over reused codecs** | |
| Broadcast | **Custom** | Depends on native capture, per-app audio and GPU encode — the platform must supply these |
| Shield scanners | **Reuse**, heavily sandboxed | Detection content is an ongoing intelligence problem, not a one-time build |

## Rules that fall out of this matrix

1. **Never hand-roll:** cryptography, TLS, codecs, text shaping, Unicode, font rasterisation.
   Each is a place where a bespoke implementation is strictly worse.
2. **Never reuse:** the kernel, capability enforcement, IPC, component manager, package
   system, compositor authority. Reusing these means adopting someone else's security model.
3. **Every reuse gets a ledger entry** in `THIRD_PARTY.md` before it is committed: source,
   licence, purpose, whether privileged, and modifications.
4. **Anything parsing untrusted input runs unprivileged and sandboxed**, whether custom or
   reused.
5. **Reuse decisions are revisitable.** Each row records replaceability, because "we reused X"
   should never become "we can never change X".
