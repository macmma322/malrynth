# Networking: wired Ethernet first

## Evidence labels

- **OFFICIAL FACT** — standards-body/vendor documentation.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — upstream model/driver evidence; license governs reuse.
- **COMMUNITY EVIDENCE** — field inventory/procurement evidence, not a support guarantee.
- **INFERENCE** — engineering conclusion from cited evidence.
- **PROPOSED MALRYNTH DECISION** — recommended project policy.

## Decision and ranking

| Rank | Family | R0 judgment | Reason |
|---:|---|---|---|
| 1 | Intel I210/I211 (`8086:1533` / `8086:1539`) | **FEASIBLE / preferred** | vendor-published IDs and programming material; discrete PCIe GbE; permissive BSD lineage |
| 2 | Intel I350 | **FEASIBLE / preferred fallback** | same igb lineage and public datasheet; multiport/SR-IOV features can be ignored initially |
| 3 | Intel 82576 / QEMU igb | **FEASIBLE for emulation/used hardware** | QEMU explicitly emulates 82576; discontinued silicon makes it a test model, not procurement target |
| 4 | QEMU e1000 (`8086:100e`) | **FEASIBLE virtual bootstrap only** | simplest descriptor-ring stepping stone; QEMU's upstream model selects the 82540EM identity ([QEMU e1000 model](https://gitlab.com/qemu-project/qemu/-/blob/master/hw/net/e1000.c)) |
| 5 | Intel 82574L/e1000e (`8086:10d3`) and I219 | **DIFFICULT first native target** | common and implemented, but I219 PCH/PHY/ME/NVM interactions are less self-contained than I210; 82574L is older |
| 6 | Realtek RTL8111/8168/8411 | **DIFFICULT / secondary** | cheap and available; public register documentation is weaker and revisions/quirks are numerous |

**PROPOSED MALRYNTH DECISION:** qualify a genuine discrete Intel I210/I211 or I350 adapter and make wired Ethernet the only R0 network path. Do not require onboard networking to match the reference if the board has a suitable PCIe slot.

## Why I210/I350

**OFFICIAL FACT:** Intel publishes I210 and I350 programming datasheets ([Intel Ethernet datasheet index](https://www.intel.com/content/www/us/en/support/articles/000093196/ethernet-products.html)). Intel's I210/I211 FAQ assigns programmed IDs `1533` to I210-AT and `1539` to I211-AT; `1531`/`1532` are hardware defaults for unprogrammed devices and must not be treated as equivalent retail targets ([Intel I210/I211 FAQ](https://cdrdv2-public.intel.com/334026/ethernet-controller-i210-i211-faq.pdf)). **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** FreeBSD's e1000 tree separates OS glue and shared hardware logic under per-file permissive licenses; Linux supplies GPL igb/e1000e. QEMU explicitly emulates 82576 as `igb` and describes igb → e1000e → e1000 lineage ([QEMU igb](https://www.qemu.org/docs/master/system/devices/igb.html)).

This gives Malrynth three useful levels: QEMU e1000 for a minimal descriptor-ring prototype, QEMU igb for close pre-hardware testing, and a real I210/I350 adapter.

## Native R0 subset

1. PCI enable, BAR mapping, reset, NVM checksum/MAC read, and link detection.
2. One RX and one TX queue with physically allocated descriptor rings.
3. Fixed-size receive buffers and simple copy transmit before scatter/gather/offload.
4. MSI or MSI-X single vector; interrupt moderation off or conservative.
5. MAC address filters, broadcast, and one unicast address.
6. Autonegotiated 1000BASE-T link using adapter NVM/PHY defaults; report rather than aggressively reconfigure PHY.
7. Link-change, RX, TX completion, and error interrupts.
8. Reset after wedged queue; DMA stopped before buffers are freed.

Defer checksum/TSO/LRO, RSS/multiqueue, VLAN filters, PTP, Energy Efficient Ethernet tuning, SR-IOV, management/NC-SI, PXE, wake-on-LAN, jumbo frames, and runtime power management.

## Staged support

| Stage | Controller | Exit condition |
|---|---|---|
| R0-A | QEMU e1000 | reset, one RX/TX ring, MSI, ARP/ICMP, ring-wrap and timeout recovery |
| R0-B | QEMU igb | same API on 82576 model, MSI-X single vector, link-change and injected error paths |
| R0-C | genuine I210/I211 or I350 | cold/warm reset, NVM/MAC validation, 1000BASE-T, sustained bidirectional traffic |
| R1 | e1000e/82574L and selected Realtek revision | independent qualification; no family-wide claim |
| Later | multiqueue/offloads/PTP/power/SR-IOV | feature-specific correctness and performance gates |

## Driver dependencies

- PCIe/MMIO and DMA allocation/mapping
- MSI/MSI-X
- cache/ordering barriers
- Ethernet frame layer, ARP, IPv4/IPv6, UDP/TCP or a deliberately smaller early diagnostic protocol
- timers and work queues for link/watchdog recovery
- IOMMU domain and buffer ownership before user-space driver experiments

The first proof should transmit/receive raw frames and ARP/ICMP in a controlled LAN. Network logging follows only after local serial remains available; it must not become the sole crash console.

## Adapter authenticity and NVM

Marketplace I210/I350 cards are counterfeit-prone and board NVM contents matter. Before qualification record controller markings if visible, PCI VID:DID/subsystem/revision, MAC/OUI, NVM checksum status, firmware/NVM version, link partner, and photograph. Use programmed retail/industrial adapters; do not choose EEPROM-less designs. Intel's material notes that EEPROM-less operation shifts initialization defaults into the host driver.

**COMMUNITY EVIDENCE:** marketplace photos and seller claims are insufficient to distinguish genuine silicon, programmed NVM and board layout. **INFERENCE:** procurement must use an authorized distributor or known OEM pull, then bind the support claim to the observed subsystem/revision/NVM checksum rather than the faceplate label.

## Realtek strategy

Current candidate machines expose RTL8111/8168-class hardware. Keep it as a secondary interoperability target after I210. **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux's `r8169` supports 8169/8168/8101 and contains revision-specific paths under GPL-2.0-only ([Linux `r8169`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/realtek/r8169_main.c)). **INFERENCE:** the broad family name is not a sufficient programming contract; qualify exact revision/subsystem and do not claim all devices sharing a crowd-sourced `10ec:8168` label.

## Port versus write

**PROPOSED MALRYNTH DECISION:** **WRITE NATIVE** Malrynth PCI/DMA/interrupt/network integration. **PORT ALGORITHM/LOGIC** for hardware initialization, NVM/PHY handling, reset, descriptor formats and errata from the permissively licensed FreeBSD Intel e1000 shared code after a file-by-file audit. The cited `if_em.c` is BSD-2-Clause ([FreeBSD `if_em.c`](https://github.com/freebsd/freebsd-src/blob/main/sys/dev/e1000/if_em.c)); adjacent Intel shared files can carry different notices. Linux e1000/igb/e1000e and Realtek code are GPL behavioral references, not default port sources.

## Tests

- QEMU e1000 then igb: ring wrap, small/maximum frames, dropped completions, link flap
- real I210/I350: cold/warm reset, cable unplug/replug, sustained bidirectional traffic, malformed/short frames, RX exhaustion, TX timeout
- IOMMU: verify only descriptor and packet mappings are writable; provoke a blocked DMA in a sacrificial test mode
- packet capture on a second machine to distinguish driver errors from stack errors

## Recommended integration

The driver API should expose DMA constraints and reset/failure without hard-coding Linux `net_device`. Store exact adapter/NVM identity in the hardware database and keep onboard NIC support as a separate claim.

## Source ledger contributions

| Authority | Accessed | Claim supported | URL | Licensing relevance |
|---|---|---|---|---|
| Intel | 2026-08-19 | Availability of public I210/I350 programming datasheets | https://www.intel.com/content/www/us/en/support/articles/000093196/ethernet-products.html | Vendor specifications are references, not source-code licenses. |
| Intel | 2026-08-19 | I210/I211 programmed and unprogrammed device IDs | https://cdrdv2-public.intel.com/334026/ethernet-controller-i210-i211-faq.pdf | Vendor document; supports IDs but grants no code rights. |
| Intel | 2026-08-19 | `8086:10d3` is the 82574L Gigabit CT adapter | https://www.intel.com/content/www/us/en/support/articles/000005612/ethernet-products/gigabit-ethernet-adapters-up-to-2-5gbe.html | Vendor support fact, no code grant. |
| QEMU project | 2026-08-19 | 82576 igb emulation and e1000-family relationship | https://www.qemu.org/docs/master/system/devices/igb.html | QEMU is GPL-2.0-or-later; run as oracle or comply before copying. |
| QEMU project | 2026-08-19 | e1000 model's 82540EM `8086:100e` identity | https://gitlab.com/qemu-project/qemu/-/blob/master/hw/net/e1000.c | QEMU is GPL-2.0-or-later; implementation is an oracle, not permissive copy source. |
| FreeBSD project | 2026-08-19 | Maintained Intel e1000 driver and BSD-2-Clause integration file | https://github.com/freebsd/freebsd-src/blob/main/sys/dev/e1000/if_em.c | Cited file BSD-2-Clause; retain notices and audit every dependency. |
| Linux kernel project | 2026-08-19 | Realtek family/revision complexity and license | https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/realtek/r8169_main.c | `GPL-2.0-only`; behavioral reference absent GPL adoption. |
| Linux kernel project | 2026-08-19 | e1000 implementation/device-model evidence | https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/intel/e1000/e1000_main.c | `GPL-2.0`; behavioral reference absent GPL adoption. |
