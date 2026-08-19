# Sources

Access date for every web source: **2026-08-19**. Each row maps an authority to the conclusion it supports. Product pages and specifications are factual design references, not source-code licenses. “Licensing relevance” is an engineering flag, not legal advice; any implementation reuse still needs an exact-file and exact-version review.

## Local inventory

| Source / authority | Relevant claim | URL / reference | Licensing relevance |
|---|---|---|---|
| Local Linux read-only inventory | Acer Nitro AN515-52 identity; i7-8750H; Intel UHD 630 `8086:3e9b`; NVIDIA GP107M `10de:1c8c`; Intel xHCI `8086:a36d`; Intel CNVi `8086:a370`; Samsung NVMe `144d:a808`; Realtek Ethernet `10ec:8168`; Intel USB Bluetooth `8087:0aaa`; UEFI variables and IOMMU groups visible | Commands run without `sudo`: `lscpu`, `lspci -nn`, `lsusb`, `lsblk`, `ip -brief link`; readable `/sys/class/dmi/id`, `/sys/class/drm`, `/sys/kernel/iommu_groups`, `/sys/firmware/efi`, and `/proc/cmdline`. Unprivileged `dmidecode` was denied. | Local observations only; serial numbers, MAC addresses and storage UUIDs are intentionally omitted. This is not a Malrynth driver test. |

## Architecture, firmware, IOMMU and security

| Source / authority | Relevant claim | URL / reference | Licensing relevance |
|---|---|---|---|
| Intel — Intel 64 and IA-32 SDM | x86-64 system programming, APIC/x2APIC, SMP, TSC/timers, VMX, MSRs and power mechanisms | [Intel SDM](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) | Proprietary documentation; implement from the architecture, no code copied. |
| AMD — AMD64 Architecture Programmer's Manual | AMD64 system programming, interrupt, time and SVM model | [AMD APM](https://docs.amd.com/v/u/en-US/40332_4.09_APM_PUB) | AMD Public Use document; reference under its terms. |
| UEFI Forum — UEFI 2.11 | GOP framebuffer metadata and the `ExitBootServices` lifetime boundary | [UEFI 2.11](https://uefi.org/specs/UEFI/2.11/) | UEFI Forum specification/adopter terms apply. |
| UEFI Forum — ACPI 6.6 | RSDP/XSDT, MADT, MCFG, FADT, HPET, DMAR/IVRS-related discovery, AML and sleep/reset interfaces | [ACPI 6.6](https://uefi.org/specs/ACPI/6.6/) | UEFI Forum specification/adopter terms apply. |
| PCI-SIG | PCI Express configuration/capability model and firmware interaction references | [PCIe specifications overview](https://pcisig.com/specification-overview/pci-express-base), [PCI firmware](https://pcisig.com/specification-overview/pci-firmware) | PCI-SIG access/adopter terms apply; no specification text copied. |
| Intel — VT-d Architecture Specification | DMA translation, invalidation, reserved regions and interrupt remapping | [Intel VT-d](https://www.intel.com/content/www/us/en/content-details/868911/intel-virtualization-technology-for-directed-i-o-architecture-specification.html) | Architectural reference only. |
| AMD — I/O Virtualization Technology Specification | AMD IOMMU programming and IVRS interpretation | [AMD IOMMU specification](https://www.amd.com/content/dam/amd/en/documents/processor-tech-docs/specifications/48882_IOMMU.pdf) | AMD Public Use document; no code copied. |
| Trusted Computing Group | TPM 2.0 commands/data and PC-client platform profile for future measured boot/sealing | [TPM 2.0 Library](https://trustedcomputinggroup.org/resource/tpm-library-specification/), [PC Client PTP](https://trustedcomputinggroup.org/resource/pc-client-platform-tpm-profile-ptp-specification/) | TCG specification terms apply; R0 boot does not depend on TPM. |
| uACPI project | Small OS-agnostic ACPI/AML implementation surface and MIT licensing | [uACPI](https://github.com/uACPI/uACPI) | MIT repository; exact revision/files and notices still require review. |
| Intel ACPICA project | Mature OS-independent ACPI implementation and compatibility oracle | [ACPICA](https://github.com/acpica/acpica), [Intel ACPICA downloads](https://www.intel.com/content/www/us/en/developer/topic-technology/open/acpica/download.html) | Dual-license/per-file review required before integration. |

## CPU and motherboard candidates

| Source / authority | Relevant claim | URL / reference | Licensing relevance |
|---|---|---|---|
| Intel — Core i5-9500 | Six homogeneous cores, 65 W, UHD 630 and VT-d; discontinued lifecycle | [i5-9500 specifications](https://www.intel.com/content/www/us/en/products/sku/134895/intel-core-i59500-processor-9m-cache-up-to-4-40-ghz/specifications.html) | Product facts only. |
| Intel — Core i5-8500 | Same-shape six-core/UHD 630/VT-d fallback | [i5-8500 specifications](https://www.intel.com/content/www/us/en/products/sku/129939/intel-core-i58500-processor-9m-cache-up-to-4-10-ghz/specifications.html) | Product facts only. |
| Intel — Q370 | PCIe 3.0, chipset USB/SATA, VT-d and PTT features | [Q370 specifications](https://www.intel.com/content/www/us/en/products/sku/133282/intel-q370-chipset/specifications.html), [300-series PCH datasheet](https://www.intel.com/content/www/us/en/content-details/337867/intel-300-series-chipset-family-pch-datasheet-vol-1.html) | Product/datasheet facts; board firmware must still be tested. |
| ASUS — PRIME Q370M-C/CSM | Q370, I219-LM, dual M.2, two COM headers, LPC debug, onboard TPM and AMI UEFI/ACPI 6.1 | [Manual](https://dlcdnets.asus.com/pub/ASUS/mb/LGA1151/PRIME_Q370M-C/E14162_PRIME_Q370M-C_UM_WEB.pdf), [specifications](https://www.asus.com/us/motherboards-components/motherboards/prime/prime-q370m-c-csm/techspec/) | Copyrighted vendor material; facts only. The UART electrical/programming model still needs specimen validation. |
| AMD — Ryzen 5 5600G | Six Zen 3 cores/twelve threads, 65 W, PCIe 3.0 and integrated Radeon graphics | [5600G specifications](https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-5000-series/amd-ryzen-5-5600g.html) | Product facts only. |
| AMD — AM4/B550 | Ryzen 5000/B550 platform compatibility | [AMD AM4 chipsets](https://www.amd.com/en/products/processors/chipsets/am4.html) | Product facts only. |
| ASUS — Pro B550M-C/CSM | B550, M.2, COM/LPC debug, onboard TPM 2.0, Realtek RTL8111H and AMI UEFI | [Specifications](https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/), [firmware support](https://www.asus.com/us/motherboards-components/motherboards/csm/pro-b550m-c-csm/helpdesk_bios?model2Name=Pro-B550M-C-CSM) | Copyrighted vendor facts/firmware; redistribution is not implied. |
| MSI — PRO B550M-P | Alternative B550 board with COM, TPM header and debug LEDs | [MSI specifications](https://www.msi.com/Motherboard/PRO-B550M-P/Specification) | Product facts only. |

## Graphics

| Source / authority | Relevant claim | URL / reference | Licensing relevance |
|---|---|---|---|
| Intel — Coffee Lake graphics PRM | Target-specific public programming documentation for UHD 630 generation | [Coffee Lake graphics documentation](https://www.intel.com/content/www/us/en/docs/graphics-for-linux/developer-reference/1-0/coffee-lake.html) | Documentation availability does not license a driver or firmware. |
| Linux kernel documentation | DRM/KMS, GEM/TTM, scheduler and i915 firmware/power dependencies demonstrate the kernel-side port surface | [DRM KMS](https://docs.kernel.org/gpu/drm-kms.html), [DRM memory management](https://docs.kernel.org/gpu/drm-mm.html), [i915](https://docs.kernel.org/gpu/i915.html) | Linux is GPL-2.0-only as a whole; exact-file SPDX review required. |
| Haiku source | Native non-Linux `intel_extreme` table contains Coffee Lake device IDs | [Haiku intel_extreme](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/drivers/graphics/intel_extreme/driver.cpp#L173-L183) | Haiku is MIT-oriented; preserve per-file notices and audit dependencies. |
| Mesa — ANV | Intel Vulkan userspace dependencies; documented GuC boundary begins after the proposed Coffee Lake generation | [ANV](https://docs.mesa3d.org/drivers/anv.html) | Mesa is mostly MIT; per-file/dependency review required. |
| Linux AMDGPU documentation | AMD IP-block, PSP/SMU/DC/SDMA/GC/VCN split and Display Core boundary | [AMDGPU core](https://docs.kernel.org/gpu/amdgpu/driver-core.html), [AMD Display Core](https://docs.kernel.org/5.15/gpu/amdgpu-dc.html) | Linux/file-level GPL/SPDX review; firmware separate. |
| Mesa — RADV | Vulkan userspace driver depends on amdgpu DRM uAPI/libdrm and a winsys boundary | [RADV](https://docs.mesa3d.org/drivers/radv.html) | Mesa mostly MIT, but Linux-facing dependencies are separate artifacts. |
| AMD GPUOpen / linux-firmware | Public shader ISA material and separate Radeon firmware redistribution terms | [AMD machine-readable ISA](https://gpuopen.com/machine-readable-isa/), [Radeon firmware license](https://kernel.googlesource.com/pub/scm/linux/kernel/git/firmware/linux-firmware/+/refs/heads/main/LICENSE.radeon) | Documentation/tool and binary-firmware terms differ; preserve notices and restrictions. |
| NVIDIA | Turing+ open Linux kernel modules, OS-agnostic core/Linux interface layer, GSP and matched userspace boundary | [Open GPU kernel modules](https://github.com/NVIDIA/open-gpu-kernel-modules), [open GPU docs](https://github.com/NVIDIA/open-gpu-doc) | Kernel source has GPL/MIT portions; GSP firmware and proprietary userspace are separately licensed. |
| Mesa — NVK | Modern NVIDIA Vulkan implementation remains tied to a Linux kernel baseline | [NVK](https://docs.mesa3d.org/drivers/nvk.html) | Mesa per-file licenses; conformance does not transfer to a Malrynth port. |
| FreeBSD drm-kmod / Redox / SerenityOS | Non-Linux implementation evidence bounds what is truly native versus a LinuxKPI port or framebuffer fallback | [FreeBSD drm-kmod](https://github.com/freebsd/drm-kmod), [Redox hardware](https://github.com/redox-os/redox/blob/master/HARDWARE.md), [Serenity Intel GPU](https://github.com/SerenityOS/serenity/blob/master/Kernel/Devices/GPU/Intel/NativeGraphicsAdapter.cpp) | Mixed BSD/GPL/MIT and firmware; per-file audit required. |
| Mesa and Linux licensing documentation | Project-wide licensing baselines used in the porting analysis | [Mesa license](https://docs.mesa3d.org/license.html), [Linux licensing rules](https://docs.kernel.org/process/license-rules.html) | These are routing rules; exact source files control reuse. |

## Storage, USB, input, networking and audio

| Source / authority | Relevant claim | URL / reference | Licensing relevance |
|---|---|---|---|
| NVM Express | Controller registers, queues, namespaces, Identify, PRPs, reset and power-state contract | [NVM Express specifications](https://nvmexpress.org/specifications/) | NVM Express specification terms apply. |
| Samsung | 970 EVO Plus is M.2 2280, PCIe Gen3 x4 and NVMe 1.3 | [970 EVO Plus data sheet](https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_NVMe_SSD_970_EVO_Plus_Data_Sheet_Rev.3.0_10129514071343.pdf) | Proprietary vendor data sheet; facts only. |
| Western Digital | SN570 is a second mainstream NVMe client-family cross-check | [WD Blue SN570 data sheet](https://documents.westerndigital.com/content/dam/doc-library/en_us/assets/public/western-digital/product/internal-drives/wd-blue-nvme-ssd/data-sheet-wd-blue-sn570-nvme-ssd.pdf) | Proprietary product document; facts only. |
| Intel / USB-IF — xHCI 1.2 | xHCI capability/operational/runtime/doorbell registers, command/event/transfer rings, contexts and root ports | [xHCI 1.2](https://www.intel.com/content/dam/www/public/us/en/documents/technical-specifications/extensible-host-controler-interface-usb-xhci.pdf) | Specification/adopter terms apply; implement independently. |
| USB-IF — USB 2.0, HID and Usage Tables | Enumeration/control transfers, hubs, boot keyboard/mouse protocols and report semantics | [USB documents](https://www.usb.org/documents), [HID resources](https://www.usb.org/hid) | USB-IF adopter/document terms apply. |
| Microsoft HID Tools | MIT-licensed HID descriptor authoring/validation oracle referenced by USB-IF | [HID tools](https://github.com/microsoft/hidtools) | MIT; exact files/notices required for reuse. |
| Intel — I210 | Public external architecture/register definitions for a PCIe 1GbE controller | [I210 datasheet](https://www.intel.com/content/www/us/en/content-details/333016/intel-ethernet-controller-i210-datasheet.html), [I210-T1](https://www.intel.com/content/www/us/en/products/sku/68668/intel-ethernet-server-adapter-i210t1/specifications.html) | Documentation/product facts; adapter NVM remains part of the specimen. |
| Intel — 82574L | Documented discontinued PCIe 1GbE fallback | [82574L specifications](https://www.intel.com/content/www/us/en/products/sku/32209/intel-82574l-gigabit-ethernet-controller/specifications.html) | Product facts only. |
| FreeBSD source | Permissive implementation evidence for Intel `em`/I210-family logic | [FreeBSD if_em](https://github.com/freebsd/freebsd-src/blob/main/sys/dev/e1000/if_em.c), [FreeBSD e1000 directory](https://github.com/freebsd/freebsd-src/tree/main/sys/dev/e1000) | `if_em.c` is BSD-2-Clause; adjacent files require individual review. |
| Linux wireless documentation | Firmware/mac80211/cfg80211/regulatory dependency shape and reusable ISC regulatory database design | [Linux wireless](https://wireless.docs.kernel.org/en/latest/), [regulatory design](https://wireless.docs.kernel.org/en/latest/en/developers/regulatory.html), [wireless-regdb](https://wireless.docs.kernel.org/en/latest/en/developers/regulatory/wireless-regdb.html) | Linux driver code GPL; regulatory database is separately ISC-licensed. |
| Bluetooth SIG / USB-IF | Bluetooth Core/HCI/host/profile split and standard USB Bluetooth class tuple | [Bluetooth Core 6.3](https://www.bluetooth.com/specifications/specs/core-specification-6-3/), [USB class codes](https://usb.org/defined-class-codes) | SIG/USB adopter terms apply. |
| Intel — High Definition Audio 1.0a | HDA controller, CORB/RIRB, streams, codec widgets/verbs and DMA buffer descriptors | [Intel HDA specification](https://www.intel.la/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf) | Specification reference; no source license. |
| USB-IF — Audio Device Class | Current UAC documents and the basis for a bounded UAC1-first implementation | [USB Audio documents](https://www.usb.org/documents?search=audio) | USB-IF document/adopter terms apply. |

## Porting, virtualization and driver-domain evidence

| Source / authority | Relevant claim | URL / reference | Licensing relevance |
|---|---|---|---|
| Linux kernel — VFIO | IOMMU groups, DMA mapping and interrupt delivery are necessary for isolated direct device access | [VFIO documentation](https://docs.kernel.org/driver-api/vfio.html) | Implementation evidence under Linux GPL terms; not a Malrynth API proposal. |
| OASIS — Virtio 1.3 | Stable virtual-device queues/transports and explicitly described shared-memory regions | [Virtio 1.3](https://docs.oasis-open.org/virtio/virtio/v1.3/virtio-v1.3.html) | OASIS specification terms apply. |
| QEMU — ivshmem | Shared memory and notifications can connect isolated VM peers, but lifecycle/backend work remains | [QEMU ivshmem](https://www.qemu.org/docs/master/system/devices/ivshmem.html) | QEMU is GPLv2 with component-specific licenses. |
| QEMU — device models | Repeatable e1000/e1000e, NVMe, xHCI, virtio and failure-path test oracles | [QEMU device emulation](https://www.qemu.org/docs/master/system/device-emulation.html) | GPLv2; use as an external test oracle unless code licensing is explicitly accepted. |
| FreeBSD Project | BSD-2-Clause is preferred for new FreeBSD source but the tree includes other licenses | [FreeBSD licensing policy](https://docs.freebsd.org/en/articles/license-guide/) | Project-level policy does not replace per-file review. |
| Redox OS | Non-Linux user-space/native driver architecture and implementation evidence | [Redox drivers](https://github.com/redox-os/drivers) | Repository is MIT-oriented; audit exact files and archived/current status. |

## Evidence policy

- **OFFICIAL FACT** rows support standards, product and vendor-interface claims.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** shows feasibility and dependency shape; it does not mean code can compile on Malrynth or be reused under any desired license.
- **COMMUNITY EVIDENCE** appears only where an official/non-Linux record is absent and is not sufficient for a support claim.
- Firmware is inventoried independently from driver source: acquisition, version, hash, signature, redistribution, loader ABI and update method are separate fields.
- Hardware support requires an exact Malrynth test record. Documentation and Linux inventory alone never produce `r0-supported` status.
