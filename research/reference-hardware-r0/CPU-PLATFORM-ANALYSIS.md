# CPU and platform analysis for reference hardware R0

**Status:** RESEARCH — no hardware is certified and no architecture decision is
accepted by this document.
**Research date:** 2026-08-19
**Scope:** x86_64 desktop bring-up, with QEMU as the deterministic virtual reference and
AMD/Intel physical diversity.

## Evidence labels

- **OFFICIAL FACT** — stated by a processor vendor, motherboard vendor, standards body, or
  specification owner.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — behavior or engineering practice visible in an
  official open-source OS or virtual-machine project. It is evidence, not a Malrynth
  requirement and not permission to copy code.
- **COMMUNITY EVIDENCE** — a useful operational report or practitioner reference without
  vendor/specification authority; never sufficient by itself for a hardware contract.
- **INFERENCE** — a conclusion drawn from the cited facts; it still needs validation.
- **PROPOSED MALRYNTH DECISION** — a recommendation for later review/ADR, not an accepted
  decision and not an implementation claim.

## Executive recommendation

**PROPOSED MALRYNTH DECISION:** Keep QEMU q35/OVMF as the deterministic virtual reference,
then qualify physical hardware in this order:

1. **Primary family:** Intel Comet Lake-S/Embedded, specifically a non-`F`
   i5-10500/10500E/10500TE-class six-core CPU, on Q470/Q470E. The strongest documented first
   specimen is **MSI MS-98N9 Q470E**; **ASUS Q470EI-IM-A** is a compact alternative after
   exact UART qualification.
2. **Used-market Intel alternative:** Coffee Lake-S/Q370 with a non-`F` i5-9500/i5-8500,
   preferably **Supermicro X11SCQ** or ASUS PRIME Q370M-C/CSM plus a verified I210 adapter.
3. **Cross-vendor fallback:** AMD Ryzen 5000G, specifically Ryzen 5 5600G/PRO 5650G, on a
   B550 business micro-ATX board. Prefer **ASUS Pro B550M-C/CSM**; retain ASRock B550M Pro4
   as a lower-cost alternative whose ASMedia-hub ports are excluded from first USB tests.

These are qualification candidates, not a claim of generic family support. Record exact
board revision, firmware build, CPU stepping/microcode, DIMMs, storage and firmware tables.

**INFERENCE:** Q470E/Comet Lake-S is older and less capable than a current enthusiast system,
but unusually suitable for first silicon: all six cores are homogeneous; non-`F` CPUs have
an iGPU; industrial candidates expose serial/debug, Intel Ethernet, TPM and ordinary NVMe/
USB; and the platform predates hybrid-core scheduling. This lowers bring-up ambiguity while
still exercising UEFI, ACPI, SMP, PCIe and a real VT-d implementation.

**INFERENCE:** The chief challenge is acquisition cost and lifecycle, not architecture.
Q470E industrial boards may be expensive even while firmware remains available; Q370 stock
is likely used or new-old-stock. Freeze revision labels and exact firmware. This research
authorizes no purchase or spare-board acquisition.

## Why desktop first

**OFFICIAL FACT:** Malrynth already targets x86_64, boots as a UEFI application, and
receives an ACPI RSDP. Current project state is QEMU-only; physical bring-up, interrupts,
timers, SMP, ACPI parsing, PCIe, and IOMMU support are not implemented.

**INFERENCE:** A single-socket desktop is the smallest physical platform that exercises the
interfaces a desktop OS ultimately needs—UEFI, ACPI, local and I/O APICs, multiple logical
processors, PCIe, USB, NVMe, an IOMMU, integrated graphics, thermal control, and suspend—while
remaining replaceable and locally observable. A laptop adds embedded-controller,
battery/backlight, lid, low-power-idle, soldered-device, and vendor-method complexity before
the base PC platform is stable. A server adds NUMA, multi-socket, RAS, hotplug, and management
controller complexity. Neither is an efficient first physical target.

**PROPOSED MALRYNTH DECISION:** R0 physical support means one explicitly recorded
single-socket desktop configuration. It does **not** mean generic PC compatibility. Hardware
breadth begins only after the reference pair passes deterministic conformance tests.

## Family-first shortlist

| Priority | CPU/platform family | Concrete CPU | Board/chipset class | Concrete board | Why it belongs | Qualification risks |
|---|---|---|---|---|---|---|
| 1 | Intel Comet Lake-S/Embedded, 10th generation | Core i5-10500/10500E/10500TE-class | Q470E industrial ATX/mini-ITX | MSI MS-98N9 Q470E; ASUS Q470EI-IM-A | Homogeneous cores, iGPU, VT-d; onboard I210-AT + I219LM, serial/debug, TPM and M.2 | Industrial price/availability; freeze exact SKU; ASUS manual does not explicitly prove 16550 compatibility |
| 2 | Intel Coffee Lake-S, 8th/9th generation | Core i5-9500; i5-8500 substitute | Q370 commercial/industrial | Supermicro X11SCQ or ASUS PRIME Q370M-C/CSM + I210 | Used-market cost path; homogeneous cores/iGPU; X11SCQ explicitly documents 16550 and I210 | Older stock; exact firmware/revision; ASUS needs I210 and UART qualification |
| 3 | AMD Cezanne/Ryzen 5000G | Ryzen 5 5600G/PRO 5650G | B550 business mATX | ASUS Pro B550M-C/CSM | Homogeneous 6C/12T, iGPU; COM, LPC debug, speaker, onboard TPM2, dual M.2 | Realtek NIC; exact IVRS/isolation and UART must be measured; CPU links are PCIe 3.0 |
| 4 | AMD Cezanne/Ryzen 5000G | Ryzen 5 5600G | B550 value mATX | ASRock B550M Pro4 | Documented COM/TPM headers, M.2 and expansion | Realtek NIC; some rear USB ports sit behind ASM1074; lower pre-kernel observability |

**PROPOSED MALRYNTH DECISION:** Qualify the Comet Lake-S/Q470E family contract first, but
freeze one exact specimen as the oracle. Q370 is an acquisition fallback, not permission to
claim both generations supported. Exclude `F`-suffix processors because they remove the iGPU;
exclude Pentium/Celeron parts because they reduce SMP coverage; exclude Xeon/ECC initially.

## Candidate platform facts

### Intel primary: Q470E

**OFFICIAL FACT:** Intel lists Q470E with VT-d, Intel PTT, 24 PCH PCIe 3.0 lanes, USB and
SATA capabilities. The i5-10500TE is a six-core/twelve-thread Comet Lake-S Embedded part with
UHD 630, VT-x/EPT and VT-d; the exact board CPU list remains controlling.
[Q470E chipset](https://www.intel.com/content/www/us/en/products/sku/203700/intel-q470e-chipset/specifications.html),
[Core i5-10500TE](https://www.intel.com/content/www/us/en/products/sku/203891/intel-core-i510500te-processor-12m-cache-up-to-3-70-ghz/specifications.html)

**OFFICIAL FACT:** MSI documents MS-98N9 Q470E with I210-AT + I219LM, chipset USB,
NVMe-capable M.2, LPC/SPI debug and a 16550A-compatible UART. ASUS documents Q470EI-IM-A
with Q470E, I210-AT + I219LM, five COM ports, M.2, TPM, LPC debug, xHCI hand-off and VT-d.
[MSI manual](https://download.msi.com/archive/mnu_exe/ipc/MS-98N9v1.2.pdf),
[ASUS manual](https://dlcdnets.asus.com/pub/ASUS/mb/Embedded_IPC/Q470EI-IM-A/E21947_Q470EI-IM-A_UM_v5_WEB.pdf?model=Q470EI-IM-A)

**INFERENCE:** MSI is the stronger debug oracle because its reviewed manual explicitly
states UART compatibility. ASUS is smaller but its UART implementation must be identified
rather than inferred from “COM.”

### Intel used-market alternative: Q370

**OFFICIAL FACT:** Intel lists the
[Core i5-9500](https://www.intel.com/content/www/us/en/products/sku/134895/intel-core-i59500-processor-9m-cache-up-to-4-40-ghz/specifications.html)
as a discontinued six-core/six-thread 65 W FCLGA1151 processor with UHD Graphics 630,
16 PCIe 3.0 lanes, VT-x, EPT, VT-d, idle states, Enhanced SpeedStep and thermal monitoring.
The [Core i5-8500](https://www.intel.com/content/www/us/en/products/sku/129939/intel-core-i58500-processor-9m-cache-up-to-4-10-ghz/specifications.html)
has the same core/thread count, socket, 65 W class, UHD 630 and virtualization set, at lower
maximum turbo frequency.

**OFFICIAL FACT:** Intel lists the
[Q370 chipset](https://www.intel.com/content/www/us/en/products/sku/133282/intel-q370-chipset/specifications.html)
with VT-d, Platform Trust Technology (PTT), vPro eligibility, 24 chipset PCIe lanes and no
ECC-memory support. These chipset fields do not prove how a particular board's firmware
configures the facilities.

**OFFICIAL FACT:** ASUS documents PRIME Q370M-C/CSM as supporting 8th/9th-generation LGA1151
processors and providing Intel I219-LM Ethernet, two COM headers, a speaker header, an ASUS
LPC debug-card header, an onboard TPM 2.0 IC, two M.2 storage sockets, six SATA ports, AMI
UEFI and ACPI 6.1. [Board manual](https://dlcdnets.asus.com/pub/ASUS/mb/LGA1151/PRIME_Q370M-C/E14162_PRIME_Q370M-C_UM_WEB.pdf),
[ASUS specifications](https://www.asus.com/us/motherboards-components/motherboards/prime/prime-q370m-c-csm/techspec/)

**INFERENCE:** Q370 is a useful cost alternative, but three marketing traps must stay
explicit: the COM ports are internal headers rather than rear DE-9 connectors; LPC debug
requires ASUS's compatible card; and “TPM IC onboard” is a discrete board device, not proof
that firmware will expose Intel PTT or that either TPM path is correctly provisioned.

### AMD fallback

**OFFICIAL FACT:** AMD identifies Ryzen 5 5600G as a Zen 3/Cezanne, six-core/twelve-thread,
65 W AM4 processor with integrated Radeon graphics and PCIe Gen 3. The official AM4 chipset
matrix lists Ryzen 5000 support on B550. [AMD Ryzen consumer guide](https://www.amd.com/content/dam/amd/en/documents/partner-hub/ryzen/amd-consumer-pocket-guide-ryzen-radeon-july-2024.pdf),
[AMD AM4 chipsets](https://www.amd.com/en/products/processors/chipsets/am4.html)

**OFFICIAL FACT:** ASUS lists Pro B550M-C/CSM with a B550 chipset, onboard TPM 2.0 IC, one
COM header, an LPC debug header, speaker, two M.2 storage sockets, AMI UEFI and Realtek
RTL8111H Ethernet. [ASUS specifications](https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/)

**OFFICIAL FACT:** MSI lists PRO B550M-P with one COM header, a TPM 2.0 module header, four
EZ Debug LEDs, two M.2 sockets and RTL8111H Ethernet. It does not claim an onboard TPM or a
general LPC debug header. [MSI specifications](https://www.msi.com/Motherboard/PRO-B550M-P/Specification)

**INFERENCE:** ASUS B550 is the meaningful vendor-diversity control because it preserves the
same serial/LPC/TPM observability pattern. MSI is a budget procurement fallback, not an equal
debugging oracle. Neither product page establishes IVRS correctness, interrupt-remapping
coverage or useful isolation groups; measure those on the exact firmware.

**PROPOSED MALRYNTH DECISION:** Use stock clocks and JEDEC memory settings. Disable XMP/DOCP,
Precision Boost Overdrive, undervolting and board auto-overclocking. Reproducibility matters
more than peak performance.

## TPM boundary

**OFFICIAL FACT:** The TCG TPM 2.0 Library defines TPM commands, data structures and
cryptographic behavior; the PC Client Platform TPM Profile constrains how a PC platform
implements and exposes that TPM. [TCG TPM 2.0 Library](https://trustedcomputinggroup.org/resource/tpm-library-specification/),
[TCG PC Client profile](https://trustedcomputinggroup.org/resource/pc-client-platform-tpm-profile-ptp-specification/)

**OFFICIAL FACT:** Q470E and Q370 advertise Intel PTT capability, while investigated boards
also expose onboard or header-based TPM 2.0 options. These are distinct implementations.
The operating system must discover the active interface through UEFI/ACPI/TCG mechanisms;
it must not choose a transport from a chipset name.

**PROPOSED MALRYNTH DECISION:** R0 inventories the TPM2 ACPI table, UEFI TCG2 protocol/event
log when present, interface type, manufacturer/firmware identifiers, PCR banks and clear/
ownership state. It does not seal boot-critical secrets, take ownership or clear a TPM during
bring-up. Measured boot and key custody require a separate threat model, recovery policy and
physical-presence test plan. A missing/broken TPM is a reported capability failure, not a
reason to weaken IOMMU/DMA policy.

## CPU architectural baseline

**OFFICIAL FACT:** The current
[Intel 64 and IA-32 Software Developer's Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
cover interrupt/exception handling, multiprocessor support, APIC/x2APIC, thermal/power
management, VMX, debugging, and performance monitoring. AMD's current
[AMD64 Architecture Programmer's Manual, Volume 2](https://docs.amd.com/v/u/en-US/24593_3.44_APM_Vol2)
(revision 3.44, 2026-03-06) defines AMD64 system programming, including APIC, x2APIC, SVM,
and system registers.

**PROPOSED MALRYNTH DECISION:** Discover every optional architectural feature with CPUID and
model-specific capability checks. Vendor name or marketing generation must never imply that
a feature exists or is enabled.

Minimum R0 CPU assumptions should remain deliberately small:

- x86-64 long mode and the already selected kernel target;
- local APIC presence as reported architecturally and described by firmware;
- NX, SSE2, and other features only when current kernel policy explicitly requires them;
- no dependency on AVX, AVX-512, VMX, SVM, invariant TSC, TSC deadline, x2APIC, or SMT until
  each is detected and its fallback path is tested.

**INFERENCE:** The two candidates support much more than this baseline. Keeping the kernel
baseline below the reference hardware prevents accidental dependence on a single generation.

## APIC, x2APIC, and interrupt routing

**OFFICIAL FACT:** ACPI 6.6 defines the Multiple APIC Description Table (MADT), including
processor local APIC/x2APIC entries, I/O APICs, interrupt-source overrides, NMIs, and an
optional multiprocessor-wakeup structure. See the
[ACPI 6.6 system-description-table chapter](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html#multiple-apic-description-table-madt).

**OFFICIAL FACT:** Intel's APIC architecture exposes xAPIC registers through MMIO and x2APIC
registers through MSRs. Intel now documents a phased
[xAPIC deprecation plan](https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/xapic-deprecation-plan.html)
and recommends x2APIC on affected systems. AMD's architecture manual also defines both
modes. This does not prove that firmware enables x2APIC on a particular board.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux retains multiple APIC drivers and falls back
on hardware without x2APIC; its
[x86 Kconfig](https://github.com/torvalds/linux/blob/master/arch/x86/Kconfig)
also ties full x2APIC use on bare metal to interrupt-remapping support. Linux's
[local APIC implementation](https://github.com/torvalds/linux/blob/master/arch/x86/kernel/apic/apic.c)
contains substantial mode selection and firmware/platform handling. These files are
GPL-2.0-family code and must be studied, not copied.

**PROPOSED MALRYNTH DECISION:** Bring up interrupts in this order:

1. validate MADT and create a firmware-identity map keyed by ACPI processor UID and APIC ID;
2. establish the BSP local APIC in the currently active safe mode;
3. enumerate I/O APICs and apply every MADT interrupt-source override, including polarity
   and trigger mode;
4. route a single diagnostic timer interrupt, then external interrupts;
5. add x2APIC as a detected mode with an xAPIC fallback;
6. enable interrupt remapping before granting untrusted drivers MSI/MSI-X authority.

**PROPOSED MALRYNTH DECISION:** Do not assume IRQ 0 maps directly to global interrupt 0,
IRQ 9 has a fixed polarity, one I/O APIC exists, APIC IDs are dense, or logical CPU number
equals APIC ID.

## SMP and CPU topology

**OFFICIAL FACT:** x86 platform firmware identifies enabled processors/APIC IDs through MADT,
while vendor-specific CPUID leaves describe thread/core/die/package topology. These are
different questions: MADT answers which interrupt-controller endpoints firmware exposes;
CPUID describes the processor's resource topology.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux's
[x86 topology documentation](https://docs.kernel.org/arch/x86/topology.html)
uses ordered vendor-specific CPUID fallbacks. Current Linux prefers AMD leaf 0x80000026,
then 0xB, with older fallbacks; for Intel it prefers leaf 0x1F, then 0xB, then older leaves.
It also demonstrates that firmware enumeration is not necessarily a sane, dense logical
numbering. The implementation is GPL-2.0-family evidence, not reusable Malrynth code.

**OFFICIAL FACT:** The processor manuals define INIT and startup IPI sequencing and the
architectural state in which application processors begin. Firmware MP services are boot
services; they are not a post-ExitBootServices replacement for kernel SMP startup.

**PROPOSED MALRYNTH DECISION:** The BSP allocates a per-CPU record for every validated MADT
entry, assigns a dense Malrynth CPU number independently of APIC ID, and starts APs through a
small physical-address trampoline. Each AP must report explicit milestones—entered
trampoline, long mode, per-CPU state installed, local APIC ready, scheduler-ready—before it
is counted online.

**PROPOSED MALRYNTH DECISION:** Initial physical acceptance runs with SMT disabled, then
enabled. SMT is not a separate core, and security/performance policy must retain sibling
topology rather than flattening every logical processor.

## Timers

**OFFICIAL FACT:** x86 PC platforms may expose several independent timing facilities:
the TSC, local APIC timer (including detected TSC-deadline mode), ACPI PM timer, HPET, RTC,
and legacy PIT. The
[ACPI 6.6 hardware specification](https://uefi.org/specs/ACPI/6.6/04_ACPI_Hardware_Specification.html)
defines the PM timer interface. The older but still relevant
[IA-PC HPET 1.0a specification](https://www.intel.com/content/dam/www/public/us/en/documents/technical-specifications/software-developers-hpet-spec-1-0a.pdf)
defines a firmware-enumerated free-running counter plus comparators; the document itself
contains restrictive/no-license wording and must be treated as read-only research material.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux separates clock sources from clock-event
devices, as documented in
[Clock sources, clock events, sched_clock and delay timers](https://docs.kernel.org/timers/timekeeping.html).
That distinction is useful evidence: reading monotonically increasing time and scheduling a
wakeup are separate responsibilities.

**PROPOSED MALRYNTH DECISION:** Use a capability-ranked timer policy, never a single hard
coded source:

- begin with a firmware-described reference counter (ACPI PM timer or validated HPET) for
  calibration;
- use TSC as a monotonic clock source only after CPUID/vendor checks and cross-CPU
  synchronization tests pass;
- prefer the local APIC TSC-deadline timer when detected and validated; otherwise use APIC
  one-shot mode;
- keep one independent reference source for drift/monotonicity checks;
- test counter rollover, SMP skew, frequency transitions, idle, and virtualization.

**INFERENCE:** A timer that works in QEMU can still fail on physical firmware because QEMU's
device model and host time source do not reproduce every chipset quirk. Conversely, a fast
TSC on one desktop does not establish an architectural guarantee for all x86-64 systems.

## Virtualization

**OFFICIAL FACT:** Intel VMX/VT-x and AMD SVM virtualize CPU execution. Intel VT-d and AMD
IOMMU/AMD-Vi remap device DMA and interrupts. They are separate capabilities and must not be
collapsed into one “virtualization enabled” flag.

**OFFICIAL FACT:** QEMU provides both full emulation (TCG) and accelerator backends. Its
[x86 CPU model guidance](https://www.qemu.org/docs/master/system/i386/cpu.html)
explains that host-passthrough exposes host-specific features while named CPU models provide
a more controlled guest contract.

**PROPOSED MALRYNTH DECISION:** Maintain at least these virtual test profiles:

| Profile | Purpose |
|---|---|
| QEMU TCG, pinned named CPU, 1 vCPU | deterministic architectural minimum and fallbacks |
| QEMU TCG, same CPU, 4 vCPUs | AP startup, IPIs, APIC timer, SMP races |
| KVM, named CPU model | hardware-accelerated stable feature contract |
| KVM, host-passthrough on AMD | vendor-specific CPUID/timer exposure |
| KVM, host-passthrough on Intel | second-vendor exposure |

**PROPOSED MALRYNTH DECISION:** Guest VMX/SVM support is not an R0 requirement. Detect it,
log it, and leave it disabled until Malrynth deliberately implements a hypervisor boundary.
Nested virtualization must never be required for ordinary kernel tests.

## PCIe and chipset considerations

**OFFICIAL FACT:** The current
[PCI Express Base specification](https://pcisig.com/specification-overview/pci-express-base)
is revision 7.0, but an endpoint's link generation is independent of the OS programming
model used for basic enumeration. The current
[PCI Firmware Specification](https://pcisig.com/specification-overview/pci-firmware)
is revision 3.3 plus published ECNs. It covers firmware/OS ownership and PCI-family
configuration interfaces.

**OFFICIAL FACT:** Both candidate boards expose CPU- and chipset-connected PCIe resources.
The Coffee Lake/Q370 side is PCIe 3.0; although B550 can expose PCIe 4.0 with some processors,
the 5600G is a PCIe 3.0 processor. Board slot shape is therefore not proof of electrical
width, link generation, isolation or IOMMU ownership. [Intel i5-9500](https://www.intel.com/content/www/us/en/products/sku/134895/intel-core-i59500-processor-9m-cache-up-to-4-40-ghz/specifications.html),
[AMD Ryzen consumer guide](https://www.amd.com/content/dam/amd/en/documents/partner-hub/ryzen/amd-consumer-pocket-guide-ryzen-radeon-july-2024.pdf)

**PROPOSED MALRYNTH DECISION:** Enumerate PCI domains, root bridges, bus ranges, and resource
windows from firmware. Use ECAM only for validated MCFG segments/bus ranges; retain a
controlled legacy configuration-access fallback only where the platform contract explicitly
requires it. Never derive a BAR mapping from marketing-page lane counts.

**PROPOSED MALRYNTH DECISION:** The first physical configuration should contain only CPU,
one memory kit, one NVMe device, onboard UART, onboard Ethernet, and integrated graphics.
Add one device class at a time and record the resulting ACPI, PCI, interrupt, and IOMMU
topology delta.

## Microcode

**OFFICIAL FACT:** Intel's
[processor microcode repository](https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files)
states that BIOS loading is preferred, some updates are BIOS-only, and OS early loading is
supported for a subset of processors. The binary redistribution license permits unmodified
binary redistribution subject to notice conditions and forbids reverse engineering.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** The Linux
[microcode loader documentation](https://docs.kernel.org/arch/x86/microcode.html)
applies a matching update to the BSP before SMP, then to APs, and caches it for resume. It
also explains why late loading is difficult and disabled by default. Linux loader code is
GPL-2.0-family; the vendor blobs have separate licenses.

**OFFICIAL FACT:** AMD microcode binaries distributed by the upstream
[linux-firmware project](https://kernel.googlesource.com/pub/scm/linux/kernel/git/firmware/linux-firmware/+/refs/heads/main/amd-ucode/)
are covered by a separate AMD binary redistribution license. Availability in that repository
does not prove coverage for every consumer CPU or supersede board firmware.

**PROPOSED MALRYNTH DECISION:** For R0, update the motherboard firmware to a recorded vendor
release and log CPUID family/model/stepping plus microcode revision on every boot. Do not ship
or load vendor microcode blobs until provenance, CPU coverage, signature/authenticity,
rollback policy, update ordering, and exact redistribution terms have passed legal and
security review. When OS loading exists, early load before AP startup is the default; late
load is a separate high-risk feature.

## Acceptance gates for any physical reference board

**PROPOSED MALRYNTH DECISION:** A product page is insufficient. A board becomes an R0
reference only after all gates pass with a pinned firmware version:

- UEFI boot succeeds without CSM/legacy mode, and the final memory map is internally valid;
- RSDP, XSDT, FADT, MADT, MCFG, DSDT/SSDT, HPET (if present), and vendor IOMMU tables all
  pass bounds and checksum validation;
- every enabled processor in MADT reaches the AP-ready milestone; APIC IDs need not be dense;
- one-shot timer tests pass on every CPU, and the selected clock source remains monotonic
  through SMT, idle, and sustained load;
- both xAPIC fallback and x2APIC (when exposed) are tested;
- physical UART output is captured from reset/loader through panic using the board's
  documented connector and correct electrical adapter;
- PCI inventory and BAR windows are stable across three cold boots;
- IOMMU coverage, reserved regions, interrupt remapping, faults, and minimum isolation groups
  are measured—not inferred from the CPU name;
- cold reboot and ACPI S5 poweroff succeed repeatedly; suspend is not an R0 gate;
- firmware settings, table hashes, PCI IDs, CPU/microcode revision, memory part numbers, and
  serial logs are retained with the test result.

## Rejected shortcuts

**PROPOSED MALRYNTH DECISION:** Reject these shortcuts for R0:

- one vendor only;
- a hybrid Intel CPU as the first SMP platform;
- a laptop as first physical hardware;
- assuming fixed COM1, IRQ, APIC, HPET, or PCI addresses without firmware/board evidence;
- equating CPU VT-d/AMD-V support with a usable platform IOMMU;
- enabling every CPUID feature globally from the BSP without checking AP consistency;
- treating a successful QEMU boot as physical-platform validation;
- copying Linux, QEMU, ACPICA, EDK II, vendor-manual text, or register definitions without
  license/provenance review.

## Source and licensing notes

All links were accessed 2026-08-19. Vendor product pages and architecture manuals are
authoritative for the stated product/architecture facts but are proprietary documentation,
not source-code licenses. UEFI/ACPI and PCI-SIG specification access is governed by their
owners' terms; do not redistribute specification text. Linux and QEMU are implementation
evidence under GPL-2.0-family terms; no code was copied. Intel and AMD microcode are binary
artifacts with separate restrictive redistribution terms and are not included here.

## Source ledger contributions

| Authority | Accessed | Claim contributed | URL | Licensing relevance |
|---|---|---|---|---|
| Intel | 2026-08-19 | i5-10500TE 6C/12T, UHD 630, VT-x/EPT/VT-d and power features | https://www.intel.com/content/www/us/en/products/sku/203891/intel-core-i510500te-processor-12m-cache-up-to-3-70-ghz/specifications.html | Product facts only |
| Intel | 2026-08-19 | Q470E VT-d, PTT, PCIe and USB platform facts | https://www.intel.com/content/www/us/en/products/sku/203700/intel-q470e-chipset/specifications.html | Product facts only |
| MSI / ASUS | 2026-08-19 | Q470E UART, debug, Intel NIC, M.2, TPM and firmware controls | https://download.msi.com/archive/mnu_exe/ipc/MS-98N9v1.2.pdf | Manual facts only |
| Intel | 2026-08-19 | i5-9500: 6C/6T, 65 W, UHD 630, PCIe 3.0, VT-x/EPT/VT-d, idle and thermal features; lifecycle | https://www.intel.com/content/www/us/en/products/sku/134895/intel-core-i59500-processor-9m-cache-up-to-4-40-ghz/specifications.html | Product facts only |
| Intel | 2026-08-19 | i5-8500 same-shape fallback facts and lifecycle | https://www.intel.com/content/www/us/en/products/sku/129939/intel-core-i58500-processor-9m-cache-up-to-4-10-ghz/specifications.html | Product facts only |
| Intel | 2026-08-19 | Q370 VT-d, PTT, vPro eligibility, chipset lanes and lack of ECC | https://www.intel.com/content/www/us/en/products/sku/133282/intel-q370-chipset/specifications.html | Product facts only |
| ASUS | 2026-08-19 | Q370 board CPU support, I219-LM, COM/LPC debug/speaker, onboard TPM, storage, AMI UEFI/ACPI 6.1 | https://dlcdnets.asus.com/pub/ASUS/mb/LGA1151/PRIME_Q370M-C/E14162_PRIME_Q370M-C_UM_WEB.pdf | Manual facts; no text/code copied |
| AMD | 2026-08-19 | Ryzen 5 5600G 6C/12T, Zen 3, 65 W, iGPU and PCIe 3.0 | https://www.amd.com/content/dam/amd/en/documents/partner-hub/ryzen/amd-consumer-pocket-guide-ryzen-radeon-july-2024.pdf | Product facts only |
| AMD | 2026-08-19 | B550/Ryzen 5000 compatibility and chipset lane classes | https://www.amd.com/en/products/processors/chipsets/am4.html | Product facts only |
| ASUS | 2026-08-19 | B550 board COM/LPC debug/speaker, onboard TPM2, storage, AMI UEFI and RTL8111H | https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/ | Product facts only |
| MSI | 2026-08-19 | B550 alternative COM, TPM header, debug LEDs, storage and RTL8111H | https://www.msi.com/Motherboard/PRO-B550M-P/Specification | Product facts only |
| Intel | 2026-08-19 | x86 architectural contract: CPUID, APIC, SMP, VMX, timers, power and debug | https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html | Proprietary documentation; no code copied |
| AMD | 2026-08-19 | AMD64 system programming, APIC/x2APIC, SVM and registers | https://docs.amd.com/v/u/en-US/24593_3.44_APM_Vol2 | Specification agreement; no code copied |
| UEFI Forum | 2026-08-19 | MADT, PM timer and firmware-described platform topology | https://uefi.org/specs/ACPI/6.6/ | Specification terms; no code copied |
| TCG | 2026-08-19 | TPM 2.0 library model and PC-client platform profile | https://trustedcomputinggroup.org/resource/tpm-library-specification/ | TCG specification terms; no code copied |
| Linux kernel project | 2026-08-19 | Existing-OS topology, APIC, timekeeping and microcode implementation evidence | https://docs.kernel.org/arch/x86/topology.html | GPL-2.0-family ecosystem; behavior only, no code copied |
| QEMU project | 2026-08-19 | Named vs host-passthrough CPU-model test contracts | https://www.qemu.org/docs/master/system/i386/cpu.html | GPL-2.0 project; usage evidence only |
