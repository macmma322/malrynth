# Wi-Fi and Bluetooth staging

## Evidence labels

- **OFFICIAL FACT** — standards-body or vendor documentation.
- **OPEN-SOURCE IMPLEMENTATION EVIDENCE** — upstream code/firmware evidence; license governs reuse.
- **COMMUNITY EVIDENCE** — field inventory/procurement evidence, not a support guarantee.
- **INFERENCE** — engineering conclusion from cited evidence.
- **PROPOSED MALRYNTH DECISION** — recommended project policy.

## Decision

**PROPOSED MALRYNTH DECISION:** Wi-Fi is **R3**, not R0/R1. Bluetooth controller transport and HCI exploration may begin alongside R3, but BT HID is the first profile and audio is later. R0 uses wired Ethernet and wired USB devices.

The first **native research** family should be a replaceable conventional PCIe Atheros ath9k AR9280/AR9380 adapter; the first **modern driver-domain** family should be a conventional PCIe Intel AX200/AX210 with separately enumerated USB Bluetooth. Exact product support remains uncommitted until EEPROM/calibration, firmware redistribution, regulatory enforcement and host-interface work are proven.

## Why Wi-Fi is not “another PCI driver”

### Firmware

Current Intel adapters use substantial separately distributed firmware with a driver/firmware API. **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Intel's upstream documentation couples iwlwifi, mac80211, cfg80211, backport, firmware and userspace components in validated releases ([iwlwifi release components](https://wireless.docs.kernel.org/en/latest/en/users/drivers/iwlwifi/core_release.html), [iwlwifi firmware](https://wireless.docs.kernel.org/en/latest/en/users/drivers/iwlwifi.html)). Firmware crashes require their own diagnostics and recovery; redistribution permission and source-code permission are separate questions.

### MAC/PHY split

Depending on the MAC/PHY split, the host implements or coordinates scanning, authentication/association, rate control, aggregation/reordering, encryption/key programming, power save, management frames, remain-on-channel and virtual interfaces. A full-MAC device moves more logic into firmware but replaces host algorithms with a vendor command/event protocol. **INFERENCE:** neither soft-MAC nor firmware-heavy hardware is a small register driver; the former requires a reusable 802.11 MAC layer and the latter a versioned firmware ABI plus recovery.

### Regulatory handling

Transmit frequencies, bandwidth, power, DFS/radar, indoor/outdoor limits and country changes are safety/legal constraints. **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** Linux combines cfg80211, driver/EEPROM constraints and a signed regulatory database; upstream describes the database as ISC-licensed and intended for reuse by other platforms ([Linux wireless regulatory design](https://wireless.docs.kernel.org/en/latest/en/developers/regulatory.html), [wireless-regdb](https://wireless.docs.kernel.org/en/latest/en/developers/regulatory/wireless-regdb.html)). **PROPOSED MALRYNTH DECISION:** transmit is disabled unless an authenticated, updateable database and hardware-specific restrictions intersect to permit the channel/power.

### Userspace security and policy

802.11 authentication is not one ioctl. WPA2/WPA3, EAPOL, SAE, enterprise EAP, key lifecycle, credential UI/storage, scanning, roaming and connection policy need a supplicant/service boundary. Power management covers station doze/wake, DTIM/listen interval, firmware ownership, PCIe ASPM, suspend/resume and wake-on-wireless; coexistence adds Bluetooth/platform interactions. **OPEN-SOURCE IMPLEMENTATION EVIDENCE:** wpa_supplicant supplies mature security/policy logic under a BSD license and already has Linux/BSD driver seams ([wpa_supplicant README](https://android.googlesource.com/platform/external/wpa_supplicant_8/+/master/README)).

## Wi-Fi stages

1. **Passive research:** parse PCI identity, collect firmware licenses/APIs, design regulatory boundary; no radio control.
2. **Lab receive/scan:** firmware boot and restricted passive/scan behavior in a shielded/controlled regulatory configuration.
3. **R3 client subset:** one adapter, one region database, infrastructure station mode, WPA2-Personal first, no AP/P2P/monitor promise.
4. **Security expansion:** WPA3-SAE, protected management frames, robust key deletion/recovery.
5. **Mobility/power:** roaming, suspend, coexistence, enterprise authentication.

## Candidate families

| Family | Assessment | Notes |
|---|---|---|
| Atheros ath9k AR9280/AR9380 PCIe | **rank 1 native research** | replaceable, older 802.11n soft-MAC family with extensive open host evidence; aging supply, EEPROM/calibration and GPL implementation still block a casual port ([ath9k supported chipsets](https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath9k.html)) |
| Intel AX200/AX210 PCIe | **rank 1 modern/domain** | conventional PCIe Wi-Fi plus USB BT; Intel documents that AX200 uses Wi-Fi over PCIe and BT over USB ([Intel AX200](https://www.intel.com/content/www/us/en/products/sku/189347/intel-wifi-6-ax200-gig/specifications.html)); firmware-heavy and Linux-stack dependent |
| MediaTek MT7921/MT7922 | **rank 2 selective-port research** | modern combo family; cited Linux PCI file is BSD-3-Clause-Clear, but it depends on mt76/mac80211 and firmware, so that file alone is not a portable driver ([Linux MT7921 PCI](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/mediatek/mt76/mt7921/pci.c)) |
| Atheros ath9k_htc AR9271/AR7010 USB | **rank 3 lab adapter** | open firmware exists and upstream publishes concrete USB IDs such as `0cf3:9271`; adds USB/firmware latency and is 2.4-GHz/legacy hardware ([ath9k_htc device list](https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath9k_htc/devices.html), [ath9k_htc firmware](https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath9k_htc.html)) |
| Intel 9560/AX201/AX211 CNVi | **reject first target** | depends on compatible Intel platform/CNVi split; poor portable reference |
| Current Realtek Wi-Fi | **later only** | revision churn and weak public programming documentation; useful only after an exact module has an auditable path |

**INFERENCE:** ath9k is the best bounded native learning target, not the best user experience; AX200/AX210 is the best modern interoperability target through a contained Linux driver domain. A permissively tagged hardware-interface file does not relicense GPL framework dependencies or binary firmware.

## Bluetooth decomposition

### Controller transport

Most combo-card Bluetooth functions appear as USB devices. First support therefore depends on xHCI, USB enumeration, bulk/interrupt transfers, device-specific firmware upload, and reset. UART transports are a separate option but not the likely desktop path.

**OFFICIAL FACT:** USB-IF assigns class/subclass/protocol `e0/01/01` to the Bluetooth Programming Interface ([USB-IF class codes](https://usb.org/defined-class-codes)). **PROPOSED MALRYNTH DECISION:** bind the first generic transport by class tuple, then apply a narrow firmware/reset quirk only to a qualified VID:PID; do not make the current laptop's Intel ID a universal match.

### HCI

**OFFICIAL FACT:** Bluetooth Core 6.3 is current and publishes distinct HCI, L2CAP, ATT, GATT, GAP, security-manager and controller conformance material ([Bluetooth Core 6.3](https://www.bluetooth.com/specifications/specs/core-specification-6-3/)). HCI is the command/event/data boundary between host and controller. A minimal host needs command serialization, event parsing, ACL buffers/flow control, controller initialization, addresses and feature/version discovery.

### Host protocols

L2CAP, SDP (BR/EDR), ATT, GATT, SMP, security/pairing, and GAP sit above HCI. They are not controller-driver details.

### Profiles

- **first:** HID over GATT or classic HID for keyboard/mouse, after secure pairing/key storage;
- **next:** limited BLE GATT client/device discovery;
- **later:** file/device services;
- **much later:** A2DP/HFP and LE Audio, which add codecs, timing, audio routing, policy, and often patent/licensing considerations.

Bluetooth Core 6.3 being published does not mean R3 must implement its newest optional features. Negotiate features and target a small interoperable baseline. **INFERENCE:** HID-over-GATT is not delivered merely by an HCI USB driver; secure pairing, L2CAP, ATT/GATT, service discovery, bond storage and an HID translation layer are all exit criteria.

## Security and privacy gates

- no transmission before regulatory domain is known and enforced;
- cryptographically strong random generation and protected credential/key storage;
- explicit UI consent for pairing and trust;
- randomized addresses and scan privacy policy;
- firmware provenance/hash/version records;
- fuzz command/event, 802.11 management, HCI, L2CAP, ATT/GATT parsers;
- controller reset/revocation when a driver domain or service crashes.

## Port strategy

**PROPOSED MALRYNTH DECISION:** Wi-Fi is **PORT LARGE DRIVER or USE DRIVER DOMAIN TEMPORARILY** only after a Malrynth wireless core/regulatory/supplicant plan exists. Directly porting iwlwifi alone is insufficient because it expects mac80211/cfg80211, a firmware loader, timers, work queues, DMA, NAPI-like receive handling and userspace `nl80211` policy. Start native feasibility with ath9k, but treat its Linux implementation as GPL evidence, not a copy source.

Bluetooth transport is **WRITE NATIVE / PORT ALGORITHM/LOGIC**; the host stack can reuse protocol logic only from files with compatible provenance after audit. BlueZ provides strong behavioral evidence but mixes GPL-2.0 and LGPL-2.1 material ([BlueZ repository](https://github.com/bluez/bluez)); repository-level “LGPL” is not permission to copy arbitrary daemon/profile code.

A Linux driver domain is most credible for Wi-Fi during bootstrap: passthrough the whole replaceable adapter with IOMMU isolation and export virtio-net. It still adds Linux boot/firmware/attack surface and makes radio/regulatory policy depend on the domain, so it cannot be the default native architecture.

## Current laptop

**COMMUNITY EVIDENCE:** local inventory reports an Intel Wireless-AC 9560 CNVi function and Intel USB Bluetooth function. This is useful for negative/secondary tests, but local PCI/USB enumeration is not vendor authority for a family-wide ID claim. CNVi is deliberately excluded from the first Wi-Fi target.

## Recommended integration

When R3 begins, architecture review must define radio-regulatory authority, supplicant/service placement, key storage, firmware distribution, and crash recovery before selecting a device driver.

## Source ledger contributions

| Authority | Accessed | Claim supported | URL | Licensing relevance |
|---|---|---|---|---|
| Linux Wireless project | 2026-08-19 | ath9k AR9280/AR9380 support and mac80211 dependency | https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath9k.html | Linux driver is GPL; use behavior unless GPL port is approved. |
| Intel | 2026-08-19 | AX200 conventional PCIe Wi-Fi plus USB Bluetooth interface | https://www.intel.com/content/www/us/en/products/sku/189347/intel-wifi-6-ax200-gig/specifications.html | Vendor product fact; firmware has separate redistribution terms. |
| Linux Wireless/Intel | 2026-08-19 | iwlwifi/firmware/mac80211/cfg80211/userspace coupling | https://wireless.docs.kernel.org/en/latest/en/users/drivers/iwlwifi/core_release.html | Host code GPL; firmware is binary under separate Intel terms. |
| MediaTek/Linux kernel project | 2026-08-19 | MT7921 PCI host implementation and file license | https://github.com/torvalds/linux/blob/master/drivers/net/wireless/mediatek/mt76/mt7921/pci.c | Cited file `BSD-3-Clause-Clear`; audit GPL framework and firmware dependencies. |
| Linux Wireless project | 2026-08-19 | ath9k_htc concrete USB IDs and open firmware requirement | https://wireless.docs.kernel.org/en/latest/en/users/drivers/ath9k_htc/devices.html | Host driver GPL; open firmware has its own license/provenance. |
| Linux Wireless project | 2026-08-19 | Regulatory architecture and reusable ISC wireless-regdb | https://wireless.docs.kernel.org/en/latest/en/developers/regulatory.html | wireless-regdb ISC; retain notice and build trusted update/signing policy. |
| hostap project | 2026-08-19 | wpa_supplicant security/policy implementation and BSD license | https://android.googlesource.com/platform/external/wpa_supplicant_8/+/master/README | BSD reuse candidate; retain notice and audit crypto/dependencies. |
| USB Implementers Forum | 2026-08-19 | Bluetooth USB class tuple `e0/01/01` | https://usb.org/defined-class-codes | Classification fact; no source-code grant. |
| Bluetooth SIG | 2026-08-19 | Current Core 6.3 and host/controller protocol layers | https://www.bluetooth.com/specifications/specs/core-specification-6-3/ | Specification/qualification/trademark terms apply; not a code license. |
| BlueZ project | 2026-08-19 | Mature Bluetooth stack/profile implementation and mixed licenses | https://github.com/bluez/bluez | GPL-2.0/LGPL-2.1 mix; audit at file/dependency level before reuse. |
