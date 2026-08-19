# Firmware and ACPI contract for MALRYNTH R0

**Status:** desktop-first firmware research, 2026-08-19.
**Primary physical oracle:** MSI MS-98N9 Q470E; ASUS Q470EI-IM-A is a compact alternative.
**Compatibility target:** revision-tolerant parsing for the portions of ACPI 6.6 Malrynth uses.

## Evidence labels

- **OFFICIAL FACT** — vendor or specification-owner statement.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — working upstream behavior; not a Malrynth
  requirement and not permission to copy code.
- **COMMUNITY EVIDENCE** — practitioner evidence without normative authority.
- **INFERENCE** — conclusion requiring exact-firmware validation.
- **PROPOSED MALRYNTH DECISION** — design proposal, not an accepted or implemented fact.

## Decision summary

**PROPOSED MALRYNTH DECISION:** Boot R0 only through 64-bit UEFI. The loader captures a
self-contained handoff—final memory map, framebuffer, ACPI RSDP, SMBIOS pointer, image/module
data, command line, entropy status and optional TCG event-log metadata—then calls
`ExitBootServices()`. The kernel never calls UEFI Boot Services afterward.

**PROPOSED MALRYNTH DECISION:** Treat ACPI as the authoritative desktop motherboard-
description and power-control interface, but treat every table and AML program as untrusted
input. Parse static tables in a small Malrynth-owned layer; use a reviewed AML implementation
for namespace, operation regions, events and sleep rather than growing a partial interpreter.

**PROPOSED MALRYNTH DECISION:** Evaluate **uACPI** as the preferred AML candidate and use
ACPICA tools as a host-side compatibility oracle. uACPI advertises table, AML, operation-
region, event, sleep, PCI-routing and resource APIs under MIT. [uACPI repository](https://github.com/uACPI/uACPI)
ACPICA is a mature OS-independent implementation; its repository describes three licensing
alternatives and file exceptions that require exact-release review. [ACPICA repository](https://github.com/open-acpica/acpica),
[ACPICA license](https://github.com/open-acpica/acpica/blob/master/LICENSE),
[Intel evaluated releases](https://www.intel.com/content/www/us/en/developer/topic-technology/open/acpica/download.html)

This is source selection research, not approval to import code without pinning, license
review, host-boundary design, fuzzing and regression results.

## Normative model and version policy

**OFFICIAL FACT:** ACPI is an OS-directed configuration and power-management interface. It
combines static description tables with definition blocks containing AML bytecode and an
event/namespace model. [ACPI 6.6 introduction](https://uefi.org/specs/ACPI/6.6/01_Introduction.html)

**OFFICIAL FACT:** UEFI publishes the RSDP through the EFI System Table configuration-table
entries; the loader must retrieve it before leaving Boot Services. UEFI 2.11 defines the
memory-map ownership transition, boot/runtime services and serial/debug protocols.
[ACPI software model](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html),
[UEFI 2.11](https://uefi.org/specs/UEFI/2.11/)

**PROPOSED MALRYNTH DECISION:** ASUS's “ACPI 6.1” claim is not a reason for a 6.1-only
parser. Consume each table by signature, declared revision and length. Accept valid older
layouts, ignore unknown trailing fields, and never read a newer field unless `Length` covers
it. ACPI 6.6 is the research reference, not a requirement that firmware emit 6.6 tables.

## UEFI loader-to-kernel handoff

The handoff is copied into loader-owned pages and contains:

- ABI magic/version/size, image build ID and integrity status;
- physical memory-map descriptors plus descriptor size/version and map key diagnostics;
- RSDP and SMBIOS addresses obtained from known configuration-table GUIDs;
- GOP framebuffer base/size, pixel layout, stride and mode;
- loaded modules with physical ranges, lengths, type and hashes;
- UEFI runtime-service pointer only if a later runtime mapping policy explicitly enables it;
- serial protocol/device-path facts when available, never an opaque live Boot Services
  object;
- optional TCG2 event-log address/length and truncation/final-events metadata.

**OFFICIAL FACT:** UEFI requires a current memory map/key for `ExitBootServices()`; an
intervening allocation can invalidate the key. [UEFI boot services](https://uefi.org/specs/UEFI/2.11/07_Services_Boot_Services.html)

**PROPOSED MALRYNTH DECISION:** The loader performs bounded map/key retry: obtain map with
headroom, allocate nothing afterward, call exit, and retry only the specified stale-key case.
It validates all physical ranges for overflow/overlap before handoff. The kernel copies no
firmware pointer blindly and maps runtime regions only under a separately reviewed policy.

## Defensive static-table layer

For every RSDP/XSDT table or child:

1. validate signature, revision-dependent minimum size and checksum;
2. check declared length before mapping or iterating;
3. reject physical-address addition overflow and ranges outside accepted firmware memory;
4. map only the declared range with appropriate cache attributes;
5. reject zero-length/undersized substructures so loops always advance;
6. preserve unknown tables/substructures for diagnostics without interpreting them;
7. copy facts needed after remapping rather than retain unsafe transient pointers.

**PROPOSED MALRYNTH DECISION:** Parser results are typed values with provenance
(table/signature/offset/revision), not packed firmware structs passed around the kernel.
Fuzz the parser in userspace with integer/bounds sanitizers and captured table corpora.

## Desktop-first table priority

| Priority | Tables/data | R0 use and failure policy |
|---|---|---|
| Required for full platform | RSDP, XSDT, FADT/FACS, MADT, DSDT/SSDT | Root, reset/power registers, APIC topology and AML namespace; invalid root/MADT stops full bring-up. |
| Required for reference PCI/IOMMU claim | MCFG plus DMAR or IVRS | ECAM segments and requester/remapping topology; invalid data disables the dependent capability. |
| Strongly preferred | HPET, TPM2, SPCR, DBG2 | Timer candidate, TPM interface, firmware-selected serial/debug port; absence is supported. |
| Inventory only initially | SRAT/SLIT, HEST/BERT/EINJ, WDAT, NFIT, LPIT and unknown tables | Hash/log/preserve; do not claim NUMA/RAS/watchdog/NVDIMM/low-power-idle support. |

Specific parsing rules:

- **MADT:** APIC IDs need not be dense; honor interrupt-source overrides, polarity and
  trigger; reject malformed entries independently where safe.
- **MCFG:** validate segment/bus ranges and physical-size arithmetic before ECAM mapping;
  overlapping contradictory windows disable ECAM for the affected range.
- **FADT/FACS:** validate GAS address space/width/offset; distinguish legacy blocks from
  extended fields and hardware-reduced ACPI.
- **DMAR/IVRS:** parsing feeds IOMMU qualification, never a boolean “IOMMU present.”
- **TPM2/SPCR/DBG2:** select interface/transport from the table/profile rather than board
  marketing or assumed COM1.

## AML execution boundary

**OFFICIAL FACT:** AML can access system I/O, memory, PCI configuration and other operation
regions, synchronize/notify, acquire the firmware global lock and execute control flow. It is
executable platform policy, not inert configuration. [ACPI namespace and AML](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html)

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** uACPI exposes an explicit kernel host API and
optional table-only mode. ACPICA provides an OS-services abstraction and tooling. Their
surface area demonstrates that a complete interpreter requires memory mapping, allocation,
locking, scheduling, I/O, PCI and event contracts; neither can safely be dropped into an
early kernel as a blob. [uACPI integration](https://github.com/uACPI/uACPI),
[ACPICA project](https://github.com/open-acpica/acpica)

**PROPOSED MALRYNTH DECISION:** Do not write a “just enough for `_S5`” evaluator. The
selected engine's host boundary exposes only validated physical mapping, port I/O, PCI
configuration, monotonic time/sleep, allocation, mutex/event primitives, work scheduling,
logging and fatal diagnostics. Deny embedded-controller, GPIO, Generic Serial Bus and other
operation regions until a driver and authorization policy exist.

Guardrails include global instruction/time budgets per evaluation, bounded recursion/stack
and object growth, no AML in hard-interrupt or panic context, serialization where firmware
declares it, and audit records for operation-region writes. A timeout/error returns a typed
failure and cannot continue with partially computed values.

## Initialization and event order

1. **Static early:** validate RSDP/XSDT and parse FADT, MADT, MCFG, HPET, DMAR/IVRS, TPM2 and
   SPCR/DBG2; do no AML.
2. **Interpreter bootstrap:** provide allocation, maps, locks and operation-region policy;
   load DSDT/SSDT namespace without enabling SCI/GPEs.
3. **Query phase:** evaluate the minimum discovery methods such as `_STA`, `_CRS` and PCI
   routing only after dependencies exist.
4. **Event phase:** install SCI route, fixed-event and GPE state; clear stale status before
   enabling narrowly selected sources.
5. **Power phase:** enable button/reset/S5 paths; later power states require their own tests.

**OFFICIAL FACT:** ACPI defines an SCI event model containing fixed and general-purpose
events which can dispatch control methods. [ACPI event model](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html)

**PROPOSED MALRYNTH DECISION:** The SCI top half only snapshots/acknowledges bounded status
needed to quiesce the interrupt and queues AML/event work. Repeated unhandled events are
masked and logged. AML never executes in interrupt context.

## Serial discovery strategy

**OFFICIAL FACT:** UEFI defines Serial I/O and Debugport protocols; ACPI defines SPCR/DBG2
descriptions. The selected MSI Q470E board documents rear/header serial options and a
16550A-compatible UART; the ASUS Q470E alternative exposes COM headers but still needs exact
UART qualification.
[UEFI 2.11](https://uefi.org/specs/UEFI/2.11/),
[MSI Q470E downloads/manual index](https://ipc.msi.com/product_download/Industrial-Motherboard/ATX/MS-98N9),
[ASUS Q470E manual](https://dlcdnets.asus.com/pub/ASUS/mb/Embedded_IPC/Q470EI-IM-A/E21947_Q470EI-IM-A_UM_v5_WEB.pdf?model=Q470EI-IM-A)

**PROPOSED MALRYNTH DECISION:** Use three phases:

1. loader logging through UEFI console/Serial I/O when present;
2. a qualification-profile direct polled 16550 path for the recorded physical board and
   QEMU, requiring explicit base/clock/electrical adapter data;
3. replace that assumption after table/PCI discovery with the SPCR/DBG2 or enumerated UART,
   while retaining a bounded polled panic path.

Never infer RS-232 voltage, I/O base, IRQ or clock merely from a “COM header” label.

## Exact-board capture and acceptance

**OFFICIAL FACT:** MSI documents MS-98N9 Q470E with AMI UEFI, 16550A serial, debug headers,
I210-AT plus I219LM, TPM and M.2. ASUS documents Q470EI-IM-A with Q470E, five COM ports,
LPC debug, TPM, M.2 and I210-AT plus I219LM. ASUS declares AMI UEFI, COM/LPC debug and
onboard TPM2 for Pro B550M-C/CSM.
[MSI Q470E downloads/manual index](https://ipc.msi.com/product_download/Industrial-Motherboard/ATX/MS-98N9),
[ASUS Q470E manual](https://dlcdnets.asus.com/pub/ASUS/mb/Embedded_IPC/Q470EI-IM-A/E21947_Q470EI-IM-A_UM_v5_WEB.pdf?model=Q470EI-IM-A),
[B550 specifications](https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/)

For each board revision and firmware build archive firmware image URL/hash and release notes;
all tables both raw and normalized; setup screenshots/defaults/changes; UEFI memory map and
configuration-table GUIDs; SMBIOS and PCI inventory; cold/warm/S5 serial captures; and
firmware recovery procedure. Any firmware update is a new platform revision.

| Area | Pass condition |
|---|---|
| Parser | Captured Q470E/B550 plus malformed corpus runs with ASan/UBSan/fuzzing and no OOB, leak or hang. |
| Determinism | Frozen firmware yields identical normalized tables across cold boots except classified volatile fields. |
| AML | Namespace loads; bounded `_STA`/`_CRS` results agree with an independent host-side implementation. |
| PCI routing | ACPI route data and exercised interrupt configuration agree. |
| Events | One power-button press produces one event; unknown GPE storms are containable. |
| Shutdown/reset | 25 S5 and 25 reset cycles finish with serial end markers and correct cold/warm classification. |
| Negative | Bad checksum, overflow, unknown GAS, AML timeout and SCI storm each reach the designed degraded mode. |

**COMMUNITY EVIDENCE:** OSDev's shutdown notes document that extracting only `_S5` and
hard-coding legacy PM registers is incomplete on real machines. It is a useful warning, not a
normative implementation source. [OSDev Shutdown](https://wiki.osdev.org/Shutdown)

Failure policy: invalid RSDP/XSDT/MADT stops before SMP/device initialization with direct
serial output; an invalid optional table quarantines that feature; namespace failure permits
only static-table diagnostics; SCI storms are masked; and bounded `ExitBootServices()`
failure returns to firmware or halts rather than entering with ambiguous ownership.

## Source ledger contributions

| Authority | Accessed | Claim contributed | URL | Licensing relevance |
|---|---|---|---|---|
| UEFI Forum | 2026-08-19 | Current ACPI model, tables, AML, events and power interfaces | https://uefi.org/specs/ACPI/6.6/ | Specification terms; no code copied |
| UEFI Forum | 2026-08-19 | UEFI boot/runtime transition, configuration tables and serial/debug protocols | https://uefi.org/specs/UEFI/2.11/ | Specification terms; no code copied |
| MSI / ASUS | 2026-08-19 | Q470E UEFI, COM/debug, TPM, storage and Intel NIC facts; reviewed MSI English manual dated 2023-01-31 | https://ipc.msi.com/product_download/Industrial-Motherboard/ATX/MS-98N9 | Manual facts only |
| ASUS | 2026-08-19 | B550 fallback UEFI, COM/LPC debug and TPM facts | https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/ | Product facts only |
| uACPI project | 2026-08-19 | Portable AML/table/event/sleep/resource implementation and host API | https://github.com/uACPI/uACPI | MIT; candidate dependency, pin/review required |
| ACPICA project / Intel | 2026-08-19 | Mature OS-independent implementation and evaluated releases | https://github.com/open-acpica/acpica | Intel/simplified-BSD/GPLv2 alternatives plus exceptions; exact-file legal review required |
| EDK II project | 2026-08-19 | Open UEFI/ACPI integration evidence | https://github.com/tianocore/edk2 | BSD-2-Clause-Patent; evidence only |
| OSDev community | 2026-08-19 | Partial hard-coded `_S5` shutdown warning | https://wiki.osdev.org/Shutdown | Community evidence; no code copied |
