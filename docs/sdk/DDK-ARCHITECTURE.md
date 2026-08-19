# DDK Architecture

**Status:** PROPOSED. Target: M4 (internal), M7 (public).

## Why the DDK is a product decision, not a documentation task

Vendors will not write Malrynth drivers because we ask. They need users, stable contracts,
excellent tooling and a support organisation. The DDK is the contract half of that, and its
quality determines whether third-party hardware support is ever possible.

## Driver context

A driver is an unprivileged user-space program (L4) that receives:

```
Device            identity, config space access (scoped)
IoRegion          MMIO mapping capability for its BARs only
Interrupt         IRQ delivery as messages
DmaDomain         IOMMU-confined DMA
Firmware          blob access capability
Power             D-state transitions
```

and **does not** receive: arbitrary physical memory, other devices, kernel memory, other
processes' memory, full PCI config space, or unrestricted I/O ports.

## Illustrative API

```rust
let dev  = ctx.device();
let bar0 = dev.map_io_region(PciBar::Bar0, Rights::READ | Rights::WRITE)?;
let irq  = dev.bind_interrupt(InterruptMode::Msix { vector: 0 })?;
let dma  = dev.create_dma_domain()?;

let buffer  = MemoryObject::new(4 * 1024 * 1024)?;
let mapping = dma.map(&buffer, DmaRights::DEVICE_READ | DmaRights::DEVICE_WRITE)?;
```

## Contents

| Area | Contents |
|---|---|
| Framework | Rust driver runtime; stable C ABI for vendor code |
| Bus support | PCI/PCIe, USB helpers |
| Resources | MMIO, IRQ, DMA, IOMMU APIs |
| Power | Suspend, resume, runtime D-states, hotplug |
| Protocols | Typed device-class protocol definitions |
| Diagnostics | Logging, tracing, crash-dump format |
| Testing | Virtual device simulators, conformance suite, **fuzzing harness** |
| Signing | Development and production driver signing |

## Failure model

```
driver faults → kernel revokes IRQ → IOMMU mappings torn down
   → device reset → driver manager restarts → clients reconnect
```

**This is the normal path, not an exceptional one.** A driver crash must be as routine as an
application crash; if it is not, the user-space driver model has not delivered its main benefit.

## In-kernel exceptions

Permitted only where the boundary cannot exist — interrupt controller, timer, early debug
output — and each requires an ADR answering: why not user space, which benchmark proves it,
what privileges are needed, what fuzzing exists, what the rollback plan is.

M0's 16550 UART is currently such an exception and is documented in-source as moving to user
space once the driver framework exists.

## Vendor reality

Early hardware strategy selects **specific supported devices** rather than promising "PC
compatibility". A short certified list that genuinely works beats a long list that mostly does
not — see [`EFFORT-AND-RISK.md`](../roadmap/EFFORT-AND-RISK.md).
