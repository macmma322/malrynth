# Driver Model

**Status:** PROPOSED. Not implemented. Target: M4.

## Principle

**Drivers run in user space by default.** A driver is an ordinary program that happens to
hold capabilities to an MMIO range, an interrupt, and a DMA-capable memory region.

Drivers are the largest, least reviewed, most hardware-specific body of code in any
operating system, and in a monolithic kernel each one is a potential full compromise. Moving
them out is the single largest reduction in trusted computing base available, and it is only
achievable if it is the default from the start.

## Confinement

- **MMIO** is granted as a mapped capability to a specific physical range, not as arbitrary
  physical memory access.
- **Interrupts** are delivered as messages to a driver's handler thread; the kernel
  acknowledges the controller, the driver handles the event.
- **DMA is confined by the IOMMU where hardware permits.** A device may only reach memory its
  driver was explicitly granted. Without an IOMMU, a device is fully trusted — Malrynth must
  say so plainly rather than imply protection it does not have. See
  `docs/security/THREAT-MODEL.md` on DMA attacks.
- A driver crash is contained and restartable. Losing a device is not losing the system.

## Where in-kernel drivers are permitted

Only where the boundary cannot exist: the interrupt controller, the timer, and early debug
output. Each is an explicit, enumerated exception requiring an ADR — not a category that
grows.

M0's 16550 UART driver is in the kernel under this exception. It is a debug facility, and it
is documented in-source as moving to user space once the driver framework exists.

## Linux driver compatibility

An isolated Linux driver-compatibility domain is a **possible future**, not a plan, and
would run Linux drivers in a confined VM whose DMA is IOMMU-restricted. It must never become
a path by which Linux code ends up beneath the Malrynth kernel. Recorded here so the
distinction is not lost later.
