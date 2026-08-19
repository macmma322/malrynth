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

## Structure (when it exists)

Product definitions will live under `products/` in this repository, as manifests:

```
products/
  desktop/    manifest, packages, policy, profiles
  server/     manifest, packages, policy, profiles
  mobile/     FUTURE.md
  console/    FUTURE.md
```

The directory is **not created yet**, because at M0 there are no services, packages or
policies to compose and an empty tree of manifests would express a roadmap, not a system.
`manifests/products/` in this repository records the intended composition axes until then.

Mobile and Console will begin as a single document each. Creating source trees for them
before Desktop boots would be scaffolding for an unwritten system.
