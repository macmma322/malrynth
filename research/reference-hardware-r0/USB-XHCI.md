# USB: xHCI-first strategy

## Evidence labels

- **OFFICIAL FACT** — standards-body/vendor material.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — upstream code or model evidence, subject to its license.
- **COMMUNITY EVIDENCE** — field reports useful for triage, not qualification.
- **INFERENCE** — engineering conclusion from the evidence.
- **PROPOSED MALRYNTH DECISION** — recommended project policy.

## Decision

**PROPOSED MALRYNTH DECISION:** implement one standards-conforming PCI xHCI host controller, then hubs and USB HID. Do not implement EHCI/UHCI/OHCI for R0. Select physical ports routed to the chipset xHCI function, without Type-C policy or an auxiliary ASMedia controller in the first test.

**OFFICIAL FACT:** the xHCI specification defines the register-level host-controller interface for all USB speeds and is intended for device-driver developers; Intel currently publishes revisions 1.2c and 2.0 ([Intel USB/xHCI specifications](https://www.intel.com/content/www/us/en/products/docs/io/universal-serial-bus/universal-serial-bus-specifications.html)). It unifies the host-controller programming model but does not replace USB enumeration or class drivers.

## Controller ranking

| Rank | Controller family | Evidence-backed role |
|---:|---|---|
| 1 | QEMU `qemu-xhci`, `1b36:000d` | Deterministic R0 oracle; QEMU allocates this exact VID:DID for its PCI xHCI model ([QEMU PCI IDs](https://www.qemu.org/docs/master/specs/pci-ids.html)). |
| 2 | Intel/AMD integrated chipset xHCI | First physical target because it avoids an add-in bridge and is the normal root controller; qualify the exact board/ports, not a broad vendor allowlist. |
| 3 | Renesas µPD720202 | Useful discrete cross-check; vendor states PCIe Gen2 x1, two all-speed ports and xHCI 1.0 compliance ([Renesas µPD720202](https://www.renesas.com/en/products/upd720202)). |
| 4 | ASMedia ASM3142 | Later discrete cross-check; vendor states PCIe-to-USB 3.1 Gen2 and xHCI 1.1 compliance ([ASMedia ASM3142](https://www.asmedia.com.tw/product/55AYQ83xg4uy6Uj0/0C8YQ4asx4yt2JR4.html)). |

**INFERENCE:** class compliance supports a common core, but controller revisions still need bounded quirks. Do not copy community PCI IDs for physical controllers into the support matrix; record IDs from owned hardware and require a vendor manual or accepted upstream match before claiming them.

## Dependency map

### Controller discovery

- PCI class `0c:03:30`, BAR mapping, PCI command, MSI/MSI-X
- capability length/version, structural parameters, doorbell/runtime offsets
- Extended Capabilities walk with loop/bounds protection
- BIOS/OS ownership handoff when the legacy-support capability is present
- supported-protocol capabilities to map physical ports and speeds

### Memory and DMA

- page-aligned Device Context Base Address Array
- scratchpad array/buffers if advertised
- command ring with link TRBs and cycle-state tracking
- one or more event rings plus ERST
- per-device input/output contexts and endpoint transfer rings
- 64-bit DMA-address support validation; no pointer truncation
- correct producer/consumer barriers before doorbells and after events

### Controller operation

1. Halt and reset with bounded timeouts; honor controller-not-ready.
2. Set maximum device slots conservatively.
3. Install DCBAA, command ring, and event-ring state.
4. Configure interrupter moderation conservatively and enable MSI/MSI-X.
5. Run, inspect port status/change bits, reset a connected port, and derive slot speed.
6. Enable Slot, Address Device using a default control endpoint, then read the first descriptor bytes and update EP0 maximum packet size as required.
7. Read full device/configuration descriptors with strict length validation.
8. Configure endpoints and submit normal/control/interrupt transfers.
9. Match transfer events by TRB pointer/event data and handle short packets, stalls, disconnects, and ring wrap.

### Enumeration and hubs

Enumeration requires standard USB requests, address/configuration state, descriptor parsing, interface/alternate-setting selection, endpoint model, and string handling. External hubs add hub descriptors, port power/reset/status, an interrupt status endpoint, depth, transaction translators for low/full-speed devices behind high-speed hubs, and recursive disconnect. A root hub is a software view over xHCI ports; it is not an ordinary USB device. **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux separates the host-controller layer from USB core/hub enumeration and represents transaction-translator state explicitly ([Linux USB host-side API](https://docs.kernel.org/driver-api/usb/usb.html)).

## Staging

### First

- one direct root port
- USB 2 low/full-speed wired keyboard
- USB 2 mouse
- control and interrupt transfers
- one simple USB 2 hub after direct devices work

### Next

- mass storage (Bulk-Only Transport first, with robust reset/recovery)
- simple standards-conforming gamepad/HID reports
- USB CDC ACM or selected FTDI serial only after the serial console no longer depends on it
- USB Audio Class 1 playback/capture

### Later

- webcams/UVC and isochronous scheduling
- USB Audio Class 2/4 advanced clocks and high channel counts
- Bluetooth HCI transports
- unusual HID quirks, RGB devices, composite gaming receivers
- USB 3 hubs, streams, UASP, Type-C/UCSI policy, suspend/resume, power delivery

## Hardware-port qualification

**OFFICIAL FACT:** the ASRock B550M Pro4 manual assigns four rear USB 3.2 Gen1 ports through an ASMedia ASM1074 hub; these should not be first ports ([ASRock B550M Pro4 manual](https://download.asrock.com/Manual/B550M%20Pro4.pdf)). Q470E and the used-market Q370 alternative provide chipset USB, but each exact board block diagram/manual must identify rear/internal routing. Test one physically labeled port at a time and store its root-port/hub path.

Use deliberately boring USB 2 input devices. Firmware compatibility is not proof of class compliance: firmware may emulate a keyboard through SMM before `ExitBootServices`.

## Failure and security requirements

- bounds-check every descriptor and TRB-derived length;
- never trust device-reported endpoint counts, string lengths, or interval values;
- cancel and reclaim rings on disconnect without use-after-free;
- isolate controller DMA with IOMMU before hostile peripherals are in scope;
- put timeouts on reset, commands, and transfers;
- preserve event-ring diagnostics and controller state on fatal error;
- fuzz descriptors and events in QEMU/software models before broad real-device testing.

## Port versus write

**WRITE NATIVE** for the xHCI core against the official register specification. **PORT ALGORITHM/LOGIC** for ring handling, quirks, hub state machines, and USB descriptor validation from mature BSD/Linux/Haiku/Serenity/Redox sources only after license review. A large Linux xHCI port would import DMA, USB core, work queues, timers, scatter/gather, PCI, and power-management assumptions that Malrynth does not yet possess.

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** FreeBSD separates controller and USB-device/core code; for example `usb_device.c` is BSD-2-Clause ([FreeBSD USB device core](https://github.com/freebsd/freebsd-src/blob/main/sys/dev/usb/usb_device.c)). Linux xHCI is GPL-2.0 and demonstrates reset, DCBAA, command/event rings, MSI and a large quirk surface ([Linux xHCI](https://github.com/torvalds/linux/blob/master/drivers/usb/host/xhci.c)). Redox's MIT `xhcid` is a smaller architecture reference, but its GitHub mirror was archived in April 2026 ([Redox drivers](https://github.com/redox-os/drivers)). Audit individual files and dependencies; repository-level reputation is not a license conclusion.

## Recommended integration

The future USB core should separate host-controller, USB device state, hub, and class-driver layers. Keep the first xHCI implementation single-controller/single-interrupter but do not bake those limits into public APIs.

## Source ledger contributions

| Authority | Accessed | Claim supported | URL | Licensing relevance |
|---|---|---|---|---|
| Intel | 2026-08-19 | xHCI register-interface scope; current 1.2c/2.0 downloads and adopter agreement | https://www.intel.com/content/www/us/en/products/docs/io/universal-serial-bus/universal-serial-bus-specifications.html | Specification/adopter terms apply; not a source-code license. |
| QEMU project | 2026-08-19 | Allocated `1b36:000d` for QEMU PCI xHCI | https://www.qemu.org/docs/master/specs/pci-ids.html | Documentation fact; QEMU implementation is GPL-2.0-or-later. |
| Renesas | 2026-08-19 | µPD720202 PCIe/two-port/xHCI 1.0 characteristics | https://www.renesas.com/en/products/upd720202 | Vendor documentation, no code grant. |
| ASMedia | 2026-08-19 | ASM3142 PCIe-to-USB 3.1 Gen2/xHCI 1.1 compliance | https://www.asmedia.com.tw/product/55AYQ83xg4uy6Uj0/0C8YQ4asx4yt2JR4.html | Vendor documentation, no code grant. |
| ASRock | 2026-08-19 | B550M Pro4 physical USB routing through ASM1074 hub | https://download.asrock.com/Manual/B550M%20Pro4.pdf | Board manual may be cited; no code permission. |
| Linux kernel project | 2026-08-19 | xHCI reset/ring/interrupt/quirk complexity and USB core layering | https://github.com/torvalds/linux/blob/master/drivers/usb/host/xhci.c | `GPL-2.0`; behavioral reference unless GPL reuse is intended. |
| FreeBSD project | 2026-08-19 | Separately layered USB device core and permissive file license | https://github.com/freebsd/freebsd-src/blob/main/sys/dev/usb/usb_device.c | `BSD-2-Clause` for cited file; retain notices and audit dependencies. |
| Redox OS project | 2026-08-19 | MIT `xhcid` exists; mirror archived in 2026 | https://github.com/redox-os/drivers | MIT with notice preservation; archived status raises maintenance risk. |
