# Physical milestone proposal

These are **integration recommendations only**. They are deliberately separate from existing M0–M7 names and do not modify the roadmap.

## PHYSICAL-0 — firmware handoff proof

### Exit criteria

- boot from USB/removable path on one exact R0-A UEFI board with CSM disabled;
- firmware/build/settings identity printed to serial;
- UEFI memory map captured and validated through `ExitBootServices` retry semantics;
- ACPI RSDP and XSDT located, checksummed, and table inventory printed;
- GOP mode/base/size/stride/pixel format recorded and a post-handoff pattern drawn;
- kernel entry and exception/panic paths produce serial output;
- 100 repeated controlled boots can be proposed later, but the milestone initially requires a preserved log set of cold and warm boots, not a fake reliability percentage;
- no Linux host kernel participates after firmware launches Malrynth.

Not required: SMP, xHCI, storage, network, GPU acceleration, AML interpreter, or IOMMU translation.

## PHYSICAL-1 — CPU, interrupts, and platform inventory

- parse MADT/MCFG/FADT and DMAR/IVRS headers/scopes;
- enumerate PCIe deterministically;
- bring all intended logical CPUs online and identify topology/features;
- local APIC/I/O APIC, timer, exception, and MSI test paths work;
- monotonic time stays sane across CPUs and idle;
- reboot and shutdown work;
- serial and GOP diagnostics survive failure paths.

## PHYSICAL-2 — first DMA devices

- DMA allocator with address limits and diagnostics;
- one NVMe controller/namespace: identify, bounded read/write/flush, reset/recovery on a disposable target;
- one xHCI direct root port, USB enumeration, wired boot keyboard and mouse;
- one Intel I210/I350: raw frames then minimal IP connectivity;
- rings/queues dumped on error; no unbounded polling.

## PHYSICAL-3 — confinement and repeatability

- IOMMU translation for at least I210 or a sacrificial DMA device;
- interrupt remapping where supported;
- intentional blocked-DMA test without host corruption;
- exact R0 support profile automated and stored with hardware/firmware record;
- second SSD vendor and one hub added without weakening first devices;
- cold/warm/reboot loops and negative tests produce reproducible artifacts.

## PHYSICAL-4 — second desktop and useful peripherals

- qualify R0-B AMD B550/AM4 against the same profile;
- USB mass storage and UAC1 audio;
- optional HDA controller/one codec path;
- begin deeper power states only with rollback/instrumentation.

## Graphics/wireless milestones

Keep these separate after PHYSICAL-3:

- **DISPLAY-0:** fixed-mode native display on one selected AMD generation, reset and GOP/serial fallback;
- **GPU-0:** memory/submit/fence/recovery plus trusted test commands;
- **VULKAN-0:** Mesa winsys/driver port and compositor proof;
- **RADIO-0:** one conventional PCIe Wi-Fi client in an enforced regulatory domain, followed by USB Bluetooth HCI/HID.

This avoids making a GPU or Wi-Fi schedule hide core physical-platform health.

## Evidence packet per milestone

- Malrynth commit/build hash
- board revision, CPU stepping/microcode, firmware version/settings hash
- serial log and framebuffer photo/capture
- UEFI memory-map and ACPI table hashes/dumps
- PCI/USB topology and IOMMU grouping
- device IDs/firmware/NVM versions
- pass/fail checklist with known quirks and recovery instructions
- destructive-test declaration and data backup for storage work

## Recommended integration

Founder/roadmap owners may adopt, rename, split, or reject these milestones. This research branch must not edit the existing roadmap.
