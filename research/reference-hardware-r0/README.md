# Malrynth reference hardware R0 research

Status: research proposal, not architecture, implementation, procurement approval, or certification.

Accessed and last reviewed: 2026-08-19.

This directory evaluates a controlled physical x86-64 engineering target for moving Malrynth beyond QEMU. It does not claim that any listed device is currently supported. `R0 supported` is an eventual test result, not a property inferred from a Linux driver or a datasheet.

## Executive result

The proposed primary family is **INTEL-FIRST**: a non-`F`, homogeneous 10th-generation Core i5 desktop/embedded CPU with UHD 630 on Q470/Q470E. The strongest investigated first specimen is MSI MS-98N9 Q470E because its manual explicitly documents a 16550A UART, I210-AT plus I219LM Ethernet, M.2 NVMe, chipset USB, debug headers, and AMI UEFI. ASUS Q470EI-IM-A is a compact alternative after exact UART qualification. Coffee Lake/Q370 remains the used-market acquisition fallback, not a second support claim.

The fallback family is AMD AM4 B550 with a Ryzen 5 5600G/PRO 5650G-class APU. ASUS Pro B550M-C/CSM is the preferred investigated business-board example: AMI UEFI, current vendor firmware support, APU display output, COM and LPC debug headers, onboard TPM 2.0, NVMe and conventional expansion. Its onboard RTL8111H is not the preferred first-driver target; add an Intel I210/I211/I350 PCIe NIC and qualify the exact physical USB-port topology. ASRock B550M Pro4 remains a lower-cost candidate if its downstream ASMedia hub is kept outside first xHCI tests.

Initial graphics means firmware GOP framebuffer only. Native acceleration is not an R0 gate. The R0 *platform* order is **Intel, AMD, NVIDIA** because Intel supplies display without an added device. The future committed *native-acceleration* order is **AMD, Intel, NVIDIA** because AMD has the strongest broad open implementation seams; NVIDIA remains firmware/vendor-stack dependent. See [GPU-FEASIBILITY.md](GPU-FEASIBILITY.md).

## Evidence vocabulary

- **OFFICIAL FACT**: stated in a standards body or vendor document.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE**: demonstrated by a maintained source tree; this proves feasibility clues, not Malrynth compatibility.
- **COMMUNITY EVIDENCE**: a lead or observed quirk that still needs controlled reproduction.
- **INFERENCE**: a conclusion drawn from the preceding evidence.
- **PROPOSED MALRYNTH DECISION**: a recommendation for later founder/architecture review.

Every decision document uses these labels where the distinction matters. [SOURCES.md](SOURCES.md) maps major claims to sources, authority, access date, and code-license relevance.

## R0 support profile

A machine is eventually `MALRYNTH REFERENCE R0 supported` only when a recorded hardware revision and firmware version passes all of the following:

1. UEFI removable-media boot reaches Malrynth Boot and transfers control to the kernel.
2. Serial diagnostics and the GOP framebuffer both remain usable after `ExitBootServices`.
3. The UEFI memory map and ACPI RSDP/XSDT are validated; MADT and MCFG are parsed.
4. All intended logical CPUs start; a stable timer and local/APIC interrupts work.
5. DMAR or IVRS is discovered and its scopes are recorded. Translation need not be the earliest gate, but incorrect or missing discovery fails the profile.
6. PCI/PCIe enumeration is stable across cold and warm boot.
7. One specified NVMe namespace works through reset, identify, read, write, and error paths.
8. One specified xHCI controller enumerates a wired USB keyboard and mouse, including through one tested USB 2 hub.
9. One specified wired Ethernet controller sends and receives sustained traffic and recovers from link changes.
10. Shutdown and reboot work repeatedly without relying on a Linux host.

GPU acceleration, Wi-Fi, Bluetooth, suspend, motherboard analog audio, camera, and TPM-backed policy are explicitly outside the first R0 pass.

## Reading map

- Platform choice and bill of materials: [REFERENCE-R0-RECOMMENDATION.md](REFERENCE-R0-RECOMMENDATION.md), [CPU-PLATFORM-ANALYSIS.md](CPU-PLATFORM-ANALYSIS.md)
- Driver feasibility: [GPU-FEASIBILITY.md](GPU-FEASIBILITY.md), [STORAGE-NVME.md](STORAGE-NVME.md), [USB-XHCI.md](USB-XHCI.md), [NETWORK-ETHERNET.md](NETWORK-ETHERNET.md)
- Peripheral staging: [INPUT-HID.md](INPUT-HID.md), [WIFI-BLUETOOTH.md](WIFI-BLUETOOTH.md), [AUDIO.md](AUDIO.md)
- Platform plumbing: [IOMMU.md](IOMMU.md), [FIRMWARE-ACPI.md](FIRMWARE-ACPI.md), [POWER-MANAGEMENT.md](POWER-MANAGEMENT.md), [DEBUGGING.md](DEBUGGING.md)
- Execution strategy: [DRIVER-PORTING-STRATEGY.md](DRIVER-PORTING-STRATEGY.md), [LINUX-DRIVER-DOMAIN.md](LINUX-DRIVER-DOMAIN.md), [DRIVER-DIFFICULTY-MATRIX.md](DRIVER-DIFFICULTY-MATRIX.md)
- Governance: [HARDWARE-RISK-REGISTER.md](HARDWARE-RISK-REGISTER.md), [PIVOT-CRITERIA.md](PIVOT-CRITERIA.md), [PHYSICAL-MILESTONE-PROPOSAL.md](PHYSICAL-MILESTONE-PROPOSAL.md)
- Data and sourcing: [HARDWARE-DATABASE-SCHEMA.md](HARDWARE-DATABASE-SCHEMA.md), [INVESTIGATED-HARDWARE.json](INVESTIGATED-HARDWARE.json), [SOURCES.md](SOURCES.md)

## Current-machine inventory

Read-only inventory was collected without elevation, firmware changes, driver changes, or direct-device experiments.

| Area | Observed hardware/state |
|---|---|
| System | Acer Nitro AN515-52; Insyde UEFI V1.24 dated 2018-12-05; Secure Boot disabled |
| CPU | Intel Core i7-8750H, 6 cores/12 threads; x2APIC, invariant/nonstop TSC and VT-x reported |
| Graphics | Intel UHD 630 (`8086:3e9b`) plus NVIDIA GP107M GTX 1050 Ti (`10de:1c8c`) |
| USB | Intel Cannon Lake PCH xHCI (`8086:a36d`) |
| Storage | Samsung 970 EVO Plus 500 GB (`144d:a808`, subsystem `144d:a801`, firmware `2B2QEXM7`) plus Toshiba SATA disk |
| Ethernet | Realtek RTL8111/8168-family (`10ec:8168`, revision 12) |
| Wireless | Intel Wireless-AC 9560 CNVi (`8086:a370`, subsystem `8086:0034`) and USB Bluetooth (`8087:0aaa`) |
| ACPI | APIC, MCFG, FADT/FACP, HPET, DMAR, TPM2, LPIT, DBG2/DBGP, DSDT and multiple SSDTs were readable |
| IOMMU topology | Linux exposed 16 groups; NVMe was isolated, while NVIDIA VGA+HDA and Realtek card-reader+Ethernet shared their respective groups |
| Early serial | No readable `/proc/tty/driver/serial` entry; no external legacy UART was established |

**PROPOSED MALRYNTH DECISION:** retain this laptop as a later secondary compatibility target and source of investigated device IDs. Do not make it R0: hybrid graphics, a vendor embedded controller, CNVi, laptop thermal/backlight/battery AML, and mobile power behavior combine several hard classes at once.

## Boundary and integration

This worktree was based on `main` revision `7a421b4e86cdb9114bf2657536a3643c50e2558d` on branch `research/reference-hardware-r0`. Research lives only in `research/reference-hardware-r0/`. No kernel, architecture, ADR, roadmap, manifest, tool, CI, or package file is changed.

## Recommended integration

Founder/architecture review may later translate the support profile, PHYSICAL milestones, and driver priorities into project-owned documents. Nothing here should be copied as an architectural commitment without that review.
