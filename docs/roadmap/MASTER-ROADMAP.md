# Master Roadmap

**Status:** ACCEPTED. **Dependency-gated, not calendar-gated.**

M0–M7 are preserved unchanged and placed inside broader horizons, so that everything beyond M7
has a home rather than living as loose ambition.

## Why no dates beyond the immediate

A date on unstarted kernel work is a guess presented as a plan. Every gate below is a
**condition**, and the conditions come from
[`DEPENDENCY-GRAPH.md`](../architecture/DEPENDENCY-GRAPH.md).
[`EFFORT-AND-RISK.md`](EFFORT-AND-RISK.md) gives order-of-magnitude effort for scoping.

## Horizons

| Horizon | Contents | Gate to exit |
|---|---|---|
| **H0 — Foundation** | M0 · **H0.5 architecture** | Kernel boots and is verified; platform architecture specified end to end |
| **H1 — Kernel ownership** | M1 · M2 · M3 | Malrynth owns memory, CPU, scheduling and **authority**. Capability invariants hold under adversarial test |
| **H2 — Hardware** | M4 | Real hardware runs: ACPI, PCIe, IOMMU, NVMe, USB, Ethernet. A malicious driver cannot DMA outside its domain |
| **H3 — Command-line OS** | M5 | Self-hosting text-mode system: VFS, loader, libc, netstack, packages, transactional updates, offline recovery |
| **H4 — Graphical platform** | M6 | Compositor presents at refresh rate; Vulkan conformance; audio latency met |
| **H5 — Developer OS** | M7 | Malrynth is a usable daily development machine **for its own developers**; a third party can build and ship an app from published docs |
| **H6 — Native app ecosystem** | Application suite, Store, SDK maturity | Third-party applications exist that were not written by us |
| **H7 — Compatibility & gaming** | Linux personality, Wine/Proton, gaming stack | A meaningful corpus of existing software runs |
| **H8 — Account, Store, Link** | Optional cloud | Everything remains fully usable offline |
| **H9 — Server & enterprise** | Server composition, Organizations, MDM, EDR | Server product runs real workloads |
| **H10 — Mobile** | Mobile composition | Shares one core; no second kernel |
| **H11 — Console** | Console composition | Shares one core; no second kernel |

## Current position

```
H0  ████████████████████░  M0 complete · H0.5 architecture complete
H1  ░░░░░░░░░░░░░░░░░░░░  next: M1
H2+ ░░░░░░░░░░░░░░░░░░░░
```

## Release artifacts

| Artifact | Contents | Honest claim |
|---|---|---|
| **Malrynth Kernel Developer Preview** | H1–H2 | A real custom kernel with capabilities, IPC, user-space drivers, IOMMU confinement. Not a usable OS. |
| **Malrynth Developer OS** | H3–H5 | Self-hosting, then a developer desktop |
| **Malrynth Desktop 1.0** | H6+ with certification | A daily driver on certified hardware |

**The first public artifact is not called 1.0.** Naming an early kernel "1.0" commits to
guarantees nothing has earned.

## Cross-horizon work

Some work spans horizons and must not wait for its "own" milestone:

| Work | Spans | Why early |
|---|---|---|
| Driver framework and hardware lab | H2 → H6 | Hardware support is continuous, not a phase |
| MalrynthFS research | H2 → H9 | Must mature for years before becoming default |
| Supply chain, signing, reproducibility | H0 → ongoing | Already partly in place at M0 |
| Security event design | H1 (M3) | EDR observability must be designed with the object model, never retrofitted |
| Accessibility | H4 onward | Retrofitted accessibility is always poor |
| Performance budgets | H1 onward | A budget defined after implementation is a description |

## The rule that keeps this honest

**A horizon is not entered because the previous one took long enough.** It is entered when its
gate is met — and if a gate cannot be met, the correct response is to say so, not to redefine it.
