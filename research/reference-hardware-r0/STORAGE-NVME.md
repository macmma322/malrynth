# Storage: NVMe-first strategy

## Evidence labels

- **OFFICIAL FACT** — standards-body or vendor material.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — upstream code/model evidence; its license still governs reuse.
- **COMMUNITY EVIDENCE** — inventory or field reports useful for leads, not a support guarantee.
- **INFERENCE** — an engineering conclusion from cited evidence.
- **PROPOSED MALRYNTH DECISION** — a recommendation for this project.

## Decision

**PROPOSED MALRYNTH DECISION:** make one PCIe/NVMe namespace the only R0 persistent-storage driver target. Put SATA/AHCI in R1 or later. Disable VMD, RST, RAID, and vendor remapping in firmware.

**OFFICIAL FACT:** NVMe 2.3 is the current modular specification set; the PCIe transport, base specification and NVM command set collectively define the host/controller contract ([NVM Express Base Specification page](https://nvmexpress.org/specification/nvm-express-base-specification/)). **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** QEMU exposes configurable controller, namespace, queue-count, MSI-X-count and MDTS behavior and identifies its modern model with allocated `1b36:0010` ([QEMU NVMe documentation](https://www.qemu.org/docs/master/system/devices/nvme.html), [QEMU allocated PCI IDs](https://www.qemu.org/docs/master/specs/pci-ids.html)). It is still a bus-mastering DMA device and must not be treated as a trivial MMIO block.

## Minimum controller path

1. Discover PCI class `01:08:02` or a qualified NVMe function; enable memory and bus mastering only after BAR validation.
2. Map BAR0/1 with device memory attributes. Read capability/version registers and reject unsupported page sizes, queue entry sizes, or transport.
3. Perform a bounded controller disable/reset sequence and wait using the advertised timeout. No infinite polling.
4. Allocate physically contiguous, page-aligned Admin Submission and Completion Queues; program AQA/ASQ/ACQ.
5. Select a memory page size supported by both kernel and controller; program CC and wait for CSTS.RDY.
6. Issue Identify Controller and Identify Namespace through the admin queue. Record model, serial, firmware revision, MDTS, namespace count, LBA formats, optional-command bits, and volatile write-cache state.
7. Create one I/O queue pair. Start with a single CPU/queue, one interrupt vector, and conservative queue depth.
8. Implement bounded PRP handling for aligned physical buffers before scatter/gather optimization. Do not assume a request fits one or two pages.
9. Support Flush, Read, Write, and necessary Dataset Management only after capabilities are checked. Completion status is not a boolean; decode SCT/SC and phase tags.
10. Add orderly shutdown notification, controller reset, queue teardown, timeout/cancel policy, and post-reset namespace re-identification.

**OFFICIAL FACT:** Identify data is capability discovery, not decoration: namespace LBA formats select the logical block data size, while MDTS constrains a command's transfer size. Submission queues and completion queues are host-memory rings, completion phase tags distinguish new entries after wrap, and PRPs describe host data pages ([NVMe 2.3 specification set](https://nvmexpress.org/specification/nvm-express-base-specification/)). **INFERENCE:** a Malrynth request must be split at the minimum of block-layer, PRP-representation and MDTS limits; hard-coding 512-byte blocks, two PRPs or one namespace is unsafe even if the first QEMU image happens to fit.

## Dependencies

- PCI BAR sizing/mapping and bus mastering
- coherent or explicitly synchronized DMA allocation
- MSI/MSI-X programming, with a temporary polling mode useful for first bring-up
- memory barriers matching x86 and device ordering requirements
- monotonic timeouts
- block layer with 64-bit LBA/count checking
- IOMMU mapping later; identity DMA is acceptable only in a controlled early milestone and must be loudly recorded

## Required R0 subset

- NVM command set over PCIe, not NVMe-oF
- one controller, one active namespace
- 512-byte and 4 KiB logical block formats; select only an already formatted supported LBA size
- Admin Identify, Get Log Page (basic health/error), Create/Delete I/O SQ/CQ, Set/Get Features needed for queues, Abort if feasible
- I/O Flush/Read/Write
- MSI or MSI-X, single vector initially
- clean shutdown and controller reset

Defer namespaces shared across controllers, multipath, SR-IOV, zoned namespaces, reservations, sanitize/format, firmware update, namespace management, APST, host-memory buffer, telemetry, and vendor commands.

Power policy is intentionally conservative. Record the Identify Controller power-state descriptors but leave Autonomous Power State Transition disabled in R0. Use the specified normal shutdown notification before removing power; after a timeout, escalate from command abort (when viable) to queue/controller reset and re-run Identify before serving I/O. **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux's PCI host driver has separate admin/I/O queues, MSI/MSI-X vectors, reset/shutdown locks, APST policy and a large explicit quirk set, showing that nominal compliance does not eliminate recovery work ([Linux `nvme-pci`](https://github.com/torvalds/linux/blob/master/drivers/nvme/host/pci.c)).

## Device shortlist

### Samsung 970 EVO Plus (owned; first device)

**OFFICIAL FACT:** Samsung specifies M.2 2280, PCIe Gen3 x4, NVMe 1.3, an in-house controller and client-PC use ([Samsung 970 EVO Plus data sheet](https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_NVMe_SSD_970_EVO_Plus_Data_Sheet_Rev.3.0_10129514071343.pdf)). **COMMUNITY EVIDENCE:** a retail family name or PCI-ID database match does not prove identical controller silicon or firmware across revisions.

**PROPOSED MALRYNTH DECISION:** use the already-owned 500 GB device for read-only and disposable-partition testing once backups exist. Do not run destructive tests against the active system disk. A separate spare of the same family is preferable but not a prerequisite for research.

### WD Blue SN570 (second client cross-check)

**OFFICIAL FACT:** Western Digital specifies a single-sided M.2 2280 PCIe Gen3 x4 NVMe design and advertises low-power client use ([WD SN570 announcement](https://www.westerndigital.com/en-ca/company/newsroom/press-releases/2021/2021-10-04-content-creators-can-now-capture-their-creativity-with-a-new-solution-from-western-digital)). **INFERENCE:** it is a useful second client implementation without making PCIe Gen5 or enterprise options part of R0.

### Micron 7450 M.2 (enterprise cross-check, not a budget buy)

**OFFICIAL FACT:** Micron documents PCIe Gen4, M.2 variants with power-loss protection, up to 128 namespaces, and both 512- and 4096-byte sectors ([Micron 7450 product page](https://www.micron.com/products/storage/ssd/data-center-ssd/7450-ssd), [Micron 7450 product brief](https://assets.micron.com/adobe/assets/urn%3Aaaid%3Aaem%3Ae71d9e5e-58c1-43cb-94fd-5b0c023e9150/original/as/7450-nvme-ssd-product-brief.pdf)). This is useful for standards/error-path validation if already available, but its enterprise price/features do not define R0.

Exact SSD firmware and capacity must be recorded. A retail family name does not prove identical controller silicon across revisions; qualification attaches to VID:DID, subsystem ID, model string, and firmware.

## Reset and recovery tests

- cold boot, warm reboot, and controller disable/enable
- invalid namespace and out-of-range LBA rejection
- queue full/backpressure
- command timeout with bounded escalation: abort, queue reset, controller reset, device marked failed
- surprise status/error injection in QEMU before real hardware
- data integrity across sizes crossing page and MDTS boundaries
- flush ordering with a test filesystem or raw journal harness
- IOMMU fault on an intentionally unmapped DMA buffer once remapping exists

Never experiment with firmware update, format, sanitize, or namespace management on an owned data-bearing drive.

## Why AHCI is later

**OFFICIAL FACT:** AHCI 1.3.1 defines a PCI HBA with 1–32 SATA ports, host-memory command structures, ATA/ATAPI, PIO/DMA and optional NCQ/64-bit addressing ([Intel AHCI 1.3.1](https://www.intel.com/content/www/us/en/io/serial-ata/serial-ata-ahci-spec-rev1-3-1.html)). **INFERENCE:** adding it to R0 creates a second storage stack, port-multiplier/ATAPI decisions and SATA error recovery without improving the chosen NVMe-first boot. **PROPOSED MALRYNTH DECISION:** AHCI is R1, limited initially to ordinary SATA disks; ATAPI, port multipliers and aggressive power management are later. USB mass storage should follow xHCI before arbitrary SATA when the goal is cheap removable test media.

## Port versus write

**PROPOSED MALRYNTH DECISION:** **WRITE NATIVE** around the NVMe specification. Use QEMU and Linux as executable/behavioral references, not copy sources: both relevant implementations are GPL-licensed ([QEMU license](https://www.qemu.org/docs/master/about/license.html), [Linux `nvme-pci` SPDX](https://github.com/torvalds/linux/blob/master/drivers/nvme/host/pci.c)). Audit individual BSD files before any permissive reuse. Do not port a large host driver: Malrynth needs a smaller initial subset and different DMA/block abstractions.

## Recommended integration

The eventual block API should express DMA limits, flush/FUA semantics, queue reset, device removal, and an IOMMU domain. NVMe conformance and device qualification belong in tests/database, not in the core roadmap from this research branch.

## Source ledger contributions

| Authority | Accessed | Claim supported | URL | Licensing relevance |
|---|---|---|---|---|
| NVM Express, Inc. | 2026-08-19 | NVMe 2.3 is current; modular base, command-set and transport specifications | https://nvmexpress.org/specification/nvm-express-base-specification/ | Specification access is not a source-code grant; review published terms. |
| QEMU project | 2026-08-19 | NVMe 1.4 model, namespaces, queue/MSI-X/MDTS controls | https://www.qemu.org/docs/master/system/devices/nvme.html | QEMU is GPL-2.0-or-later; run as oracle or comply before copying. |
| QEMU project | 2026-08-19 | Allocated QEMU NVMe ID `1b36:0010` | https://www.qemu.org/docs/master/specs/pci-ids.html | Documentation fact; implementation remains GPL. |
| Samsung | 2026-08-19 | 970 EVO Plus form factor/interface/controller/client characteristics | https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_NVMe_SSD_970_EVO_Plus_Data_Sheet_Rev.3.0_10129514071343.pdf | Proprietary vendor document; cite, do not copy protected expression. |
| Western Digital | 2026-08-19 | SN570 single-sided M.2 2280, PCIe Gen3 x4 and low-power client positioning | https://www.westerndigital.com/en-ca/company/newsroom/press-releases/2021/2021-10-04-content-creators-can-now-capture-their-creativity-with-a-new-solution-from-western-digital | Vendor publication, no code license. |
| Micron | 2026-08-19 | 7450 PCIe generation, M.2/PLP, namespace and sector-size capabilities | https://assets.micron.com/adobe/assets/urn%3Aaaid%3Aaem%3Ae71d9e5e-58c1-43cb-94fd-5b0c023e9150/original/as/7450-nvme-ssd-product-brief.pdf | Vendor document, no code license. |
| Intel | 2026-08-19 | AHCI 1.3.1 programming model and scope | https://www.intel.com/content/www/us/en/io/serial-ata/serial-ata-ahci-spec-rev1-3-1.html | AHCI specification has implementation/document terms; no general code grant. |
| Linux kernel project | 2026-08-19 | Real host complexity: queues, DMA, interrupts, resets, APST and quirks | https://github.com/torvalds/linux/blob/master/drivers/nvme/host/pci.c | `GPL-2.0`; behavioral reference unless GPL reuse is chosen. |
