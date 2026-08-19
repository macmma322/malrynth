# Desktop-first power management for MALRYNTH R0

**Status:** research and acceptance policy, 2026-08-19.
**Primary target:** Intel Comet Lake-S/Q470E.
**Cross-vendor target:** AMD Cezanne/Ryzen 5 5600G/B550.

## Evidence labels

- **OFFICIAL FACT** — specification-owner or vendor statement.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — behavior in an official upstream project;
  evidence only, not code to copy.
- **COMMUNITY EVIDENCE** — practitioner evidence without normative authority.
- **INFERENCE** — conclusion requiring validation on the frozen specimen.
- **PROPOSED MALRYNTH DECISION** — proposed policy, not implemented support.

## Decision summary

**PROPOSED MALRYNTH DECISION:** Deliver desktop power in dependency order:

1. safe processor idle (`HLT`/C1) and idle accounting;
2. reliable reset and ACPI S5 soft-off;
3. power-button/fixed-event handling;
4. thermal emergency visibility while firmware retains fan control;
5. CPU performance control (Intel first, AMD second);
6. device D-states and wake policy;
7. S3/S4/low-power-S0 only after complete resume infrastructure exists.

**PROPOSED MALRYNTH DECISION:** Never report “power management supported” as one boolean.
Expose independent capability/test state for idle, performance, reset, S5, power button,
thermal visibility, device PM, S3, S4 and low-power S0.

## ACPI state model

**OFFICIAL FACT:** ACPI separates global/system states, device D-states, processor C-states
and performance states. S1–S4 are sleeping states; S5 is soft-off in G2 and retains no OS
context, though parts of the platform may remain powered. [ACPI waking and sleeping](https://uefi.org/specs/ACPI/6.6/16_Waking_and_Sleeping.html)

**OFFICIAL FACT:** ACPI defines objects/interfaces such as `_Sx`, `_PTS`, `_TTS`, `_WAK`,
`_PRW`, `_PS0`–`_PS3`, `_CST`, `_PSS`, `_CPC` and low-power-idle descriptions.
[ACPI 6.6](https://uefi.org/specs/ACPI/6.6/)

| Layer | R0 contract |
|---|---|
| CPU C-state | C1 only at first; deeper states remain described-but-disabled. |
| CPU performance | Capability-probed backend; no fixed frequency claim. |
| System S-state | S0 and S5 first; S3/S4 inventory only. |
| Device D-state | D0 default; per-driver opt-in after reset/wake testing. |
| Platform G-state | Reset and G2/S5 behavior explicitly measured. |

## C1 idle first

**OFFICIAL FACT:** Intel lists idle-state support and Enhanced SpeedStep for the
[Core i5-10500TE](https://www.intel.com/content/www/us/en/products/sku/203891/intel-core-i510500te-processor-12m-cache-up-to-3-70-ghz/specifications.html).
Architecturally, `HLT` stops instruction execution until an enabled wake event/interrupt or
other architecturally defined condition. Vendor manuals define deeper model-specific states.

**PROPOSED MALRYNTH DECISION:** The first idle loop is:

1. disable local interrupts while checking the run queue/wakeup generation;
2. if work appeared, restore state and schedule it;
3. otherwise atomically restore interrupt delivery and execute `HLT` using an ordering that
   cannot lose a wakeup;
4. on return, account entry/exit and service the event.

Never execute `HLT` with interrupts accidentally masked and no validated alternate wake
source. Add deeper C-states only after timer, interrupt, TSC monotonicity and latency tests
pass on every CPU.

**PROPOSED MALRYNTH DECISION:** Begin with periodic/one-shot wake stress, randomized remote
IPIs, scheduler enqueues and device interrupts. Test online/offline and panic transitions so
an idle CPU is never silently stranded.

## Reset policy

**OFFICIAL FACT:** ACPI FADT can describe a reset register/value; UEFI provides
`ResetSystem()` as a runtime service. CPU/chipset mechanisms also exist but are
platform-specific. [ACPI FADT](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html),
[UEFI ResetSystem](https://uefi.org/specs/UEFI/2.11/08_Services_Runtime_Services.html)

**PROPOSED MALRYNTH DECISION:** Choose and report a reset path rather than blindly spray
several registers. During loader-stage failure, use UEFI reset. After kernel ownership,
prefer a validated FADT reset register; use UEFI runtime reset only if runtime mappings/calling
convention are deliberately supported. A final platform-specific fallback is isolated behind
the exact-board profile.

Before reset: stop new user work, flush the authoritative serial marker and persistent
storage only while bounded and safe, disable/quiesce DMA where possible, stop APs, then issue
one selected mechanism. Reset timeout emits a last marker and takes the next *documented*
fallback; it never loops indefinitely.

## S5 soft-off

**OFFICIAL FACT:** ACPI defines the S5 transition through namespace/sleep objects and either
legacy PM control registers or the hardware-reduced interface, with optional transition
methods. [ACPI sleep transitions](https://uefi.org/specs/ACPI/6.6/16_Waking_and_Sleeping.html)

**PROPOSED MALRYNTH DECISION:** Implement S5 through the selected bounded ACPI engine:

1. reject new work and report transition-in-progress;
2. sync/stop storage under a bounded shutdown policy;
3. revoke user-driver devices and quiesce DMA/IOMMU domains;
4. stop secondary CPUs and mask unrelated wake/event sources;
5. evaluate required transition methods with time/instruction limits;
6. program the firmware-described sleep interface exactly once;
7. if still executing after timeout, report failure over polled serial and offer explicit
   reset/halt policy rather than writing guessed ports.

**COMMUNITY EVIDENCE:** OSDev's shutdown notes show why extracting `_S5` constants and
hard-coding legacy PM registers works only on a subset of machines. This is an operational
warning, not a normative source. [OSDev Shutdown](https://wiki.osdev.org/Shutdown)

## Power button and events

**OFFICIAL FACT:** ACPI defines fixed power-button events and control-method power-button
devices, plus SCI/GPE handling. A physical long-press override can remain a hardware/firmware
mechanism outside OS policy. [ACPI event model](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html)

**PROPOSED MALRYNTH DECISION:** A short press queues one high-level event outside interrupt
context. Default R0 policy requests orderly S5 from the shell/session manager when safe; the
kernel event layer itself does not run a complex shutdown in SCI context. Debounce duplicate
status/notify paths, rate-limit logs and mask storming unknown GPEs while preserving counters.

## Intel performance control

**OFFICIAL FACT:** Intel documents legacy P-state mechanisms and Hardware-Controlled
Performance States (HWP) in the Intel SDM. Availability and controls are enumerated through
CPUID/MSRs; a processor family name is insufficient. [Intel SDM](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux `intel_pstate` maintains separate paths for
HWP and non-HWP systems and coordinates policy with scheduler/load information. This
demonstrates the need for capability probing and bounded policy, not an API to copy.
[Linux intel_pstate](https://docs.kernel.org/admin-guide/pm/intel_pstate.html)

**PROPOSED MALRYNTH DECISION:** On the selected i5-10500/10500E/10500TE-class specimen, inventory CPUID, HWP capability MSRs, ACPI
`_PSS`/`_CPC`, firmware settings and effective frequencies before selecting a backend. Prefer
HWP only if the exact CPU/firmware exposes a coherent interface; otherwise use a validated
legacy mechanism or leave firmware policy intact. Start with conservative minimum/maximum and
nominal requests; turbo is permitted only as hardware policy, never assumed performance.

## AMD performance control

**OFFICIAL FACT:** AMD's architecture programming manual and ACPI CPPC describe performance
capabilities/requests distinct from a fixed clock. [AMD APM Volume 2](https://docs.amd.com/v/u/en-US/24593_3.44_APM_Vol2),
[ACPI CPPC](https://uefi.org/specs/ACPI/6.6/08_Processor_Configuration_and_Control.html)

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux `amd-pstate` uses CPPC performance hints and
documents multiple operating modes. [Linux amd-pstate](https://docs.kernel.org/admin-guide/pm/amd-pstate.html)

**PROPOSED MALRYNTH DECISION:** Enable a 5600G CPPC backend only when CPUID/MSRs and
firmware `_CPC` form a coherent supported interface. Otherwise validate legacy ACPI states or
leave firmware policy untouched. Do not assume every AM4 firmware exposes the interface used
by current Linux on newer AMD systems.

Cross-vendor policy uses abstract minimum/nominal/maximum/desirable performance plus energy-
versus-latency intent. Vendor-specific register semantics stay in backends.

## Thermal safety

**OFFICIAL FACT:** The i5-10500TE page advertises thermal-monitoring technologies; the MSI
Q470E and ASUS B550 boards provide firmware monitoring/fan features.
[Intel i5-10500TE](https://www.intel.com/content/www/us/en/products/sku/203891/intel-core-i510500te-processor-12m-cache-up-to-3-70-ghz/specifications.html),
[MSI Q470E downloads/manual index](https://ipc.msi.com/product_download/Industrial-Motherboard/ATX/MS-98N9)

**PROPOSED MALRYNTH DECISION:** R0 leaves firmware fan curves and CPU hardware thermal
protection enabled. It logs architectural thermal status/throttling when documented, checks
that sustained stress does not produce critical events, and provides an emergency orderly
shutdown path. It does not take board-fan ownership from undocumented sensor mappings.

**INFERENCE:** An uncalibrated temperature number is telemetry, not a safe control signal.
Fan control waits for board-specific sensor/fan mapping plus failed-fan and sensor-fault tests.

## Device power and suspend deferral

**OFFICIAL FACT:** ACPI defines D0–D3, power resources, `_PSx`, `_PRW` and dependencies;
PCI/PCIe devices also have bus-level power-management capabilities. [ACPI device power](https://uefi.org/specs/ACPI/6.6/07_Power_and_Performance_Mgmt.html)

**PROPOSED MALRYNTH DECISION:** All drivers start in D0 with runtime PM disabled. Opt-in
requires quiesce, save/restore, DMA revocation, interrupt masking, legal transition sequence,
bounded timeout, reset/recovery and wake-source tests. Storage/console stay powered until an
independent recovery path exists.

**INFERENCE:** S3 is a whole-system checkpoint/restore test: CPUs, APICs, timers, IOMMU, PCI,
storage, framebuffer and AML events must resume in a defined order. Writing the final sleep
register before those contracts exist creates a one-way power transition, not suspend.

**PROPOSED MALRYNTH DECISION:** Inventory `_S3`, `_S4`, FADT flags and low-power-idle
descriptions from day one, but expose no suspend command until secondary-CPU park/resume,
resume page tables/vector, timer correction, interrupt/IOMMU/device restore, wake attribution,
failure recovery and 100-cycle stress all pass. S4 additionally waits for a versioned,
authenticated hibernation-image design.

## Observability and acceptance

Expose a structured snapshot:

```text
power.system: s0=true s5=tested s3=described/disabled s4=described/disabled
power.cpu0: idle=C1 perf=hwp|cppc|pss|firmware thermal=ok
power.event: sci=<gsi> power_button=fixed|device masked_gpe=<count>
power.last_transition: kind=reset method=fadt result=success duration_us=...
```

Record idle entries/time, rejected state descriptions, SCI/GPE/storm counters, performance
requests, thermal events, transition attempts and last failure. Persist the final marker in
serial capture; TPM/UEFI-variable persistence needs a separate wear/security policy.

| Capability | Physical pass criterion |
|---|---|
| C1 | All CPUs survive 10 million randomized wakeups; idle residency rises when quiescent. |
| S5 | 25 shell and 25 power-button cycles fully leave S0 and cold-boot cleanly. |
| Reset | 25 cycles identify the selected path without firmware recovery or lost settings. |
| Power button | One short press yields one event; storms are maskable; long-press override remains usable. |
| Performance | Requests remain in discovered bounds under stress; time and scheduler fairness remain valid. |
| Thermal | Firmware cooling stays active; software event tests and actual throttling are distinguishable. |
| Negative AML | Timeout/error aborts before irreversible register write and returns a typed failure. |
| Cross-vendor | Intel and AMD expose the same policy/state contract through different backends. |

## Recommended integration

Adopt only the R0 idle/shutdown/reboot acceptance gates and typed power-policy boundary after platform review. Keep S3/S4, advanced performance policy, and all laptop battery/EC/thermal-profile work outside R0.

## Source ledger contributions

| Authority | Accessed | Claim contributed | URL | Licensing relevance |
|---|---|---|---|---|
| UEFI Forum | 2026-08-19 | ACPI system/device/CPU/performance states, events and sleep methods/registers | https://uefi.org/specs/ACPI/6.6/ | Specification terms; no code copied |
| UEFI Forum | 2026-08-19 | UEFI runtime reset service | https://uefi.org/specs/UEFI/2.11/ | Specification terms; no code copied |
| Intel | 2026-08-19 | i5-10500TE idle, SpeedStep and thermal capability facts | https://www.intel.com/content/www/us/en/products/sku/203891/intel-core-i510500te-processor-12m-cache-up-to-3-70-ghz/specifications.html | Product facts only |
| Intel | 2026-08-19 | Architectural idle, thermal, P-state and HWP programming | https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html | Documentation terms; no code copied |
| AMD | 2026-08-19 | AMD system/performance programming model | https://docs.amd.com/v/u/en-US/24593_3.44_APM_Vol2 | Specification agreement; no code copied |
| Linux kernel project | 2026-08-19 | Working amd-pstate/CPPC behavior | https://docs.kernel.org/admin-guide/pm/amd-pstate.html | GPL-2.0-family ecosystem; evidence only |
| Linux kernel project | 2026-08-19 | Working Intel pstate/HWP behavior | https://docs.kernel.org/admin-guide/pm/intel_pstate.html | GPL-2.0-family ecosystem; evidence only |
| MSI / ASUS | 2026-08-19 | Reference-board ACPI/monitoring/firmware facts; reviewed MSI English manual dated 2023-01-31 | https://ipc.msi.com/product_download/Industrial-Motherboard/ATX/MS-98N9 | Manual/product facts only |
| OSDev community | 2026-08-19 | Warning against partial hard-coded ACPI shutdown | https://wiki.osdev.org/Shutdown | Community evidence; no code copied |
