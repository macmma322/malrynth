# Application Map

**Status:** PROPOSED — a roadmap, not an inventory. **Nothing here exists.**

This document exists so the intended first-party ecosystem is recorded *without* generating
hundreds of empty crates. Per ADR-0001, applications will live in one workspace, created
when development actually reaches them. A directory per unwritten application would be
scaffolding that has to be maintained, searched, and eventually deleted.

## Shared foundation

All first-party applications share the Malrynth UI toolkit, runtime APIs, capability
definitions, media framework, accessibility primitives, localisation, packaging, CI and test
infrastructure. **That shared foundation is precisely why they belong in one workspace and
not one repository each.**

## Catalogue

| Group | Applications | Earliest |
|---|---|---|
| **System** | Files, Settings, Search, Terminal, Monitor, Devices, Store, Shield, Recovery, Backup, Vault | M7 (Files, Settings, Search, Terminal, Monitor, Shield baseline) |
| **Communication** | Browser, Mail, Calendar, Contacts, Tasks, Link | post-M7 |
| **Media** | Photos, Video, Music, Camera, Recorder, Capture, Canvas, Broadcast | post-M7 |
| **Productivity** | Notes, PDF, Write, Sheets, Present | post-M7 |
| **Developer** | Studio, Data, API, Profiler, SDK/DDK tools | M7 (SDK/DDK tools only) |
| **Enterprise** | Organizations, collaboration, MDM, work profiles, EDR, fleet management | far post-M7 |
| **Cloud** | Account, Store entitlements, Sync, Backup, device restoration | far post-M7 |

## Principles

1. **First-party applications are replaceable** (Constitution §7). Each is the default, not
   the only option, and none receives a private API or a capability a third party could not
   obtain for the same function.
2. **Every application is capability-confined.** Files gets storage capabilities; it does not
   get ambient filesystem authority.
3. **Applications do not ship in `core/`.** They compose into products (see
   `docs/architecture/PRODUCT-COMPOSITION.md`).

## Likely first split candidates

Under ADR-0001's criteria, the applications most likely to eventually earn their own
repository are **Browser** (a vendored engine would bring enormous history and distinct
license obligations — criteria F and G) and **Studio**. Every other application is expected
to remain in the shared workspace indefinitely.
