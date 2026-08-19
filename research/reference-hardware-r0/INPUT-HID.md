# Input: USB HID first

## Evidence labels

- **OFFICIAL FACT** — standards-body or platform specification.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — upstream implementation evidence; license governs reuse.
- **COMMUNITY EVIDENCE** — field reports/inventory, not a conformance claim.
- **INFERENCE** — engineering conclusion from cited evidence.
- **PROPOSED MALRYNTH DECISION** — recommended project policy.

## Decision

**PROPOSED MALRYNTH DECISION:** wired USB HID keyboard and mouse are R0. PS/2 is **OPTIONAL DEBUG FALLBACK**, not an early required driver.

**OFFICIAL FACT:** HID 1.11 is self-describing: report descriptors define fields and Usage Tables define their meaning; USB-IF's current Usage Tables are 1.7, dated 2026-01-27 ([USB-IF HID specifications](https://www.usb.org/hid), [HID Usage Tables 1.7](https://usb.org/document-library/hid-usage-tables-17)). That generality is also an attack surface, so R0 should begin with boot protocol and add a bounded report-descriptor parser after xHCI is stable.

## Keyboard path

1. Enumerate a USB HID interface and its interrupt-IN endpoint.
2. If supported, select boot protocol for the first console; handle the fixed modifier/key array and rollover/error values.
3. Map USB usages to internal physical key codes, not directly to Unicode.
4. Maintain modifiers/locks and key-up state; recover cleanly after missed or malformed reports.
5. Add report protocol and LED output reports only after the parser is fuzzed.

## Mouse path

Start with boot-protocol relative X/Y and buttons. Clamp arithmetic and preserve sign. Wheels, extra buttons, absolute devices, touchpads, and high-resolution scrolling require descriptor-driven report protocol and belong after the basic parser.

## HID parser requirements

- bounded global/local state stack and collection depth
- checked report offsets/widths and total report size
- no multiplication/addition overflow
- unknown usages skipped without desynchronizing the report
- separate input, output, and feature reports plus report IDs
- per-device limits and an explicit quirk table, never unbounded vendor interpretation in the interrupt path
- transport-neutral HID core so USB, Bluetooth HID, and later I2C HID can share parsing

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux documents HID core as independent from USB, Bluetooth, I2C, or userspace transport. This is a sound layering reference, not code to compile unchanged.

The upstream documentation assigns raw transport and setup to a lower-level driver while HID core parses and interprets reports ([Linux HID transport documentation](https://docs.kernel.org/hid/hid-transport.html)). **INFERENCE:** Malrynth should expose the same conceptual seam without copying Linux object models: USB owns endpoint lifetime; HID owns descriptor/report meaning; the input service owns focus, layout, repeat and text composition.

## Device qualification

First devices should be wired, single-interface, low/full-speed, class-compliant, and usable without vendor software. Record VID:PID, bcdDevice, descriptor hashes, protocol, endpoint, tested root port/hub, and any quirk. Avoid RGB keyboards, wireless dongles, biometric keys, NKRO-only devices, composite headsets, and gaming mice for the initial profile. **PROPOSED MALRYNTH DECISION:** match the USB HID class/interface/protocol and parsed descriptors, never a VID:PID allowlist; IDs identify qualified specimens and quirks only.

**COMMUNITY EVIDENCE:** retail names and crowd-sourced VID:PID lists frequently span silent firmware revisions. They may help procure specimens, but only captured descriptors plus a physical test run support a Malrynth claim.

## PS/2 assessment

### Arguments for a fallback

- very small controller/keyboard path on boards that expose a real i8042-compatible interface;
- independent of xHCI and useful if USB bring-up fails;
- some candidate boards expose a combined PS/2 connector.

### Arguments against R0 requirement

- modern firmware may synthesize legacy input through SMM or route it through Super I/O in board-specific ways;
- mouse/keyboard multiplexing and controller self-test/translation carry legacy quirks;
- an industrial UART plus serial console is a better earliest diagnostic channel;
- requiring PS/2 narrows modern board selection while adding no production capability.

**PROPOSED MALRYNTH DECISION:** do not block PHYSICAL-0/1 or R0 certification on PS/2. A tiny polled i8042 diagnostic driver may be added if the chosen exact board proves it exposes a conventional controller and USB bring-up needs an independent input path.

**OFFICIAL FACT:** ACPI 6.6 is current, and its IA-PC Boot Architecture flags include an `8042` indication for port `0x60`/`0x64` keyboard-controller support ([UEFI ACPI specifications](https://uefi.org/specifications), [ACPI 6.6 software programming model](https://uefi.org/specs/ACPI/6.6/05_ACPI_Software_Programming_Model.html)). **INFERENCE:** blind i8042 probing on a platform that does not advertise legacy support is inappropriate. Even when advertised, PS/2 mouse multiplexing, translation and hot-plug behavior are not necessary for the minimal fallback.

## Staged support and acceptance

| Stage | Deliverable | Exit test |
|---|---|---|
| R0-A | boot keyboard over a direct xHCI root port | modifiers, press/release, rollover-error recovery, unplug/replug |
| R0-B | boot relative mouse | signed X/Y, buttons, bounds, unplug/replug |
| R0-C | bounded report parser and LEDs | fuzz corpus, report IDs, unknown usages, malformed descriptor rejection |
| R1 | composite devices, wheel/extra buttons, selected gamepads | per-interface detach and independent reports |
| Later | Bluetooth/I2C HID, touch/multitouch, vendor quirks | transport and security-specific qualification |

## Port versus write

**PROPOSED MALRYNTH DECISION:** **WRITE NATIVE** for boot keyboard/mouse and internal event conversion. **PORT ALGORITHM/LOGIC** for a descriptor parser only after an audit. USB-IF recommends Microsoft's Waratah, whose HID engine is MIT, as an authoring/validation oracle rather than a host driver ([USB-IF HID tools](https://www.usb.org/hid), [Microsoft HID Tools](https://github.com/microsoft/hidtools)). Redox has MIT `usbhidd` and `ps2d`, but its mirror is archived ([Redox drivers](https://github.com/redox-os/drivers)). Linux is GPL-2.0 and is behavioral evidence unless GPL reuse is explicitly selected. Keep parser tests host-runnable and feed malformed descriptors.

## Recommended integration

Define input events independently from HID usages and transports. That lets later Bluetooth/I2C devices reuse policy without putting USB report parsing into application/platform architecture.

## Source ledger contributions

| Authority | Accessed | Claim supported | URL | Licensing relevance |
|---|---|---|---|---|
| USB Implementers Forum | 2026-08-19 | HID 1.11 goals, report self-description, current HUT 1.7 and Waratah recommendation | https://www.usb.org/hid | Specification/tool terms differ; specification is not a code grant. |
| USB Implementers Forum | 2026-08-19 | HUT 1.7 publication date/current usage definitions | https://usb.org/document-library/hid-usage-tables-17 | USB-IF document terms; cite, do not assume source license. |
| UEFI Forum | 2026-08-19 | ACPI 6.6 current and IA-PC 8042 discovery mechanism | https://uefi.org/specifications | ACPI specification terms apply; no code grant. |
| Linux kernel project | 2026-08-19 | HID core/transport separation and report responsibilities | https://docs.kernel.org/hid/hid-transport.html | Linux documentation/code is GPL-2.0; behavioral reference. |
| Microsoft | 2026-08-19 | Waratah/HID engine implementation and MIT license | https://github.com/microsoft/hidtools | MIT; retain copyright/license if code is reused. |
| Redox OS project | 2026-08-19 | MIT `usbhidd` and `ps2d` implementation evidence; repository archived | https://github.com/redox-os/drivers | MIT with notice preservation; archived status raises maintenance risk. |
