# Hardware support database schema

## Purpose

The future database records evidence for exact hardware and firmware revisions. It must distinguish `investigated`, `boots`, `driver-probed`, `passes-profile`, and `certified`; it must never convert “Linux supports it” into “Malrynth supports it.”

`INVESTIGATED-HARDWARE.json` is a small research seed using this schema. It contains only devices examined for this report or present in the read-only host inventory. Its `test` objects record completion of inventory or document review; they are not qualification records or Malrynth support claims.

## Dataset wrapper

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | schema compatibility, initially `0.1.0` |
| `generated` | date | date this research snapshot was generated |
| `status_notice` | string | mandatory warning that investigated is not supported or certified |
| `records` | array | investigated device/system records described below |

## Device record

| Field | Type | Meaning |
|---|---|---|
| `record_id` | string | stable Malrynth identifier; not a product name |
| `kind` | enum | `system`, `motherboard`, `cpu`, `pci`, `usb`, `storage`, `firmware`, `adapter` |
| `vendor`, `product`, `marketing_family` | strings | names exactly as observed and broader family |
| `hardware_revision` | string/null | board/silicon revision; null means unknown, never wildcard |
| `identity` | object | bus-specific IDs below |
| `firmware` | array | component, version, hash, source, license/redistribution status |
| `topology` | object | parent bus/port/slot, multifunction siblings, bridges/hubs, IOMMU group |
| `driver` | object | intended driver, strategy, status, source revision, license audit |
| `test` | object | profile, state, date, build, environment, results, artifact links |
| `capabilities` | object | only observed/spec-cited features, each with evidence |
| `quirks` | array | scoped condition, symptom, mitigation, source, validation state |
| `power` | object | D-states/suspend/reset tested and result |
| `iommu` | object | remapping unit, group, DMA mask, interrupt remapping, fault test |
| `security` | object | firmware provenance, secure boot/TPM relation, known isolation limits |
| `availability` | object | status, replaceability, date checked; no volatile prices required |
| `sources` | array | source IDs/URLs plus claim and evidence class |
| `notes` | array | explicitly non-normative observations |
| `last_reviewed` | date | last evidence review |

## Identity object

```json
{
  "pci": {
    "vendor_id": "8086",
    "device_id": "1533",
    "subsystem_vendor_id": null,
    "subsystem_device_id": null,
    "revision_id": null,
    "class_code": "020000"
  },
  "usb": {
    "vendor_id": null,
    "product_id": null,
    "bcd_device": null,
    "interface_classes": []
  },
  "storage": {
    "model": null,
    "serial_redacted": true,
    "controller_pci_id": null,
    "namespace_id": null,
    "lba_size": null
  },
  "dmi": {
    "system_vendor": null,
    "product_name": null,
    "board_vendor": null,
    "board_name": null
  }
}
```

IDs are lowercase four-digit hexadecimal without `0x`. Unknown fields are `null`; do not use zero or empty string.

## Driver status state machine

```text
investigated
  -> modelled-in-emulator
  -> enumerated
  -> initialized
  -> basic-io
  -> recovery-tested
  -> profile-passed
  -> reference-supported
  -> certified   (future process, never assigned by R0 research)
```

States may regress when firmware, driver, or test profile changes. `reference-supported` is scoped to exact identity plus minimum/maximum tested firmware, not a marketing family.

## Qualification test record (future)

The following fields are required when a record claims a Malrynth test-profile result such as `boots`, `basic-io`, `profile-passed`, or `reference-supported`. Research-only seed records may instead use the preliminary fields `profile`, `state`, `date`, nullable `malrynth_build`, and `results`; `state: complete` there means only that the named inventory or document review finished.

Required fields:

- Malrynth commit and build artifact hash;
- exact machine/board and firmware record IDs;
- settings-profile hash;
- cold/warm boot count as raw artifact data, not a marketing percentage;
- every mandatory R0 check with `pass`, `fail`, `blocked`, or `not_applicable`;
- serial log, ACPI table hashes, PCI inventory, IOMMU dump, device logs;
- tester and timestamp;
- destructive-test declaration and backup confirmation for storage.

## Source/evidence record

```json
{
  "evidence_class": "OFFICIAL FACT",
  "authority": "Intel",
  "title": "Intel Ethernet Controller I210 Datasheet",
  "url": "https://www.intel.com/content/www/us/en/content-details/333016/intel-ethernet-controller-i210-datasheet.html",
  "accessed": "2026-08-19",
  "claim": "External architecture and register definitions are public",
  "license_relevance": "Specification review; implementation rights must follow its terms"
}
```

## Privacy

Public exports redact full storage serials, MAC addresses tied to owned systems, firmware secrets, Wi-Fi SSIDs/BSSIDs, and keys. Hashes should use a documented algorithm. Photos must be scrubbed for serial labels unless needed in a private artifact store.

## Recommended integration

Implement validation tooling later, after repository ownership is decided. Do not grow the seed into an unverified compatibility list.
