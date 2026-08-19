# Audio reference: PCM core, USB class first physical path, HDA later

Research snapshot: 2026-08-19. Scope: Intel High Definition Audio (HDA), USB Audio Class (UAC), HDMI/DisplayPort audio, virtual audio and the boundary between basic playback and professional-audio support.

## Evidence labels

- **OFFICIAL FACT** — normative/vendor/standards-body material.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — maintained source demonstrates behavior/complexity; license controls copying.
- **COMMUNITY EVIDENCE** — field evidence only, never the sole basis for a support claim.
- **INFERENCE** — engineering conclusion from the sources.
- **PROPOSED MALRYNTH DECISION** — recommended project policy.

## Decision and target ranking

**PROPOSED MALRYNTH DECISION:** build a transport-neutral PCM engine first. Use a simple
USB Audio Class 1 playback device as the first physical audio target after xHCI isochronous
transfers are reliable. QEMU HDA remains a deterministic development oracle, while physical
motherboard HDA follows as a later desktop target. HDMI/DisplayPort audio follows the relevant
GPU/display driver. Audio is not an R0 boot gate. Do not spend early effort on AC'97, Sound
Blaster, vendor DSP/SoundWire machine drivers or Bluetooth audio.

| Rank | Family | Concrete identity / contract | Phase and boundary |
|---|---|---|---|
| 1 | Standards-class USB Audio 1.0 DAC or simple duplex headset | USB Audio class descriptors, not VID:PID | First physical audio path after xHCI isochronous support. Start with fixed 48-kHz stereo playback and no vendor driver; implement a bounded UAC1 subset, not “all USB audio” ([USB-IF Audio document library](https://www.usb.org/documents?search=audio)). |
| 2 | QEMU ICH9 HDA plus `hda-duplex`/`hda-output` codec | PCI multimedia-audio class `04:03`; ICH9 hardware identity is `8086:293e` when that model is selected | Deterministic playback/capture laboratory that may run before physical UAC. Use model plus class and record actual ID; do not generalize an ICH9 quirk to all HDA. QEMU has a dedicated ICH9 HDA test model ([QEMU HDA test](https://gitlab.com/qemu-project/qemu/-/blob/master/tests/qtest/intel-hda-test.c), [upstream ICH9 identity evidence](https://android.googlesource.com/kernel/common/+/e0a30b8f9550000cfde7b0292e76fcb23e358060/sound/pci/hda/hda_intel.c)). |
| 3 | Desktop Intel/AMD HDA controller with conventional analog codec, especially Realtek ALC887/892/897/1220-class boards | bind controller by `04:03`; discover codec vendor/device and widget graph through HDA verbs; exact subsystem/codec captured per board | Later physical desktop path. Choose a board with rear line-out and no mandatory vendor DSP. The HDA spec defines a discoverable controller/codec interface, but board pin routing still needs validation ([Intel HDA 1.0a](https://www.intel.la/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf)). |
| 4 | Virtio-sound | Virtio device ID 25; modern PCI ID follows the standard mapping (device ID + `0x1040`, therefore `1af4:1059`) | Optional virtual fast path after common virtio. QEMU currently limits its implementation: stereo streams and unimplemented jack/channel-map properties ([OASIS Virtio 1.4](https://docs.oasis-open.org/virtio/virtio/v1.4/cs01/virtio-v1.4-cs01.html), [QEMU virtio-sound](https://www.qemu.org/docs/master/system/devices/virtio/virtio-snd.html)). |
| 5 | GPU HDMI/DisplayPort HDA codec | GPU audio function plus display codec/pin/ELD, hot-plug and active mode | R2/later. Requires GPU/display cooperation and licensed HDMI material; not “analog HDA with a different jack.” |
| 6 | Intel SOF/DSP, SoundWire/I2S/DMIC laptop topology | ACPI/NHLT, DSP firmware, machine driver and codec-specific bus | Later selected platforms. A visible HDA PCI function does not guarantee the laptop speakers/mics use the legacy HDA link. |

**OFFICIAL FACT:** HDA 1.0a supports discoverable codecs, command/response verbs, DMA streams, unsolicited responses, jack sensing, sample rates to 192 kHz, multiple widths and channels; it is explicitly not backward-compatible with AC'97 ([Intel HDA specification](https://www.intel.la/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf)). **PROPOSED MALRYNTH DECISION:** AC'97 is a later legacy plug-in only if owned target hardware demands it.

## Common PCM/audio service

Define the driver-independent unit as frames, not bytes. A stream format contains sample representation (signed integer initially), valid/container bits, channel count/map, sample rate and interleaving. A stream exposes a monotonic hardware position, period notifications, start/stop/drain, underrun/overrun count and a device-generation change. Checked conversions prevent `frames × channels × bytes` overflow.

R0/R1 baseline is signed little-endian 16-bit, stereo, 48 kHz playback. Capture, mono, 44.1 kHz and 24-bit containers follow, but the API represents them from day one. Do not silently reinterpret unsupported formats; a user-space mixer/resampler may convert explicitly. The kernel owns DMA period/ring mechanics, while user space owns policy mixing, per-application volume, resampling, device selection and effects.

Use a bounded cyclic buffer with at least two periods. Hardware IRQ reports completed periods and snapshots the position; it does not mix or allocate. Writers cannot overwrite DMA-owned frames. On underrun, output zero/silence, increment XRUN and resynchronize at a defined boundary. On capture overrun, drop according to explicit policy and mark discontinuity. Device removal/reset completes all clients with a generation error exactly once.

Security/privacy: capture devices are closed by default; opening a microphone requires user/session authorization. Hardware mute/jack state is advisory unless backed by a trusted physical switch. No raw microphone data, DMA buffers or audio content appears in logs/crash dumps. Playback gain starts muted during route construction to avoid pops or full-volume surprises.

## HDA controller implementation

### Discovery, reset and verb transport

Bind PCI multimedia audio class/subclass and a reviewed controller table. Validate BAR, enable memory/bus mastering and establish DMA width; mask `INTCTL` before reset. Drive `GCTL.CRST` low then high with specification delays/deadlines, read `STATESTS` to discover codecs, and fail rather than spin if reset/codec presence never stabilizes.

Allocate a Command Output Ring Buffer (CORB) and Response Input Ring Buffer (RIRB), select supported ring sizes, zero them, program DMA bases/pointers, start RIRB before issuing verbs, then enable interrupts. Tag each outbound verb with codec address/node/verb/payload and associate solicited responses in strict transport order; unsolicited responses are distinguished and dispatched separately. RIRB overrun or response timeout triggers a serialized link reset and graph re-enumeration. Immediate Command is a bounded bring-up fallback, not mixed concurrently with CORB/RIRB.

**OFFICIAL FACT:** the specification’s MMIO layout includes CORB/RIRB base/control/pointers, immediate command registers, DMA position buffer and stream descriptors ([Intel HDA 1.0a register table](https://www.intel.la/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf)). Modern Intel PCH documentation still lists memory command/response, immediate command, stream sync, MSI, D-states and DMA position writes ([Intel 800-series HDA capabilities](https://edc.intel.com/content/www/us/en/design/products/platforms/details/arrow-lake-s/800-series-chipset-family-platform-controller-hub-pch-datasheet-volume/intel-high-definition-audio-intel-hd-audio-controller-capabilities/)).

### Codec/widget discovery and routing

For each present codec address, query root-node vendor/revision and subordinate node range. Find Audio Function Groups, enumerate every node, and record widget type/capabilities, connection lists, PCM/rate support, stream formats, input/output amplifier caps, pin caps/config-default, power states and unsolicited support. Cap node/connection counts and detect malformed/cyclic graphs.

Build routes from an Audio Output Converter through selectors/mixers to a Pin Complex whose default device/connectivity indicates line-out/headphone/speaker. Pick the simplest valid stereo route supported at 48-kHz/16-bit. Configure power state D0 along the path, converter format/stream tag/channel, connection selectors, pin output control/EAPD and amplifiers; ramp/unmute last. On stop, mute first and power down later under policy.

**PROPOSED MALRYNTH DECISION:** use default pin configuration and widget graph before any codec-specific patch. A quirk matches controller subsystem + codec ID/revision and describes a small route/pin correction with an owned-board test. Do not embed opaque vendor coefficient sequences copied from a binary driver. Front-panel auto-mute/jack detection and capture muxes are R1 extensions after fixed rear line-out works.

### DMA streams

Choose an output stream descriptor advertised by `GCAP`, reset it, allocate an aligned Buffer Descriptor List and PCM pages, and program each BDL entry with a DMA address, nonzero bounded length and IOC on period boundaries. Program cyclic buffer length/last-valid index/format, assign a nonzero stream tag and program the same tag/format on the converter before Run. Publish filled PCM data before handing descriptors/running to hardware with DMA ordering barriers.

Use stream completion/FIFO/descriptor error status and global interrupt status; acknowledge only defined write-one-to-clear bits. Derive progress from the DMA position buffer when reliable, otherwise LPIB with monotonic/wrap correction. Never trust a position beyond cyclic length. Stop clears Run and waits FIFO/DMA quiescence before freeing BDL/audio pages. Reset increments generation and rebuilds CORB/RIRB, codecs, routes and streams.

MSI is preferred after polling bring-up. One controller interrupt is enough for R0. Stream sync, multiple streams, channel striping, 24/32-bit and capture are later. Maintain wall-clock/position timestamps even before exposing a professional API.

## USB Audio Class

**OFFICIAL FACT:** USB Audio Device Class 4.0 (with ECNs through 2025-10-31) is current and covers audio manipulation, gain and tone functions; the USB-IF also publishes UAC2 with 2025 errata ([USB Audio 4.0](https://www.usb.org/document-library/usb-audio-devices-release-40-and-adopters-agreement), [USB Audio documents](https://www.usb.org/documents?search=audio)). **PROPOSED MALRYNTH DECISION:** support UAC1 playback first, then selected UAC2, regardless of the current top version. Version number is not a reason to ingest all topology/power/clock features.

Parse AudioControl entity graphs and AudioStreaming alternate settings with strict length/count bounds. Select one PCM Type-I-like format and channel/rate combination. Claim isochronous bandwidth before setting the alternate interface. Schedule multiple future service intervals so normal interrupt latency does not starve the pipe; isochronous packets are not retried, and per-packet status/actual length drives XRUN accounting.

Correct clocking is central. Support synchronous/adaptive/asynchronous endpoint attributes as explicitly declared. For asynchronous OUT, implement explicit feedback endpoint format/interval before claiming the device; implicit feedback waits for a paired capture/data endpoint implementation. Linux has hundreds of lines and a device-quirk table specifically for implicit feedback, strong evidence that it is not safe to guess ([Linux USB implicit feedback](https://github.com/torvalds/linux/blob/master/sound/usb/implicit.c), [USB endpoint engine](https://github.com/torvalds/linux/blob/master/sound/usb/endpoint.c)).

Rank test devices by standards simplicity:

1. owned UAC1 stereo playback DAC with one fixed 48-kHz alternate setting and no vendor driver;
2. UAC1 duplex headset with microphone authorization and Feature Unit volume/mute;
3. UAC2 interface with explicit clock source and explicit feedback;
4. multichannel/high-rate/implicit-feedback professional interfaces only after clock-domain and quirk work.

No VID:PID belongs in base binding. Device quirks require descriptor capture, upstream/owned evidence and exact match.

## HDMI/DisplayPort audio

HDMI/DP audio commonly appears as a digital-display HDA codec/controller associated with the GPU. The route depends on a connected display, current mode/pixel clock, ELD/EDID-derived sink audio capabilities, hot-plug, pin/converter assignment and GPU power. **PROPOSED MALRYNTH DECISION:** the HDA core can enumerate digital pins, but a GPU-specific bridge must supply validated ELD/hot-plug and enable the display audio path. Do not present a sink after unplug or promise a rate/channel layout absent from ELD.

HDMI 2.2 is current and its full specification is obtained through the HDMI Adopter Extranet/license; HDMI Licensing Administrator describes itself as licensing agent ([HDMI specification access](https://www.hdmi.org/spec/), [HDMI 2.2 overview/licensing](https://www.hdmi.org/spec/hdmi2?pubDate=20260205)). **PROPOSED MALRYNTH DECISION:** defer HDMI feature claims and obtain legal/specification access through the display program. Use publicly documented HDA/ELD interoperability without copying restricted HDMI text. HDCP is not needed for ordinary unprotected PCM and is outside this audio-driver scope.

## Modern laptop caveat: DSP, SoundWire and DMIC

**OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux has separate Intel SOF HDA code that maps a DSP BAR, loads firmware, scans SoundWire/ACPI topology and supports a DSP-less mode; the file is dual `GPL-2.0-only OR BSD-3-Clause` ([Linux SOF Intel HDA](https://github.com/torvalds/linux/blob/master/sound/soc/sof/intel/hda.c)). Board configuration also distinguishes DSP/I2S/DMIC/SoundWire machine drivers ([Linux Intel audio boards](https://github.com/torvalds/linux/blob/master/sound/soc/intel/boards/Kconfig)).

**INFERENCE:** successful HDA PCI enumeration on a recent laptop may yield HDMI only or no usable internal speaker/mic route. Therefore select a conventional desktop HDA codec for first physical acceptance and list DSP/SoundWire laptops as unsupported until firmware, ACPI topology, machine routing and microphone privacy are implemented.

## Professional-audio implications

Basic audible playback is not professional audio. Do not use “pro,” “low-latency,” “bit-perfect” or “studio” claims until Malrynth has measured and exposed:

- stable, monotonic hardware/sample timestamps and clock-domain identity;
- selectable period/buffer sizes with bounded scheduler/IRQ latency and an XRUN API;
- page-locked/prefaulted buffers, priority inheritance and a real-time scheduling policy;
- exact sample/container widths including packed 24-bit, 44.1/48-kHz families, multichannel maps and no hidden format conversion;
- full-duplex synchronized start, drift measurement/correction and explicit USB feedback behavior;
- exclusive/raw mode, routing/mixer controls in dB units, per-device calibration and deterministic hot-plug failure;
- MIDI 1/2 timestamping if offered, and a graph/API suitable for JACK-like routing;
- a latency test that measures application-to-DAC/ADC round trip with external equipment, not buffer duration alone.

**INFERENCE:** HDA can advertise high rates/channels, but board codec/route, mixer, scheduler and clock make the user result. USB “class compliant” similarly says protocol interoperability, not guaranteed low latency. R0/R1 should claim only the exact formats/devices tested.

## Staged delivery and acceptance

| Stage | Deliverable | Exit evidence |
|---|---|---|
| R0-A | PCM format/ring API, null sink and deterministic test tone/file path | Frame/byte overflow tests, ring wrap, XRUN/disconnect generation, mixer tests off-device. |
| Parallel virtual lab | QEMU HDA CORB/RIRB, graph discovery, fixed 48-kHz stereo playback | Recorded host output hash/frequency, stream wrap, forced underrun, reset, malformed response, repeated start/stop. |
| R1 first physical audio | UAC1 simple DAC after xHCI isochronous | Descriptor fuzzing, packet-loss/XRUN, explicit rates, hub path, unplug under playback. |
| Later desktop audio | QEMU capture, physical desktop rear line-out on one HDA codec/board | Mic authorization, route/mute sequencing, jack states, cold/warm boot, MSI, 64-bit DMA, no pops/full-volume start. |
| R2 | UAC2 explicit feedback/duplex; virtio-sound; HDMI with one supported GPU | Clock/feedback drift, full duplex, display hot-plug/ELD, VM limitations documented. |
| Later | SOF/SoundWire laptops, Bluetooth audio, professional mode | Firmware/license/topology gates plus measured latency/interoperability suites. |

Record PCI/USB IDs and revisions, HDA codec ID/subsystem, full chosen route, formats, DMA/interrupt mode, firmware, period/buffer size and test signal. Listening alone is not acceptance; compare captured waveforms for rate, channel order, clipping, discontinuity and drift.

## Write versus port; upstream/license notes

**PROPOSED MALRYNTH DECISION:** write the small PCM engine and HDA controller/codec graph from Intel HDA 1.0a plus published change notices. Port only narrow, permissively licensed pieces whose data ownership maps to Malrynth. Intel’s specification is a reference, not a source-code license; preserve citations and review terms.

Redox’s archived MIT Rust driver repository contains `ihdad`, `ac97d`, `sb16d` and audio infrastructure ([Redox drivers](https://github.com/redox-os/drivers)). `ihdad` is the most relevant port candidate if Malrynth is Rust. Audit current upstream, codec graph completeness, BDL lifetime, response/event races and process/scheme integration; preserve MIT notices. Do not port AC'97 merely because code exists.

Linux’s HDA core/header is `GPL-2.0`, and USB audio files shown here are `GPL-2.0-or-later` ([Linux HDA core](https://github.com/torvalds/linux/blob/master/include/sound/hdaudio.h), [Linux USB endpoint](https://github.com/torvalds/linux/blob/master/sound/usb/endpoint.c)). They are excellent edge-case/quirk/test references; copying requires GPL-compatible distribution. Some SOF files offer BSD-3-Clause as an alternative, but firmware, linked files and topology code require component-level audit.

OASIS Virtio 1.4 specifies sound under its Non-Assertion IPR mode and allows explanatory/implementation derivatives with notices ([Virtio 1.4](https://docs.oasis-open.org/virtio/virtio/v1.4/cs01/virtio-v1.4-cs01.html)). A clean virtio-sound driver is preferable to copying QEMU’s GPL implementation.

USB Audio 4.0 is distributed with an adopter agreement ([USB-IF Audio 4.0](https://www.usb.org/document-library/usb-audio-devices-release-40-and-adopters-agreement)); legal review is required before compliance claims. HDMI 2.2 access explicitly requires adopter licensing. Codec patent/licensing review is separate for compressed formats; basic uncompressed PCM does not justify bundling MP3/AAC/aptX/LC3 code.

No community-only report drives these choices. Community device reports may identify codec quirks only after an owned reproduction and captured graph/route.

## Recommended integration

Carry only the staged UAC1-first ordering and device/codec test-record fields into project-owned driver plans after founder review. Do not turn HDA, HDMI audio, SoundWire, Bluetooth audio, or professional-audio goals into R0 gates.

## Source ledger contributions

| Authority | Accessed | Claim contributed | URL | Licensing relevance |
|---|---|---|---|---|
| Intel | 2026-08-19 | HDA 1.0a registers, verbs, codecs, DMA streams, formats and AC'97 incompatibility | https://www.intel.la/content/dam/www/public/us/en/documents/product-specifications/high-definition-audio-specification.pdf | Vendor specification, not source-code license; review document terms and cite. |
| Intel | 2026-08-19 | Current PCH HDA controller capabilities and continued standard interface | https://edc.intel.com/content/www/us/en/design/products/platforms/details/arrow-lake-s/800-series-chipset-family-platform-controller-hub-pch-datasheet-volume/intel-high-definition-audio-intel-hd-audio-controller-capabilities/ | Public vendor documentation; no code grant. |
| QEMU project | 2026-08-19 | Reproducible current ICH9 HDA model/test configuration | https://gitlab.com/qemu-project/qemu/-/blob/master/tests/qtest/intel-hda-test.c | QEMU is GPL-2.0-or-later; use as executable oracle or comply before copying. |
| USB Implementers Forum | 2026-08-19 | Current UAC4 and UAC2 documents | https://www.usb.org/documents?search=audio | Specifications have USB-IF terms; version availability is not code permission. |
| USB Implementers Forum | 2026-08-19 | UAC4 scope and adopter agreement | https://www.usb.org/document-library/usb-audio-devices-release-40-and-adopters-agreement | Review adopter terms before compliance/product claims. |
| OASIS | 2026-08-19 | Virtio 1.4 sound device ID/queues and IPR/copy notices | https://docs.oasis-open.org/virtio/virtio/v1.4/cs01/virtio-v1.4-cs01.html | OASIS Non-Assertion mode; retain required copyright/notices. |
| QEMU project | 2026-08-19 | Current virtio-sound implementation limits | https://www.qemu.org/docs/master/system/devices/virtio/virtio-snd.html | Documentation/test target; QEMU implementation source is GPL. |
| HDMI Licensing Administrator | 2026-08-19 | HDMI 2.2 current; specification access/licensing model | https://www.hdmi.org/spec/ | HDMI adopter/trademark/specification license applies. |
| HDMI Licensing Administrator | 2026-08-19 | HDMI 2.2 adopter-extranet requirement | https://www.hdmi.org/spec/hdmi2?pubDate=20260205 | Legal gate for HDMI compliance claims; not open implementation text. |
| Linux kernel project | 2026-08-19 | HDA graph/core implementation complexity and SPDX | https://github.com/torvalds/linux/blob/master/include/sound/hdaudio.h | `GPL-2.0`; reference unless GPL reuse intended. |
| Linux kernel project | 2026-08-19 | USB isochronous/feedback implementation complexity | https://github.com/torvalds/linux/blob/master/sound/usb/endpoint.c | `GPL-2.0-or-later`; same restriction. |
| Linux/Sound Open Firmware project | 2026-08-19 | Modern Intel DSP/SoundWire/firmware path distinct from legacy HDA | https://github.com/torvalds/linux/blob/master/sound/soc/sof/intel/hda.c | Dual GPL-2.0-only/BSD-3-Clause file, but dependencies and firmware need separate audit. |
| Redox OS project | 2026-08-19 | MIT Rust `ihdad` port candidate; repository archived | https://github.com/redox-os/drivers | MIT with notice preservation; audit current provenance, correctness and architecture fit. |
