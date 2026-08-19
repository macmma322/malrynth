# Driver porting strategy

## Decision framework

Choose the smallest legal and maintainable unit that preserves hardware knowledge without importing an accidental host architecture.

- **WRITE NATIVE:** specification is sufficient and the driver is bounded.
- **PORT ALGORITHM/LOGIC:** reuse isolated state machines, tables, math, or hardware sequences behind Malrynth-native bus/DMA/interrupt APIs.
- **PORT LARGE DRIVER:** preserve a complex maintained driver and supply a deliberate compatibility layer; ongoing upstream tracking is accepted.
- **USE DRIVER DOMAIN TEMPORARILY:** run a foreign kernel/driver in an isolated VM and export a virtio-like device.
- **REQUIRES VENDOR:** public code/firmware/interface is insufficient for a supportable implementation.

## R0 and future candidates

| Class/candidate | Choice | Upstream references | License notes | Replaced Linux assumptions |
|---|---|---|---|---|
| 16550 UART | WRITE NATIVE | TI TL16C550D; FreeBSD uart; QEMU serial | specs terms; FreeBSD BSD | tty framework, platform enumeration, console glue |
| GOP framebuffer | WRITE NATIVE | UEFI 2.11; EDK2/QEMU behavior | UEFI implementation terms; inspect any code license | Linux simpledrm/fbdev, memory/cache helpers |
| ACPI fixed tables | WRITE NATIVE | ACPI 6.6; ACPICA as possible AML component | ACPICA dual BSD/GPL historically; verify current package | Linux ACPI device model, sysfs, locks, OS services |
| NVMe | WRITE NATIVE + PORT ALGORITHM/LOGIC | NVM Express specs; QEMU NVMe; FreeBSD nvme; Linux nvme | FreeBSD BSD; Linux GPL-2; NVMe spec terms | blk-mq, scatterlists, DMA API, PCI/MSI, work queues |
| xHCI/USB core | WRITE NATIVE + PORT ALGORITHM/LOGIC | Intel xHCI; USB-IF; FreeBSD USB; Linux xhci | FreeBSD BSD-family; Linux GPL; spec agreements | USB core/HCD, DMA pools, URBs, timers, PM |
| USB HID | WRITE NATIVE + PORT ALGORITHM/LOGIC | USB HID 1.11/Usage Tables; BSD/Linux parsers | per-source audit | Linux input/HID buses, quirks, work queues |
| Intel I210/I350 | WRITE NATIVE OS layer + PORT ALGORITHM/LOGIC | Intel datasheets; FreeBSD `sys/dev/e1000`; Linux igb; QEMU igb | FreeBSD Intel shared code permissive; Linux GPL | iflib/netdev, DMA tags, NAPI, PCI, PHY framework |
| RTL8111 | PORT ALGORITHM/LOGIC later | FreeBSD/Linux/Haiku drivers | per-source audit; Linux GPL | many revision/PHY quirks and OS network glue |
| UAC1 | WRITE NATIVE + PORT ALGORITHM/LOGIC | USB Audio specs; FreeBSD uaudio; Linux snd-usb | BSD versus GPL | ALSA/PCM, URBs, isochronous scheduler |
| HDA | WRITE NATIVE + PORT ALGORITHM/LOGIC | Intel HDA spec; FreeBSD/Haiku; Linux codec corpus | prefer permissive core; quirks provenance matters | ALSA, PCI/DMA, codec model, power/ACPI |
| AMD GPU | PORT LARGE DRIVER, focused generation | Linux AMDGPU/DC; Mesa RADV; AMD GPUOpen | many kernel files MIT; Mesa MIT; firmware separate | DRM/KMS, TTM/GEM, dma-fence/buf, scheduler, ACPI/I2C/PM |
| Intel GPU | PORT LARGE DRIVER, focused generation | i915/Xe; Mesa ANV; Intel PRMs | mostly MIT components; firmware/binaries separate | DRM/KMS, GEM, GuC/HuC/DMC, VBT, power framework |
| NVIDIA GPU | REQUIRES VENDOR or research large port | NVIDIA open kernel modules; Nouveau/Nova; NVK | kernel dual MIT/GPL; GSP proprietary firmware; user mode differs | Linux kernel-interface layer, DRM, GSP ABI, proprietary user mode |
| Intel Wi-Fi | PORT LARGE DRIVER or temporary domain | iwlwifi, mac80211/cfg80211, firmware, hostap | GPL driver/stack; separate firmware license; supplicant license | wireless core, regulatory DB, crypto/key management, netlink/policy |
| Bluetooth | WRITE NATIVE transport + PORT ALGORITHM/LOGIC stack | Bluetooth Core; FreeBSD/BlueZ/other stack | protocol implementations vary BSD/GPL/LGPL | USB/UART transport, sockets, security/pairing, audio |

## Porting rules

1. Record upstream repository, exact revision, file list, original license/SPDX, local changes, and notices before importing code.
2. Never copy code while doing research. Produce interface maps and tests first.
3. Keep Malrynth-native OS glue in separate files from portable hardware logic.
4. Define an upstream-update procedure before approving a large port.
5. Treat firmware as a separate deliverable: provenance, hash, redistribution, version compatibility, update/recovery, and source availability.
6. Do not expose a Linux uAPI merely because Mesa expects it. Choose intentional native ABI, shim, or Linux-compatibility ABI and document ownership.
7. Prefer behavior tests and generated register descriptions over copied macro forests where licensing or drift is risky.
8. Fuzz all device-controlled parsers and exercise reset/fault paths before enabling untrusted hardware.

## Linux dependency replacement map

| Linux facility | Malrynth capability needed |
|---|---|
| PCI core, managed resources | PCI enumeration, BAR/resource ownership, hot/remove lifecycle |
| DMA API/scatterlist | typed DMA allocator, masks, sync, IOMMU map/unmap, SG representation |
| MSI/MSI-X/IRQ domains | vector allocation, message composition, affinity, interrupt remapping |
| workqueues/timers/kthreads | bounded jobs, sleep/wake, cancellation, monotonic timers |
| mutex/spinlock/RCU/refcount | audited synchronization and object lifetime |
| firmware loader | verified firmware store, license/provenance, device-version matching |
| DRM GEM/TTM/dma-buf/fence | GPU memory, sharing, synchronization, eviction, process accounting |
| KMS atomic helpers | display objects/state validation/commit/rollback/hotplug |
| netdev/NAPI/skbuff/PHY | packet buffers, receive scheduling, link/PHY state, offload contract |
| USB HCD/URB/class core | controllers, transfers, devices, hubs, class matching, cancellation |
| block-mq/bio | block requests, flush/FUA, queueing, timeout/reset, partition/filesystem boundary |
| cfg80211/mac80211/nl80211 | wireless MAC, regulatory, configuration API, userspace supplicant boundary |

## Kill signal for large ports

A large port is unacceptable if its compatibility layer becomes an unversioned imitation of Linux internals, if upstream updates routinely require semantic patches across the whole kernel API, or if firmware redistribution/support cannot be guaranteed. [PIVOT-CRITERIA.md](PIVOT-CRITERIA.md) makes those gates explicit.

## Recommended integration

Later DDK/driver architecture should adopt provenance manifests and a compatibility-layer ownership policy. This research does not modify those project areas.
