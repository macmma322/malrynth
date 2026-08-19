# Isolated Linux driver-domain feasibility

## Scope

This evaluates a bootstrap/compatibility mechanism:

```text
Malrynth kernel / VMM
  ├─ IOMMU + interrupt remapping
  ├─ assigned whole PCI/USB-controller function
  └─ minimal Linux guest/domain
       ├─ vendor/Linux driver + firmware
       └─ virtio/shared-memory service exported to Malrynth
```

It is not permission to make Linux the production host kernel, and it is not the default native driver architecture.

## Prerequisites

- VMX/EPT or SVM/NPT virtualization and reliable VM-exit/interrupt injection
- VT-d/AMD IOMMU translation plus interrupt remapping
- safe whole-device/IOMMU-group assignment and reset
- a minimal Linux image, measured/versioned as a separate trust component
- shared-memory transport with ownership, feature negotiation, backpressure, reset, and authentication where needed
- Malrynth front-end driver (virtio-net/block/gpu/input or a deliberately similar protocol)
- lifecycle coordination: boot, firmware load, service-ready, crash, domain reset, device reset, remap, reconnect

VFIO is useful implementation evidence: direct assignment requires IOMMU-protected access and group ownership. It is not an interface Malrynth can simply call; Malrynth must implement the host-side equivalent.

## Device-class ranking

| Rank | Class | Feasibility | Export | Judgment |
|---:|---|---|---|---|
| 1 | Wi-Fi | high bootstrap value | virtio-net; keep supplicant/regulatory policy clearly placed | **BEST FIT** because native driver+firmware+wireless-stack cost is large and latency tolerance is reasonable |
| 2 | specialized USB peripheral via assigned controller | medium/high | protocol-specific service or virtio input/audio | **USEFUL** if a whole secondary xHCI controller and group can be assigned; never assign the boot keyboard controller |
| 3 | Bluetooth | medium | HCI proxy or higher-level service | **POSSIBLE**, but native USB HCI transport may be simpler; audio timing raises cost |
| 4 | NIC | medium technically, low strategic value | virtio-net | **BOOTSTRAP ONLY**; I210 native driver is simpler, faster to boot, and smaller TCB |
| 5 | GPU compute | medium for whole-device batch compute | virtio-gpu/compute RPC or mediated service | **NICHE**; reset, firmware, huge shared memory, and vendor user mode remain |
| 6 | GPU display | low | virtio-gpu scanout/shared surfaces | **POOR PRIMARY DISPLAY** due boot splash, modeset, latency, crash recovery, console circularity |
| 7 | storage | low strategic value | virtio-blk/scsi | **AVOID FOR ROOT/BOOT**; creates circular boot and data-integrity dependency; possible for secondary exotic storage only |

## Data paths

### NIC/Wi-Fi

Assign the entire adapter, let Linux run firmware/MAC/regulatory driver, and export virtio-net queues. Copies can be avoided with shared page pools, but ownership and IOMMU mappings become complex. Malrynth should own high-level connection policy only if a stable control protocol exists; otherwise the domain also contains supplicant/regulatory policy and expands the trust boundary.

### USB

Assign a secondary discrete xHCI controller, never individual USB devices behind a host controller Malrynth also owns unless hardware mediation is designed. Export HID/audio/device-specific data. Physical unplug and malicious descriptors attack the Linux domain, which is an isolation benefit, but the shared protocol parser remains exposed.

### GPU

Whole-GPU assignment gives Linux its normal DRM/vendor stack. Frames or render commands return through virtio-gpu-like shared memory. Problems: GOP-to-domain handoff, display ownership, GPU reset, multi-function groups, large pinned buffers, synchronization, proprietary userspace, latency, and loss of console when the domain crashes. Compute-only on a second GPU is more credible than primary display.

### Storage

The domain must boot before it can export storage, so it cannot host the only boot/root device without an initramfs/secondary store circularity. Flush/FUA, power loss, reset, and crash semantics must cross two kernels. Native NVMe is a much safer R0 investment.

## Security and reliability

Benefits:

- driver/device faults can be contained to a VM;
- mature driver, firmware, regulatory, and recovery logic becomes available;
- the host sees a smaller standardized front end.

Costs:

- Linux kernel, image builder, packages, firmware, and update process join the TCB/supply chain;
- the domain has direct hardware and DMA access within its mappings;
- shared-memory parsers and control protocol are new attack surfaces;
- groups/reset may prevent safe recovery;
- correlated host/VMM bugs and side channels remain;
- boot time, memory, latency, and debugging increase;
- GPL/source-offer and firmware redistribution duties must be handled.

## Failure model

The host must detect heartbeat/queue timeout, stop new requests, revoke mappings/interrupts, reset the device, discard untrusted shared state, restart the domain, renegotiate, and restore policy. If a device lacks reliable reset or shares a group with a host-critical function, it is ineligible.

Never let domain failure take down serial, GOP panic output, root NVMe, or the only wired recovery network during R0.

## Performance

Virtio rings and shared pages can keep throughput high; latency includes guest scheduling, notification, possible copy/mapping, and protocol translation. Network/Wi-Fi tolerate this better than interactive primary display or professional audio. Benchmark only after correct ownership and failure recovery; zero-copy is not worth stale-DMA bugs.

## Decision gates

Approve a prototype only if:

1. the device is much harder than its standardized exported service;
2. it occupies an isolated group and has reliable reset;
3. firmware/driver redistribution is legal;
4. boot/recovery remains possible without it;
5. the front-end protocol is versioned and fuzzed;
6. a native path remains the long-term default unless explicitly reconsidered.

## Recommended integration

Prototype first with an emulated/assigned secondary Wi-Fi or NIC and virtio-net after the VMM/IOMMU are mature. Do not place this mechanism on the R0 critical boot path.
