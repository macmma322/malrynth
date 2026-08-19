# Graphics Stack

**Status:** PROPOSED. GPU driver strategy is [Q3](../architecture/OPEN-QUESTIONS.md) —
**the highest technical risk in the project.**

## Stack

```
application / game / compositor
        │  Vulkan
        ▼
Vulkan loader  ──> vendor ICD                       L5, per-process
        │  Malrynth GPU protocol
        ▼
GPU system driver   contexts · GPU VM · queues · fences · buffers   L4, unprivileged
        │  MMIO + IRQ + DMA capabilities
        ▼
kernel GPU mediation   minimal privileged surface only              L2
        │  IOMMU-confined
        ▼
GPU hardware
```

The kernel's role is deliberately tiny: map MMIO, deliver interrupts, program the IOMMU,
arbitrate. **Command submission, memory management and scheduling live in the user-space
driver.** If GPU logic starts migrating into the kernel, the driver model has failed.

## Vulkan first

Vulkan is the primary explicit graphics API. It is a Khronos standard with a conformance test
suite (CTS), which gives a new OS something rare: an objective external measure of correctness.
The CTS becomes part of the continuous graphics test farm.

OpenGL arrives later as a translation layer over Vulkan (Zink-class), not a native
implementation — the compatibility value does not justify a second native driver path.

## The hard problem

Every route is bad in a different way:

| Route | Cost |
|---|---|
| Write drivers from scratch | Enormous; vendor hardware knowledge is not public |
| Port Mesa drivers | Real hardware knowledge, but they assume Linux DRM/KMS, `ioctl` conventions and Linux memory semantics |
| Vendor cooperation | Best outcome; cannot be assumed by a new OS with no users |
| virtio-gpu only | Works in VMs; not a product |

**Current inclination:** virtio-gpu first for M6 bring-up, then port a Mesa-derived Vulkan
driver for one open, well-documented family (AMD or Intel), then a second, and only then
consider NVIDIA. Supporting every family at once is a resource trap.

The decisive unknown — how much of a Mesa Vulkan driver is genuinely
kernel-interface-independent — must be answered by a spike, not by estimate.

## Display protocol: native, with Wayland as compatibility

Malrynth's compositor speaks a **native, capability-oriented surface protocol**. Wayland is
supported as a *compatibility endpoint* for Linux GUI applications.

This ordering matters. Adopting Wayland as the native protocol would import its authority
assumptions and constrain capability integration permanently. A Wayland endpoint above a native
protocol keeps Linux applications working without making Malrynth's UI a Linux UI.

## Compositor authority

The compositor owns display, window placement, composition, HDR, VRR, colour management, input
routing, and — critically — **screen-capture authorisation**.

Capture is a capability, never implicit. This is what allows Broadcast to exist without
allowing every application to watch the screen, and it must be designed into the compositor
from the first commit rather than added later.

## Surfaces and buffers

Buffer sharing between application, compositor, media and capture uses Vulkan's standardised
external-memory mechanisms, so no Malrynth-specific sharing protocol is needed. Hardware video
encode/decode targets Vulkan Video, which keeps the media path inside the same standard.

## Depends on / blocks

**Depends on:** IOMMU (M4), memory objects (M3), display driver.
**Blocks:** compositor, UI toolkit, every GUI application, gaming, hardware media encode —
i.e. most of the visible product. This is why Q3's deadline is the start of M6, and why the
spike should happen earlier.
