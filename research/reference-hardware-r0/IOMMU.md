# IOMMU research for reference hardware R0

**Status:** RESEARCH — proposed policy and qualification sequence; no platform is certified.
**Research date:** 2026-08-19
**Scope:** Intel VT-d on Coffee Lake-S/Q370 and AMD IOMMU on Ryzen 5000G/B550.

## Evidence labels

- **OFFICIAL FACT** — stated by a specification owner or hardware vendor.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — a working pattern in an official open-source
  project; evidence, not permission to copy code.
- **COMMUNITY EVIDENCE** — practitioner observation without specification authority; useful
  only to motivate a test.
- **INFERENCE** — a conclusion that requires measurement on the exact specimen.
- **PROPOSED MALRYNTH DECISION** — policy proposed for later review, not implemented fact.

## Security boundary

**OFFICIAL FACT:** CPU virtualization and I/O virtualization are different facilities.
Intel VMX/VT-x and AMD SVM control guest CPU execution; Intel VT-d and AMD IOMMU translate
and constrain device-originated DMA and can remap interrupts. Intel's
[VT-d Architecture Specification](https://www.intel.com/content/www/us/en/content-details/868911/intel-virtualization-technology-for-directed-i-o-architecture-specification.html)
and AMD's
[I/O Virtualization Technology Specification](https://www.amd.com/content/dam/amd/en/documents/processor-tech-docs/specifications/48882_IOMMU.pdf)
define different discovery structures and programming interfaces for the same broad class of
protection.

**INFERENCE:** A CPU or chipset page saying VT-d, AMD-V or “virtualization” does not prove
that board firmware enables an IOMMU, describes every requester correctly, supplies
interrupt remapping, or yields one-function isolation groups. Only table inspection and
adversarial tests on the exact board/firmware build establish the usable boundary.

**PROPOSED MALRYNTH DECISION:** A working IOMMU is mandatory before a DMA-capable device is
granted to an unprivileged user-space driver. The kernel must make the device's DMA authority
match the memory capabilities granted to its driver.

## Reference-platform order

**OFFICIAL FACT:** Intel lists both
[Core i5-9500](https://www.intel.com/content/www/us/en/products/sku/134895/intel-core-i59500-processor-9m-cache-up-to-4-40-ghz/specifications.html)
and [Q370](https://www.intel.com/content/www/us/en/products/sku/133282/intel-q370-chipset/specifications.html)
as VT-d capable. ASUS documents the exact PRIME Q370M-C/CSM board, but its product facts do
not certify DMAR correctness or isolation topology. [ASUS board manual](https://dlcdnets.asus.com/pub/ASUS/mb/LGA1151/PRIME_Q370M-C/E14162_PRIME_Q370M-C_UM_WEB.pdf)

**PROPOSED MALRYNTH DECISION:** Implement and qualify VT-d first on i5-9500/Q370 because
both CPU and chipset explicitly advertise the facility and the board has strong serial/debug
observability. “First” is implementation order, not an Intel-shaped generic interface.

**OFFICIAL FACT:** AMD's IOMMU specification defines IVRS discovery and AMD remapping; AMD's
[AM4 chipset matrix](https://www.amd.com/en/products/processors/chipsets/am4.html) establishes
Ryzen 5000/B550 compatibility. The
[ASUS Pro B550M-C/CSM specifications](https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/)
establish board I/O, not IVRS quality or isolation grouping.

**PROPOSED MALRYNTH DECISION:** Keep the domain, mapping, fault and ownership interfaces
vendor-neutral, then run the same test contract on Ryzen 5 5600G/B550. AMD support is a
cross-vendor security validation, not merely a second boot target.

## Firmware discovery

### Intel DMAR

**OFFICIAL FACT:** Intel firmware describes remapping hardware and requester scope in the
ACPI DMAR table. Structures identify remapping units, device scopes, reserved-memory regions
and optional capabilities; registers on each unit provide the architectural capability set.

**PROPOSED MALRYNTH DECISION:** Accept DMAR only after ACPI checksum/length validation,
substructure minimum-length checks, alignment and arithmetic-overflow checks, and validation
against PCI segment/bus/device/function inventory. An uncovered or ambiguously covered
requester is not assignable to an untrusted driver.

### AMD IVRS

**OFFICIAL FACT:** AMD firmware uses IVRS structures to describe IOMMU units, device ranges,
aliases and reserved memory. The unit's capability/control registers determine which
optional translation and interrupt features are usable.

**PROPOSED MALRYNTH DECISION:** Apply the same defensive parsing rules to IVRS. Expand
ranges and aliases into an explicit requester-to-unit map; reject duplicate, contradictory,
overflowing or out-of-range entries instead of guessing.

### Common topology

**OFFICIAL FACT:** PCI requester identity is segment/bus/device/function based. ACPI and PCI
firmware data describe host bridges, bus ranges, resources and ownership. The
[PCI Firmware Specification overview](https://pcisig.com/specification-overview/pci-firmware)
identifies the current specification and published ECNs.

**PROPOSED MALRYNTH DECISION:** IOMMU initialization consumes validated ACPI and PCI
inventory. It must not scan arbitrary physical memory for plausible table signatures, assume
segment zero, or infer isolation from a slot's physical shape.

## Neutral kernel contract

**OFFICIAL FACT:** Both vendor architectures use OS-managed translation structures and
define permissions, translation caches, invalidations, faults and optional interrupt
remapping. Their formats and command interfaces are vendor-specific.

**PROPOSED MALRYNTH DECISION:** Separate Intel and AMD backends implement one internal
contract:

- enumerate units, capabilities and requester coverage;
- create and destroy an I/O address space;
- atomically attach/detach a validated isolation group;
- map/unmap pinned pages with explicit device-read and device-write permission;
- synchronously invalidate stale translations;
- install/remove interrupt-remapping entries;
- attribute, bound, rate-limit and audit faults;
- query page sizes, address width, coherency and optional capabilities without exposing
  vendor register layouts to drivers.

**PROPOSED MALRYNTH DECISION:** A user driver requests mapping of memory it already owns; it
never supplies arbitrary physical addresses. Mappings are page-aligned, overflow-checked,
reference-counted and revoked before pages return to the allocator. The default domain is
blocked, not identity mapped.

## Isolation groups and reserved regions

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux
[VFIO documentation](https://docs.kernel.org/driver-api/vfio.html) explains why isolation can
be coarser than one function: multifunction devices, aliases, bridges without suitable PCIe
Access Control Services and peer-to-peer paths can prevent independent remapping.

**PROPOSED MALRYNTH DECISION:** The assignable unit is an empirically validated isolation
group. All functions/bridges in a group share one owner/security domain. A future
finer-grained exception requires proof of requester-ID and peer-to-peer containment on the
exact topology.

**OFFICIAL FACT:** Intel DMAR and AMD IVRS can describe device-accessible reserved memory.
Such mappings weaken the simple promise that a driver can DMA only to its own buffers.

**PROPOSED MALRYNTH DECISION:** Every reserved mapping is visible in diagnostics and policy.
A group requiring firmware-owned identity mappings is kernel/firmware owned, explicitly
classified as reduced isolation with the minimum mapping, or rejected. Never discard a
reserved region merely to make a test pass.

## Safe enablement order

**INFERENCE:** `ExitBootServices()` does not establish that every bus-mastering device has
stopped DMA. Enabling translation beneath an active device can fault or corrupt state; leaving
translation off gives that device ambient memory authority.

**PROPOSED MALRYNTH DECISION:** Use this sequence:

1. loader captures the final memory map, RSDP and boot-device context without granting DMA;
2. kernel validates ACPI, DMAR/IVRS and minimal PCI topology;
3. record Bus Master Enable state and quiesce only devices with a documented safe path;
4. allocate remapping structures in private pinned pages and establish fault handlers;
5. install a blocked/default domain for every covered requester, retaining only approved
   firmware mappings;
6. perform architectural invalidations and enable DMA translation;
7. enable interrupt remapping when present and validated;
8. enable a device's bus mastering only after its domain and mappings are complete.

Unknown active DMA is a hard diagnostic condition. The first implementation may restrict
hardware to a proven-quiescent device set rather than claim a universal transition.

## Interrupt remapping

**OFFICIAL FACT:** DMA and interrupt remapping are separately enumerated. Interrupt
remapping constrains device-generated interrupts/destinations and participates in complete
x2APIC destination support.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** QEMU's
[system-emulator options](https://www.qemu.org/docs/master/system/qemu-manpage.html) expose
separate DMA-remapping, interrupt-remapping and x2APIC-related controls for its Intel and AMD
IOMMU models.

**PROPOSED MALRYNTH DECISION:** A DMA-remapped but interrupt-unremapped group is not fully
confined for an untrusted driver. Until interrupt remapping works, expose only
kernel-mediated interrupts; drivers cannot program arbitrary MSI/MSI-X messages.

## Invalidations, teardown and faults

**OFFICIAL FACT:** Editing translation-table memory does not itself make an IOMMU discard
cached translations. Both specifications define required invalidations and completion rules.

**PROPOSED MALRYNTH DECISION:** Mapping APIs report success only after required
invalidations complete. Teardown order is: revoke driver capability; stop submissions; mask
interrupts; quiesce and clear bus mastering; block/detach mappings; invalidate and wait;
release pinned memory; reset before a new owner when reliable reset exists. A timeout leaves
the whole group quarantined.

Every fault record includes timestamp, backend/unit, requester ID, access type, IOVA, reason,
owner and domain generation. Logs are bounded so a hostile device cannot exhaust memory or
serial bandwidth.

**PROPOSED MALRYNTH DECISION:** A user-driver fault revokes the group and triggers a
documented reset if possible; repeated/unattributable faults quarantine the group. A unit
internal error or invalidation timeout disables DMA-capable user drivers system-wide.
“Log and continue” is not containment.

## Behavior without an IOMMU

**PROPOSED MALRYNTH DECISION:** Malrynth may boot diagnostically without a usable IOMMU,
but the state is explicit: no DMA-capable device is assigned to an unprivileged driver; bus
mastering remains off except for reviewed kernel/firmware devices; certification fails; and
the system reports “DMA isolation unavailable.” A bounce buffer is not a substitute when a
device can address arbitrary memory.

## Test matrix

| Profile | Required result |
|---|---|
| q35, no IOMMU | Explicit degraded boot; user DMA assignment refused. |
| q35 + Intel IOMMU, DMA only | Mappings/faults work; untrusted MSI remains refused. |
| q35 + Intel IOMMU + interrupt remapping | VT-d backend, MSI/x2APIC path and fault attribution work. |
| q35 + AMD IOMMU + interrupt remapping | IVRS/backend reaches the same contract. |
| Malformed DMAR/IVRS corpus | Parser rejects safely before remapping-unit MMIO. |
| Out-of-range DMA | Fault is attributed and guard/target pages remain unchanged. |
| Unmap race under load | No DMA succeeds after revoke reports completion. |
| Multifunction/group case | Ownership and teardown are atomic for the whole group. |
| Driver crash/reset under DMA | Group recovers safely or remains quarantined. |

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** QEMU and Linux provide useful conformance
surfaces, but both are GPL-2.0-family projects. Tests may execute them; Malrynth must not copy
device-model or kernel implementation code.

## Physical qualification and deferrals

**PROPOSED MALRYNTH DECISION:** For each frozen Q370 and B550 firmware: capture setup pages;
hash RSDP/XSDT and DMAR/IVRS; inventory PCI topology, aliases, ACS and requester coverage under
an established OS; then independently test blocked-domain faults, DMA read/write containment,
MSI destination constraints, cold/warm boots and device resets under Malrynth. Established-OS
group output is evidence, not Malrynth truth.

**INFERENCE:** Firmware updates can change scopes, reserved regions, APIC mode and setup
defaults without changing a board marketing name. Firmware build is part of the reference-
hardware identity.

**PROPOSED MALRYNTH DECISION:** Defer PASID, ATS, PRI, Shared Virtual Addressing, nested
translation, scalable-mode extensions, posted interrupts, peer-to-peer DMA, SR-IOV and live
device migration. Basic group-level DMA and interrupt confinement must be proven first.

## Licensing relevance

Intel/AMD/PCI/ACPI specifications are authoritative research inputs, not source-code
licenses; do not reproduce protected tables wholesale. Linux and QEMU are GPL-2.0-family
implementation evidence; no code is copied here. Running those projects as test tools is
distinct from incorporating their code.

## Source ledger contributions

| Authority | Accessed | Claim contributed | URL | Licensing relevance |
|---|---|---|---|---|
| Intel | 2026-08-19 | VT-d DMAR discovery, translation, interrupt remapping, invalidation and faults | https://www.intel.com/content/www/us/en/content-details/868911/intel-virtualization-technology-for-directed-i-o-architecture-specification.html | Proprietary specification; no code/table copied |
| AMD | 2026-08-19 | AMD IOMMU IVRS discovery, translation, interrupt remapping, invalidation and faults | https://www.amd.com/content/dam/amd/en/documents/processor-tech-docs/specifications/48882_IOMMU.pdf | AMD specification terms; no code/table copied |
| Intel | 2026-08-19 | Q370 and i5-9500 advertise VT-d | https://www.intel.com/content/www/us/en/products/sku/133282/intel-q370-chipset/specifications.html | Product facts only |
| AMD | 2026-08-19 | Ryzen 5000/B550 compatibility baseline | https://www.amd.com/en/products/processors/chipsets/am4.html | Product facts only |
| UEFI Forum | 2026-08-19 | ACPI validation and platform-description context | https://uefi.org/specs/ACPI/6.6/ | Specification terms; no code copied |
| PCI-SIG | 2026-08-19 | PCI requester/configuration and firmware-ownership context | https://pcisig.com/specification-overview/pci-firmware | Specification/member terms; no text copied |
| Linux kernel project | 2026-08-19 | VFIO isolation-group and protected userspace-device model evidence | https://docs.kernel.org/driver-api/vfio.html | GPL-2.0-family ecosystem; behavior only |
| QEMU project | 2026-08-19 | Intel/AMD IOMMU and interrupt-remapping test surfaces | https://www.qemu.org/docs/master/system/qemu-manpage.html | GPL-2.0 project; test-tool use only |
| ASUS | 2026-08-19 | Exact Q370/B550 board context | https://dlcdnets.asus.com/pub/ASUS/mb/LGA1151/PRIME_Q370M-C/E14162_PRIME_Q370M-C_UM_WEB.pdf | Manual facts only |
