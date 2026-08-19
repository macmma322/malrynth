# Reference R0 recommendation

## Decision summary

**PROPOSED MALRYNTH DECISION: INTEL-FIRST for the controlled base platform.** Select a non-`F`, homogeneous Coffee Lake-S Core i5 on Q370. Freeze one exact commercial motherboard and firmware revision as the physical oracle. Keep graphics at UEFI GOP framebuffer through the first physical milestones, add an Intel I210/I211/I350 PCIe NIC even when the board exposes I219, and use one plain M.2 NVMe device plus direct chipset USB ports.

The concrete first specimen is an ASUS PRIME Q370M-C/CSM with Core i5-9500, with i5-8500 as a same-shape substitute. This is a qualification target, not generic Q370 support. A newer Q470E industrial board is a technically attractive alternative if it can be sourced cheaply; cost and replacement availability are part of R0 feasibility.

The graphics recommendation is deliberately narrower than a general vendor-openness judgment. For this exact R0 the order is Intel, AMD, NVIDIA because Coffee Lake has unusually useful public Gen9 material and non-Linux driver evidence. AMD remains the strongest broad long-term open driver research base, but acceleration is not an R0 gate.

## Why this family

**OFFICIAL FACT:** Intel publishes the Intel 64 system-programming manuals and VT-d architecture specification. The i5-9500 is a homogeneous six-core processor with UHD 630, VT-x/EPT, and VT-d. Q370 exposes VT-d and PTT capabilities. ASUS documents the candidate board's AMI UEFI/ACPI 6.1, two COM headers, LPC debug header, onboard TPM 2.0, dual M.2 storage, and I219-LM Ethernet.

**INFERENCE:** the combination supplies the physical interfaces Malrynth needs without hybrid cores, a discrete boot GPU, a laptop embedded controller, or an enthusiast-board peripheral mix. Its chief risk is lifecycle: CPU and chipset are discontinued, so the exact specimen will probably be used or new-old-stock.

## R0-A: primary configuration

| Part | Requirement | Candidate / qualification notes |
|---|---|---|
| CPU | 8th/9th-gen non-`F` Core i5; six homogeneous cores; UHD 630; VT-x and VT-d | i5-9500 primary, i5-8500 substitute; exclude `F` parts because they remove the iGPU |
| Board | Q370 commercial mATX; UEFI; documented COM/debug/TPM; usable PCIe slot | ASUS PRIME Q370M-C/CSM is the exact first candidate, not a family-wide support claim |
| GPU/display | Intel UHD 630 GOP only at first | Firmware must expose a linear framebuffer that remains reserved and writable after `ExitBootServices`; no i915/ANV dependency for R0 |
| RAM | 16–32 GiB JEDEC DDR4, two matching non-overclocked DIMMs | Disable XMP; record module part numbers and slot population |
| NVMe | M.2 2280 PCIe 3.0 x4, NVMe 1.3+; initially one namespace | Owned Samsung 970 EVO Plus is the first device; WD Blue SN570 supplies a second client implementation later |
| Ethernet | Discrete Intel I210/I211 or I350 PCIe adapter with valid NVM | The onboard I219-LM remains investigated but is not the first native NIC contract; verify PCI subsystem ID and card authenticity |
| USB | Direct Q370 xHCI port, initially with plain USB 2 keyboard/mouse | Avoid front-panel hubs, Type-C policy, RGB devices, wireless receivers, and KVMs during bring-up |
| Input | Wired USB boot-protocol keyboard and mouse | PS/2 is optional diagnostic fallback, not a required driver |
| Audio | External USB Audio Class 1 device later | Audio is not an R0 boot gate; motherboard HDA follows UAC1 |
| TPM | Onboard TPM 2.0 and Q370 PTT capability may be inventoried | Boot must not depend on TPM; never clear/take ownership during bring-up |
| Debug | Correct board-pinout COM-to-DE-9 bracket, independent RS-232 capture host, GOP, speaker/LPC POST aid | Qualify electrical levels, UART resources, cable wiring, and loopback before treating serial as authoritative |

### Board alternatives inside the Intel-first strategy

| Candidate | Evidence in its favor | Qualification risk |
|---|---|---|
| ASUS PRIME Q370M-C/CSM | Commercial mATX; two COM headers; LPC debug and speaker; onboard TPM 2.0; two M.2 sockets; AMI UEFI/ACPI 6.1; likely used-market availability | Onboard NIC is I219-LM; Super I/O identity/16550 compatibility is not explicit in the reviewed manual; needs add-in I210-class NIC and UART validation |
| Supermicro X11SCQ | Q370; NCT6776D 16550-compatible UARTs; I210-AT plus I219LM; VT-d/DMAR control; M.2 and multiple COM ports | Used/industrial availability and price; exact firmware still needs qualification |
| MSI MS-98N9 Q470E variant | Newer 10th-gen homogeneous Core; I210-AT plus I219LM; chipset USB; M.2; rear/header COM; documented 16550A UART | Large industrial ATX board; price/availability unknown; M.2 shares named PCIe resources |
| ASUS Q470EI-IM-A | Q470E Mini-ITX; I210-AT plus I219LM; five COM ports; M.2 NVMe; TPM; LPC debug; xHCI hand-off and VT-d controls | One physical x16 slot and SO-DIMMs; reviewed material does not explicitly establish 16550 compatibility |

The first board acquired must pass the checklist below. A cleaner industrial board is not preferable if it consumes the project's nonexistent lab budget or cannot be replaced.

### Required firmware settings

Record every setting and the exact firmware image/hash. Names vary by vendor.

- UEFI-only boot; CSM off after GOP boot is proven.
- Secure Boot off for bring-up unless a Malrynth image is deliberately enrolled.
- VT-x and VT-d on; interrupt remapping on when separately exposed.
- Above-4G decoding and Resizable BAR off for the smallest initial map; test later.
- SATA in AHCI mode, not RAID/RST/VMD; expose NVMe directly.
- Onboard serial enabled with fixed resources where firmware permits.
- iGPU primary with a fixed modest aperture if configurable.
- XMP, CPU overclocking, undervolting, vendor auto-overclocking, and fast boot off.
- Firmware USB keyboard support may serve setup screens; Malrynth must take native xHCI ownership.
- TPM may remain enabled for discovery, but boot must also succeed with it disabled.

## R0-B: AMD cross-vendor fallback

| Part | Requirement | Candidate / caveat |
|---|---|---|
| CPU | AMD AM4 Zen 3 APU, homogeneous cores, integrated Radeon GOP | Ryzen 5 5600G; Ryzen 5 PRO 5650G is acceptable after exact board support is verified |
| Board | B550 business mATX; documented UEFI, COM/debug path, TPM and ordinary expansion | ASUS Pro B550M-C/CSM preferred; MSI PRO B550M-P is lower-observability fallback; ASRock B550M Pro4 is a low-cost USB-topology test candidate |
| NIC | Add-in Intel I210/I211/I350 | Do not make the onboard RTL8111H the first Ethernet implementation |
| USB | Direct AMD chipset/CPU xHCI path | Map each port; avoid the ASRock board's documented downstream ASM1074 hub for initial tests |
| Other parts | Same RAM/NVMe/input/audio/debug discipline as R0-A | COM header needs the correct voltage/pinout bracket; IVRS and isolation groups must be measured |

**OFFICIAL FACT:** the ASUS B550 business board exposes a COM header, LPC debug, onboard TPM 2.0, two M.2 sockets, AMI UEFI, and RTL8111H Ethernet. **INFERENCE:** it is the right vendor-diversity control, but not as observable as the two-UART Q370 candidate and not a reason to implement Realtek Ethernet first.

## Qualification checklist

Reject or defer a board if its manual, block diagram, or read-only inventory cannot answer these questions:

1. Does UEFI boot removable x86-64 media with CSM disabled and preserve a usable GOP buffer?
2. Is VT-d/AMD IOMMU selectable, and do DMAR/IVRS tables validate on the exact firmware?
3. Which USB ports are direct root ports, and which traverse hubs or auxiliary controllers?
4. What exact Ethernet PCI VID:DID/subsystem identity is present?
5. Which UART/Super I/O supplies COM, what are its resources, and what electrical bracket is required?
6. Is M.2 direct PCIe/NVMe rather than VMD/RAID remapping?
7. Are firmware images, release notes, recovery instructions, and a full manual archived?
8. Can the reference NIC and a later GPU coexist in the usable slots?
9. Are speaker, POST/debug indication, clear-CMOS, and firmware recovery accessible?
10. What exact board revision, firmware hash, CPU stepping, and microcode revision passed?

## Engineering support tiers

- **R0 — controlled desktop:** exact Q370/Intel specimen; GOP, serial, ACPI basics, SMP/timer, PCI, IOMMU discovery, NVMe, xHCI/HID, and I210-class Ethernet.
- **R1 — second desktop platform:** qualify AMD B550/AM4; enable IOMMU translation/DMA confinement; add USB mass storage and USB Audio Class.
- **R2 — graphics expansion:** one fixed Intel UHD 630 native-display experiment, then one selected AMD family for broader port/acceleration research; retain GOP recovery.
- **R3 — wireless peripherals:** one replaceable conventional PCIe Intel Wi-Fi family plus USB Bluetooth transport; Wi-Fi client mode and BT HID precede audio profiles.
- **R4 — first laptop reference:** a deliberately selected business laptop with one GPU, replaceable Wi-Fi, and no essential vendor daemon.
- **R5 — broader qualification:** multiple boards/revisions, storage/NIC diversity, suspend/resume, performance, failure recovery, and a future certification process.

No tier is a date or promise. `REFERENCE R0 supported` is an engineering profile; it is not `MALRYNTH CERTIFIED`.

## Cost policy

Start with QEMU and owned parts. The existing Samsung NVMe, wired USB devices, and laptop can exercise discovery and negative cases without making the laptop R0. If procurement becomes possible, seek one complete used Q370 business system or board/CPU/RAM bundle, one verified I210/I350 adapter, and the correct serial bracket/cable. Do not buy a discrete GPU or a hardware lab for PHYSICAL-0/1. If Q370 cannot be sourced responsibly, reassess Q470E industrial inventory and the B550 fallback rather than relaxing observability.

## Recommended integration

Adopt the property checklist and test-scoped `R0 supported` profile only after founder review. Keep retail SKUs out of architecture; store exact tested board, firmware, PCI identities, settings, and artifacts in the future hardware database.
