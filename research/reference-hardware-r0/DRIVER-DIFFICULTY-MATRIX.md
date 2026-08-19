# Driver difficulty matrix

## Scale

Effort bands avoid false line counts:

- **tiny:** one narrow register interface, little policy;
- **small:** one device/class subset plus shared bus primitives;
- **medium:** multiple state machines, DMA/interrupt/error handling;
- **large:** broad hardware variation, firmware, power, recovery, and userspace ABI;
- **ecosystem:** multiple kernel/user services, protocols, policy, security, certification, and continuous upstream work.

The band assumes PCI, memory allocation, interrupts, locks, and basic tests exist. If they do not, the first implementation also pays for those dependencies.

| Class | Complexity / effort order | Documentation | Firmware | DMA | Interrupts | Power | Port opportunity | Vendor cooperation |
|---|---|---|---|---|---|---|---|---|
| serial 16550 | tiny; first | excellent public register model | none after firmware enables Super I/O logical device | none | optional/simple | low | write native; use BSD logic for FIFOs/quirks | low; board resource disclosure helps |
| GOP/simple framebuffer | tiny–small; first | UEFI specifies handoff/mode data | firmware initialized; no blob loaded by OS | scanout reads memory but OS does not program engine | none | none initially | write native bounds/drawing | low; firmware quality matters |
| NVMe | medium; early | excellent standards + open drivers | controller-internal, opaque but standard host ABI | high: queues/PRPs/data | MSI/MSI-X, queue model | medium later | write native subset; port error/reset logic | low for standard path; useful for errata |
| xHCI | medium–large; early | excellent register spec + USB specs | controller may have platform firmware, normally no host-loaded blob | high: contexts/rings/buffers | event rings + MSI/MSI-X | medium/high later | write native core; port ring/hub logic | low; board port routing helps |
| USB HID | small after USB; early | excellent class/usage specs | device internal only | via USB controller | interrupt transfers | low | native boot subset; port parser/quirks | low |
| Intel I210/I350 Ethernet | medium; early | excellent public datasheets | NVM/PHY data; no large runtime blob | high descriptor/packet DMA | MSI/MSI-X, moderation/link | medium later | native OS glue + permissive hardware logic | low; errata/NVM details useful |
| HDA | large; later | controller spec good; codec boards vary | codec/internal; pin policy from firmware | multiple PCM DMA streams | MSI + unsolicited codec events | medium/high | port codec graph/quirks; native PCM glue | medium for codec details |
| USB Audio Class 1 | medium–large; later | strong class specs | none normally | xHCI isochronous | periodic completion | medium | native subset; port clock/feedback logic | low |
| Wi-Fi | ecosystem; R3 | standards public; device command APIs uneven | mandatory on most current devices | high, many queues | high-rate events/RX | high/coexistence | large port or temporary domain | high for stable FW API, regulatory support |
| Bluetooth | medium transport; ecosystem profiles | Bluetooth Core/profile specs | common on USB controllers | transport-dependent | USB events | medium | native HCI + port host protocols | medium for controller firmware |
| GPU display | large–ecosystem | AMD/Intel code/docs strong; varies by generation; NVIDIA GSP-dependent | mandatory multiple blobs on modern devices | very high, GPU VM/scanout | complex/vblank/hotplug/fault | very high | focused large port, preserve OS-neutral seams | high for firmware/interface stability |
| GPU Vulkan/compute | ecosystem | Mesa/ISA evidence; kernel ABI assumed | scheduler/security/media firmware | extreme, shared VM/sync | fences/faults/resets | very high | port Mesa winsys/driver over native uAPI | high for conformance/firmware/debug |
| camera | ecosystem | UVC public, but sensors/ISP/laptops vary | frequent ISP/device firmware | sustained isochronous/bulk | frame events | high | UVC subset later; vendor for MIPI/ISP | high for integrated cameras |
| printer | medium protocol, ecosystem UX | USB printer/IPP public; page languages vary | device internal | low/USB | simple | low | standards/network-first; user-space drivers | medium for proprietary formats |
| sensors | small per bus, large as platform set | ACPI/HID/I2C specs; board details uneven | EC/device-specific | usually low | GPIO/ACPI/HID events | high for platform policy | port class logic; keep policy in services | medium/high on laptops |

## Dependency order

```text
PCI + MMIO + DMA + MSI
  ├─ NVMe
  ├─ I210 Ethernet
  └─ xHCI ─ USB enumeration ─ hubs ─ HID
                              ├─ mass storage
                              ├─ USB audio
                              └─ Bluetooth HCI

ACPI + timers + interrupts + IOMMU
  ├─ SMP / power basics
  ├─ DMA confinement
  └─ user-space or Linux driver domains

GPU VM + scheduler + reset + display
  └─ Mesa winsys/compiler/WSI ─ Vulkan/compositor
```

## Risk-adjusted first implementation order

1. polled serial and GOP ownership;
2. ACPI fixed-table inventory, PCI/MCFG, MSI, DMA allocator;
3. NVMe single queue/namespace;
4. xHCI direct port and boot HID;
5. I210-class Ethernet;
6. IOMMU translation/interrupt remapping for the above;
7. USB mass storage and UAC1;
8. HDA;
9. focused GPU display then acceleration;
10. Wi-Fi/Bluetooth and laptop devices.

## What the matrix does not claim

It does not predict calendar time, staff size, or source lines. A narrow driver can become large when hardware recovery, suspend, security, multiple revisions, hotplug, and production diagnostics are included. `FEASIBLE` means the interfaces/evidence make an engineering path credible, not that support exists.

## Recommended integration

Use the ordering as input to later roadmap discussion only. It is not a modification of the existing M0–M7 roadmap.
