# Debugging the first physical Malrynth machine

**Status:** research and qualification plan, 2026-08-19. No physical board has been
designated supported.

## Decision summary

**PROPOSED MALRYNTH DECISION:** make a directly accessible, firmware-configurable,
16550-compatible motherboard UART the authoritative R0 failure console. Use a second computer
with the electrically correct board-header-to-RS-232 path (never substitute a TTL lead unless
the board documentation explicitly specifies TTL levels). Mirror progress to GOP, POST code
or LEDs where available. A USB serial adapter is useful only after xHCI and USB enumeration,
so it cannot be the sole earliest-boot path.

The primary MSI MS-98N9 Q470E manual explicitly documents 16550A-compatible UARTs plus
debug headers, making it the strongest canonical debug specimen. ASUS Q470EI-IM-A exposes
multiple COM ports but still needs exact UART qualification. On the used-market path, ASUS
PRIME Q370M-C/CSM exposes two internal COM headers, a speaker and LPC debug-card header, so
COM1 can remain the failure console while COM2 is reserved for a later debugger. Neither a
marketing label nor a connector alone establishes base, clock, interrupt or electrical path;
qualify those on the exact board/firmware and bracket.

## Evidence labels

- **OFFICIAL FACT** — specification-owner or board-vendor documentation.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — a working reference implementation, not a
  Malrynth support claim.
- **COMMUNITY EVIDENCE** — useful practitioner evidence without normative authority.
- **INFERENCE** — conclusion needing exact-board validation.
- **PROPOSED MALRYNTH DECISION** — future project choice, not current architecture.

## Debug-channel hierarchy

| Stage | Primary channel | Secondary channel | Why |
|---|---|---|---|
| QEMU development | Emulated 16550 serial | QEMU debug console/GOP | Deterministic, automatable, loggable before complex drivers |
| UEFI loader | UEFI Serial I/O if present, plus direct qualified UART | GOP framebuffer | Captures failures before kernel ownership |
| Earliest kernel | Direct polled 16550-compatible UART | Fixed GOP framebuffer | Requires only port/MMIO access; avoids interrupts and allocators |
| Interrupt/SMP bring-up | Polled UART with optional tested IRQ transmit path | POST code/LED markers | Serial remains useful if APIC or scheduler fails |
| xHCI operational | Motherboard UART | USB serial or USB debug only as an additional path | USB path depends on the subsystem being debugged |
| Network operational | UART plus bounded remote logging | Persistent crash record | Network logging has routing, driver and link dependencies |
| Panic | Forced polled UART with timeout | Minimal framebuffer/POST code | Avoid locks, heap, scheduler, interrupts and DMA |

**PROPOSED MALRYNTH DECISION:** every boot stage emits a compact monotonic marker to serial,
and important milestones also update a one-screen GOP status page. The last marker must
identify whether failure occurred before or after `ExitBootServices()`, page-table switch,
IDT/APIC enable, SMP start, ACPI parse, PCI scan, IOMMU setup, NVMe reset or xHCI reset.

## UART qualification

A board label such as `COM1` is insufficient. The qualification record must include:

- exact board/SKU/revision and firmware build;
- Super I/O or UART identity where documented;
- I/O or MMIO base, register stride, clock and divisor;
- firmware enable/disable and resource settings;
- IRQ/polarity/trigger only after interrupt mode is tested;
- header pinout and electrical level (TTL, RS-232 or RS-422/485);
- adapter/cable part identity and whether level shifting is present;
- loopback result, cold/warm/reset logs and highest lossless baud rate;
- whether SPCR, DBG2 or UEFI Serial I/O describes the same device.

**OFFICIAL FACT:** UEFI defines Serial I/O and Debugport protocols, while ACPI defines SPCR
and DBG2 tables. They are useful discovery inputs but are not universally present.
[UEFI 2.11](https://uefi.org/specs/UEFI/2.11/),
[ACPI 6.6](https://uefi.org/specs/ACPI/6.6/)

**PROPOSED MALRYNTH DECISION:** use an exact-board profile for the first polled UART, then
cross-check it against firmware tables and enumeration. Never probe arbitrary legacy ports by
writing bytes, and never connect a TTL-only adapter to an RS-232-voltage header.

### Minimal early-console behavior

The earliest writer should configure one fixed, prequalified baud rate; poll transmitter
readiness with a finite iteration/time budget; write bytes without heap allocation or locks;
translate newline consistently; and count dropped/time-out bytes. Panic output may bypass
normal ownership only after quiescing other writers. A recursive panic prints one short marker
and halts rather than reentering formatters.

Serial logs should start with a machine-readable header containing image build ID, worktree
commit, board profile, firmware version, boot attempt ID and reset classification. Avoid
secrets, raw user memory and unbounded firmware strings.

## QEMU-to-hardware continuity

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** QEMU's `q35` machine and emulated serial device
provide a stable development oracle. QEMU device behavior does not prove that an arbitrary
Super I/O, clock or firmware resource assignment matches it.
[QEMU system emulator documentation](https://www.qemu.org/docs/master/system/)

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** QEMU also provides a GDB stub and a one-byte ISA
debug console at the implementation's default port `0xe9`. Use GDB for interactive stop-at-
reset work, serial for the real console contract and debugcon only for pre-UART stage bytes.
[QEMU GDB](https://www.qemu.org/docs/master/system/gdb.html),
[QEMU debugcon source](https://gitlab.com/qemu-project/qemu/-/blob/master/hw/char/debugcon.c)

Keep the log protocol and marker IDs identical between QEMU and the board. Hardware-specific
transport is below that protocol. Maintain golden logs for:

1. successful QEMU cold boot;
2. successful exact-board cold and warm boot;
3. intentional failures before/after UEFI exit;
4. malformed ACPI/PCI/NVMe/xHCI inputs in emulation;
5. reset, S5 and watchdog/timeout outcomes.

This separates a platform failure from a logging-format change.

## Framebuffer diagnostics

GOP is the second independent channel. The loader records physical base, length, resolution,
stride and pixel layout; the kernel validates and reserves the range before drawing. Use a
fixed bitmap font and a small status grid that works without allocation.

The diagnostic screen should expose boot stage, last error code, CPU/APIC counts, ACPI table
signatures/checksum failures, PCI device count, selected IOMMU mode, NVMe/xHCI state, and the
serial byte/time-out counter. Do not scroll large logs or treat a visually correct screen as
proof that cache attributes and bounds are correct.

GOP is valuable if UART setup is wrong, while UART remains valuable if GPU routing, display
cable, pixel format or framebuffer mapping is wrong.

## POST codes, speakers and board indicators

**OFFICIAL FACT:** PRIME Q370M-C/CSM exposes two COM headers, speaker and ASUS-specific LPC
debug-card header; Pro B550M-C/CSM exposes one COM header, speaker and LPC debug; MSI PRO
B550M-P exposes one COM header and four EZ Debug LEDs. Vendor debug headers are not a
universal electrical/API standard. [ASUS Q370 manual](https://dlcdnets.asus.com/pub/ASUS/mb/LGA1151/PRIME_Q370M-C/E14162_PRIME_Q370M-C_UM_WEB.pdf),
[ASUS B550 specifications](https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/),
[MSI B550 specifications](https://www.msi.com/Motherboard/PRO-B550M-P/Specification)

Use POST output only when the exact board and safe register/interface are documented. A
cheap PCIe POST card may not observe firmware LPC codes or may be electrically/topologically
irrelevant on a modern board. Onboard debug LEDs are coarse breadcrumbs, not structured logs.
A speaker beep code can distinguish “kernel reached” from “no display/no UART,” but must be
bounded and disabled after normal audio ownership.

## USB serial and USB debug

A conventional USB-to-UART adapter connected to the target is a USB peripheral: Malrynth
must already own xHCI, enumerate the device, implement its USB-serial protocol and survive
disconnects. Many adapters use vendor-specific protocols. It is therefore a later console,
not the first lifeline.

The reverse arrangement—motherboard UART to a USB adapter attached to the second computer—is
preferred. Malrynth sees only its simple UART; the host OS handles USB.

xHCI defines optional debug capability, but presence, routing and usable external ports are
platform-specific. Treat USB debug as a research item after ordinary xHCI works, not an R0
admission requirement. [xHCI specification landing page](https://www.usb.org/document-library/usb-32-revision-11-june-2022)

## Network and persistent crash logs

Network logging begins only after the native I210-class driver has a bounded nonblocking
panic path. It must never wait indefinitely for link, DHCP, allocation, ARP or a transmit
completion. Use a preconfigured destination and fixed buffers in a test network; UART remains
authoritative.

Persistent crash records require a deliberately reserved, checksummed, versioned area and a
write policy that cannot corrupt the filesystem. Do not issue complex NVMe writes from an
unknown controller state during panic. A later boot can copy a small RAM/pstore-like record
to normal storage.

## JTAG and hardware probes

JTAG, Intel DCI, AMD platform debug and trace probes may exist on development hardware, but
retail enablement, connectors, authentication, documentation and tool cost are inconsistent.
They are not R0 requirements. Preserve an abstraction for halt/trace integration, and record
any vendor debug feature observed, but do not plan the first physical milestone around an
unverified probe.

An inexpensive logic analyzer may help qualify UART electrical timing if already available;
the no-budget plan does not require buying one.

## Acceptance tests

| Test | Pass condition |
|---|---|
| Earliest output | A deliberate loader failure and the kernel's first instruction marker are captured on the host |
| UEFI transition | Markers immediately before and after `ExitBootServices()` are distinguishable |
| Page tables | Serial continues across the final address-space switch or produces an exact failure marker |
| SMP/interruption | Concurrent CPU logging cannot deadlock; panic can bypass normal locks |
| Negative UART | Missing/stuck transmitter times out and boot continues with GOP instead of hanging |
| Reset/S5 | Last marker is flushed in a bounded interval for 25 repeated reset and shutdown trials |
| Reproducibility | Another operator can wire the recorded header/adapter and decode the log from the written profile |
| Privacy | Logs contain no secrets or arbitrary user-memory dumps by default |

## Cost-aware kit

Use the existing second computer, a vendor-correct COM bracket or level adapter, and one
ordinary cable. Prefer a board with a rear DB-9 connector; if it uses a header, verify pinout
before purchase. Do not buy JTAG equipment, a dedicated lab server or a discrete GPU for
PHYSICAL-0/1.

## Recommended integration

Later project-owned debug specifications may adopt the stage markers, bounded panic writer,
machine-readable log header and dual serial/GOP rule. Keep all board addresses and pinouts in
the hardware record, not general architecture.

## Source ledger contributions

| Authority | Accessed | Claim contributed | URL | Licensing relevance |
|---|---|---|---|---|
| UEFI Forum | 2026-08-19 | Serial, Debugport and GOP boot interfaces | https://uefi.org/specs/UEFI/2.11/ | Specification; no code copied |
| UEFI Forum | 2026-08-19 | SPCR/DBG2 and ACPI platform description | https://uefi.org/specs/ACPI/6.6/ | Specification; no code copied |
| MSI | 2026-08-19 | Q470E board's reviewed English manual dated 2023-01-31 documents 16550A UARTs and hardware debug surfaces | https://ipc.msi.com/product_download/Industrial-Motherboard/ATX/MS-98N9 | Manual facts only |
| ASUS | 2026-08-19 | Q370 two COM headers, speaker and vendor-specific LPC debug header/card | https://dlcdnets.asus.com/pub/ASUS/mb/LGA1151/PRIME_Q370M-C/E14162_PRIME_Q370M-C_UM_WEB.pdf | Manual facts only |
| ASUS | 2026-08-19 | B550 COM/LPC debug/speaker availability | https://www.asus.com/motherboards-components/motherboards/csm/pro-b550m-c-csm/techspec/ | Product facts only |
| MSI | 2026-08-19 | Budget B550 COM and debug-LED facilities | https://www.msi.com/Motherboard/PRO-B550M-P/Specification | Product facts only |
| QEMU project | 2026-08-19 | q35 and serial development oracle | https://www.qemu.org/docs/master/system/ | GPLv2; no code copied |
| QEMU project | 2026-08-19 | GDB stub and ISA debugcon behavior | https://www.qemu.org/docs/master/system/gdb.html | GPL-2.0 project; tool usage only |
| USB-IF | 2026-08-19 | xHCI host/debug capability context | https://www.usb.org/document-library/usb-32-revision-11-june-2022 | Specification terms; no code copied |
