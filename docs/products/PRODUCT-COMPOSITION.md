# Product Composition

**Status:** PROPOSED. No product exists. Target: M7 (Desktop), later for the rest.

## Principle

Desktop, Server, Mobile and Console are **compositions of one platform**, never separate
operating systems. There is one kernel, one ABI, one driver framework, one service model.

Four kernels would mean four times the security surface, four divergent ABIs, and bugs fixed
three times out of four. This is the failure mode most likely to end the project, so the
constraint is architectural rather than aspirational: **`core/` contains nothing
product-specific.** Product identity lives entirely in composition.

## What a product selects

| Axis | Question |
|---|---|
| Shell | Which UI shell and session model, or none (Server). |
| Services | Which system services start, and in what dependency order. |
| Drivers | Which driver profile — desktop PC, server platform, SoC, console hardware. |
| Policy | Security defaults: update policy, sideloading posture, network exposure. |
| Packages | The package set installed by default. |
| Updates | Which channel and cadence. |
| Performance | Which budget profile applies (see `docs/performance/`). |
| Hardware | Which platform/board definitions are in scope. |

## What a product must NOT contain

- Kernel code. Kernel differences would create four kernels by accretion.
- Driver implementations. Hardware support belongs to the driver layer, shared by all
  products; a driver written for Desktop must work for Server unchanged.
- Forked services. A service that needs to differ takes configuration, not a fork.

## Product definitions

Each product answers the same eight questions. Nothing else distinguishes them, and nothing
below implies separate source trees.

### Malrynth Desktop — the first product (M7)

| Axis | Choice |
|---|---|
| Shell | Malrynth desktop shell, windowed, keyboard-first |
| Services | Full graphical set: compositor, audio, input, index, notifications |
| Drivers | Desktop PC profile: NVMe, xHCI, HID, Ethernet, discrete/integrated GPU |
| Policy | Sideloading allowed, developer mode available, firewall default-deny inbound |
| Packages | Files, Settings, Search, Terminal, Monitor, Shield baseline, package installer |
| Updates | A/B, user-scheduled, rollback enabled |
| Performance | Interactive profile: input-to-photon and app-launch budgets dominate |
| Hardware | Certified desktop motherboards first. **Not laptops** — firmware quirks, power states, embedded controllers, dual GPUs and suspend/resume make them the hardest possible first target |

### Malrynth Server — post-M7

| Axis | Choice |
|---|---|
| Shell | **None.** Remote management and console only |
| Services | Headless: no compositor, no audio, no desktop index |
| Drivers | Server profile: NVMe, multi-NIC, no GPU requirement |
| Policy | Hardened defaults, minimal package set, aggressive attack-surface reduction |
| Packages | Base system, container/VM tooling, remote management |
| Updates | Administrator-scheduled, staged across a fleet |
| Performance | Throughput and tail-latency profile; interactive budgets do not apply |
| Hardware | Server platforms with IOMMU, ECC, remote management |

Server is a **smaller** composition than Desktop, not a different system — it starts by
*removing* components, which is only possible because nothing in `core/` is desktop-specific.

### Malrynth Mobile — far post-M7

Touch-first shell, aggressive power management, cellular, sensors, a stricter default security
posture, and app lifecycle dominated by suspension. Requires mobile SoC support, which is a
hardware programme in its own right.

**No source, no manifests, until Desktop is real.**

### Malrynth Console — far post-M7

Gamepad-first shell, fixed certified hardware, a gaming-optimised performance profile, and
storage tuned for large titles. Depends on the entire gaming stack
([`GAMING-PLATFORM.md`](../gaming/GAMING-PLATFORM.md)).

**No source, no manifests, until Desktop is real.**

## What varies and what may never vary

| Never varies | May vary |
|---|---|
| Kernel | Shell and session model |
| Capability model and enforcement | Which services start |
| IPC and object model | Driver profile |
| Driver framework | Security policy defaults |
| Package format and update mechanism | Default package set |
| Security architecture | Update channel and cadence |
| ABI | Performance profile |

**If a product needs a kernel change, that change belongs to the kernel for every product.**
A product-specific kernel patch is the first step toward four kernels, and it is forbidden.

## Structure (when it exists)

Product definitions will live under `products/` as manifests:

```
products/
  desktop/    manifest, packages, policy, profiles
  server/     manifest, packages, policy, profiles
  mobile/     FUTURE.md
  console/    FUTURE.md
```

The directory is **not created yet**: at M0 there are no services, packages or policies to
compose, and a tree of manifests referencing nothing would express a roadmap while looking like
a build input. `manifests/products/` records the composition axes until then.
