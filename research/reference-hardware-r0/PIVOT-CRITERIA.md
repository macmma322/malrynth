# Kill and pivot criteria

These criteria stop sunk-cost reverse engineering. Crossing a trigger pauses the affected class, preserves evidence, and requires an explicit alternative decision. It does not stop unrelated physical-hardware progress.

## GPU

### Stop focused native port when

- required initialization/display/firmware interfaces cannot be lawfully documented or redistributed for the chosen exact generation;
- the port must emulate a broad, unstable set of internal Linux APIs rather than a bounded compatibility layer;
- three consecutive upstream updates each require cross-cutting semantic rework across memory management, scheduling, display, and firmware glue;
- reliable GPU reset/hang recovery cannot be demonstrated without rebooting or corrupting host memory;
- untrusted command submission cannot be confined by GPU VM plus IOMMU;
- the chosen board loses GOP/serial recovery when the native driver fails.

### Pivot to

1. a narrower/older AMD generation with a stable firmware/code base;
2. display-only driver plus software rendering;
3. Mesa/Vulkan work on virtio-gpu before physical acceleration;
4. secondary-GPU Linux domain for compute only;
5. vendor engagement. Never pivot primary boot/display to an opaque domain silently.

## NVIDIA

Stop before implementation if the selected GPU requires version-locked GSP/user components that cannot be distributed or invoked on Malrynth, or if only Linux kernel modules—not a documented host interface—are available. Reassess only after a stable GSP protocol/firmware policy and open userspace path are evidenced.

## Wi-Fi

### Stop native port when

- firmware license forbids necessary redistribution or download/bootstrap is unreliable;
- firmware/driver protocol is undocumented and maintained code cannot be legally reused;
- regulatory power/channel/DFS behavior cannot be enforced and audited;
- client WPA2/WPA3 requires inventing a device-specific security path outside a reviewed supplicant boundary;
- adapter is CNVi/platform-coupled when a replaceable PCIe alternative exists;
- crash/reset leaves the radio or DMA active beyond host control.

### Pivot to

wired Ethernet, another conventional PCIe adapter family, or an IOMMU-confined Linux domain exporting virtio-net. Do not transmit in an unknown regulatory state.

## Bluetooth

Stop a controller family if firmware transport/redistribution is blocked or reset is unreliable. Keep HCI and host stack work transport-neutral and switch USB dongle/controller. Stop audio-profile work if codecs/timing/policy swamp basic HID/GATT goals; preserve BT HID only.

## NVMe/storage

Stop qualifying a drive/firmware when it violates required standard behavior, needs vendor utilities for ordinary operation, changes controller identity within the same supply SKU without traceability, or cannot recover from controller reset. Switch to the known-good second vendor. Do not add vendor commands to rescue an R0 drive.

Stop native NVMe scope expansion if advanced features threaten basic flush/read/write recovery. Freeze the minimal subset. Do not pivot root storage into a Linux domain.

## xHCI/USB

Stop a board/controller path if firmware ownership cannot be released, the port depends on an undocumented vendor controller, or reset wedges the platform. Switch to direct chipset ports or another board. Stop a peripheral class/device if malformed descriptors require an open-ended quirk engine; select a class-compliant replacement.

## Ethernet

Stop an adapter if NVM/PHY initialization is not described by public Intel material/permissive reference code, authenticity is doubtful, or DMA cannot be stopped/reset. Switch to a verified I210/I350 adapter. Do not implement Realtek first merely because it is onboard.

## IOMMU/driver domains

Stop isolation claims on a board if DMAR/IVRS omits a bus master, groups bind the target to host-critical devices, interrupt remapping is absent for the threat model, or device reset is not contained. Keep that driver trusted/in-kernel or switch slot/board.

Stop a Linux domain if it becomes necessary for root storage, serial/panic output, basic input, or first wired recovery networking; if its shared protocol is more complex than the native driver; or if updates cannot be reproduced. Remove the device from the supported profile or fund native work.

## Laptop

Reject a laptop reference when basic display, thermals, keyboard/touchpad, battery, or suspend requires undocumented vendor ACPI/EC behavior or a proprietary daemon with no stable interface. It may remain a boot-only test target; it is not certified.

## Firmware and motherboard

Reject an exact revision if it lacks public firmware recovery, cannot disable RAID/VMD for plain NVMe, cannot expose GOP without CSM, cannot enable IOMMU, has no reliable serial/alternative early debug, or changes key onboard controllers without a distinct revision. Change boards rather than adding global quirks before first support.

## Power

Disable a deeper idle/D-state/ASPM/suspend feature when it causes an unrecoverable hang, silent data loss, missed timer/interrupt, or a failure that cannot be diagnosed through serial on three controlled reproductions. Ship the shallower state and reopen only with instrumentation and a narrower hypothesis.

## Vendor cooperation

Seek vendor help when public evidence ends, but time-box the dependency to the next milestone review. If no usable documentation/redistribution/debug channel exists at that gate, select different hardware or narrow the feature. Product independence cannot rest on an unanswered support request.

## Evidence preservation on pivot

Record exact IDs/firmware, logs, failing test, last good revision, suspected dependency, license finding, and the reason for stopping. Mark the database record `blocked`/`rejected` with scope; never delete failed evidence or represent a pivot as support.

## Recommended integration

Later project governance may adopt these as review gates. They should not be converted into dates or numeric effort promises.
