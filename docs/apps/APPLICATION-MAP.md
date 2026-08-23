# Application Map

**Status:** PROPOSED — a roadmap, not an inventory. **Nothing here exists.**

This document records the intended first-party ecosystem *without* generating empty crates.
Per [ADR-0001](../adr/ADR-0001-repository-topology.md), applications live in one workspace,
created when development reaches them. A directory per unwritten application is scaffolding
that must be maintained, searched and eventually deleted.

## Shared foundation

All first-party applications share the UI toolkit, runtime APIs, capability definitions, media
framework, accessibility primitives, localisation, packaging, CI and test infrastructure.
**That is precisely why they belong in one workspace and not one repository each.**

## Rules that apply to every row

1. **Replaceable.** Every first-party app is the default, never the only option.
2. **No private API.** For ordinary application capabilities, parity holds: an equivalent
   third-party application can request equivalent capabilities (Constitution §7). If Files can do
   something a third-party file manager cannot, that is a bug. The narrow exception is the
   enumerated **privileged system roles** — Recovery, Shield containment, update authority,
   package authority, firmware management, login/session infrastructure — which are role-based,
   explicit and auditable, and are **never** granted merely for being first-party
   ([`NATIVE-APPLICATION-MODEL.md`](NATIVE-APPLICATION-MODEL.md)).
3. **Offline-first.** Core function works with no network and no account.
4. **Quality contract.** Fast launch · low idle memory · offline · keyboard-first · accessible
   · no ads · no mandatory account · clean uninstall · no unnecessary background service.
5. **Custom UI, reused engines.** A Malrynth-native application may reuse audited libraries for
   codecs, formats and rendering. Writing a JPEG decoder or a TLS stack from scratch is not
   what "native" means.

## System

| App | Purpose / why it exists | Milestone | Key dependencies | Privileges | Offline | Build vs reuse |
|---|---|---|---|---|---|---|
| **Files** | File management. **The benchmark for platform quality** — if Files is slow, the platform is slow | **M7** | VFS, UI, thumbnailers, search | Storage caps + picker role | Full | Custom; reused format parsers, sandboxed |
| **Settings** | System configuration and the **capability review surface** | **M7** | Settings service, UI, all subsystems | Settings + policy caps | Full | Custom |
| **Search** | Local index across files, apps, settings | **M7** | Index service, VFS | Storage caps, scoped | Full | Custom; reused text extractors |
| **Terminal** | Shell access; essential for a developer OS | **M7** | PTY-equivalent, shell, text | Process creation caps | Full | Custom |
| **Monitor** | Processes, resources, **capability grants**, network flows | **M7** | Tracing, component mgr | Read-only introspection | Full | Custom |
| **Devices** | Hardware inventory, driver state, firmware | later | Device manager | Device introspection | Full | Custom |
| **Store** | Optional distribution channel | later | Packages, account | Package install (user-confirmed) | Browse offline; install needs network | Custom |
| **Shield** | Security posture, detections, containment | M7 baseline | Security event stream, scanners | Security caps | Full | Custom UI; reused scan engines |
| **Recovery** | Offline repair, rollback, restore | **M5** | Boot, storage, snapshots | Runs outside normal session | **Must be full** | Custom |
| **Backup** | Local and optional cloud backup | later | Storage, snapshots, crypto | Backup caps apps cannot obtain | Local: full | Custom; reused crypto |
| **Vault** | Credential and secret management | later | Crypto, TPM | Hardware-backed isolation | Full | Custom; reused crypto |

## Communication

| App | Purpose | Milestone | Dependencies | Privileges | Offline | Build vs reuse |
|---|---|---|---|---|---|---|
| **Browser** | Web access with Malrynth privacy and capability integration | post-M7 | **Reused engine**, GPU, net, Vault | Ordinary app; web permissions map to platform capabilities | Cached only | **Custom UI over a reused engine** ([`BROWSER-STRATEGY.md`](browser/BROWSER-STRATEGY.md)) |
| **Mail** | Email client | post-M7 | Net, storage, contacts | Network + storage caps | Read cached | Custom; reused MIME/crypto |
| **Calendar** | Scheduling | post-M7 | Storage, net, notifications | Storage + optional network | Full local | Custom; reused iCal |
| **Contacts** | Address book | post-M7 | Storage, sync | Storage caps | Full | Custom |
| **Tasks** | Task management | post-M7 | Storage, sync | Storage caps | Full | Custom |
| **Link** | Cross-device continuity | post-M7 | QUIC, crypto, discovery | Per-feature device caps | LAN works offline | Custom ([`LINK-PROTOCOL-ARCHITECTURE.md`](../link/LINK-PROTOCOL-ARCHITECTURE.md)) |

## Media

| App | Purpose | Milestone | Dependencies | Privileges | Offline | Build vs reuse |
|---|---|---|---|---|---|---|
| **Photos** | Library, viewing, light editing | post-M7 | Media framework, GPU, index | Storage caps | Full | Custom; **reused codecs** |
| **Video** | Playback | post-M7 | Video pipeline, GPU | Storage caps | Full | Custom; reused codecs |
| **Music** | Audio library and playback | post-M7 | Audio graph, index | Storage + background audio | Full | Custom; reused codecs |
| **Camera** | Capture | post-M7 | Camera service | `device.camera` + indicator | Full | Custom |
| **Recorder** | Audio recording | post-M7 | Audio graph | `device.microphone` + indicator | Full | Custom |
| **Capture** | Screenshots and screen recording | post-M7 | Compositor capture | `ui.capture.*` | Full | Custom |
| **Canvas** | Drawing and image editing | post-M7 | GPU, media, pen input | Storage caps | Full | Custom |
| **Broadcast** | Recording and streaming | post-M7 | Capture, audio graph, encode | Capture + encode caps | Recording offline | Custom ([`BROADCAST-ARCHITECTURE.md`](broadcast/BROADCAST-ARCHITECTURE.md)) |

## Productivity

| App | Purpose | Milestone | Dependencies | Privileges | Offline | Build vs reuse |
|---|---|---|---|---|---|---|
| **Notes** | Quick notes | post-M7 | Storage, sync, text | Storage caps | Full | Custom |
| **PDF** | Viewing and annotation | post-M7 | Reused engine, text, print | Storage caps | Full | **Custom UI over a reused engine** |
| **Write** | Word processing | far post-M7 | Document engine, text | Storage caps | Full | Custom UI, **reused format engines** |
| **Sheets** | Spreadsheets | far post-M7 | Document engine | Storage caps | Full | Custom UI, reused format engines |
| **Present** | Presentations | far post-M7 | Document engine, GPU | Storage + display caps | Full | Custom UI, reused format engines |

Priority is deliberately **low**: reused engines and web alternatives cover this need for years,
and a mediocre first-party suite shipped to complete a checklist costs attention the kernel
needs ([`OFFICE-STRATEGY.md`](productivity/OFFICE-STRATEGY.md)).

## Developer

| App | Purpose | Milestone | Dependencies | Privileges | Offline | Build vs reuse |
|---|---|---|---|---|---|---|
| **SDK/DDK tooling** | `malrynth` CLI, packaging, signing | **M7** | Toolchain, packages | Developer caps | Full | Custom over reused LLVM/rustc |
| **Studio** | IDE — **explicitly optional** | post-M7 | UI, toolchain, debugger | Ordinary app | Full | Custom or reused editor core |
| **Data** | Database/data tooling | post-M7 | Storage, net | Ordinary app | Full | Custom |
| **API** | API client/testing | post-M7 | Net | Network caps | Partial | Custom |
| **Profiler** | Performance analysis | post-M7 | Tracing service | Tracing caps | Full | Custom |

**Malrynth Studio must be optional.** A developer using VS Code, JetBrains, Vim, Emacs or plain
CLI tooling is fully supported ([`SDK-ARCHITECTURE.md`](../sdk/SDK-ARCHITECTURE.md)).

## M7 Developer OS application set

Only these are required for the **M7 Developer OS** milestone:

```
Files · Settings · Search · Terminal · Monitor · package installer
Shield baseline · Recovery · SDK/DDK tooling
```

Everything else is post-M7. **The M7 Developer OS application set must not ship mediocre
applications merely to fill every checkbox** — a rule taken directly from the founder vision and
worth restating, because the pressure to fill the grid is constant.

M7 is the **Developer OS** gate, not a product-quality gate. **Malrynth Desktop 1.0 is a later,
separate gate** requiring hardware certification and a mature application ecosystem
([`MASTER-ROADMAP.md`](../roadmap/MASTER-ROADMAP.md)). Nothing here should be described as "v1".

## Likely first split candidates

Under ADR-0001's criteria, the applications most likely to eventually earn their own repository
are **Browser** (a vendored engine brings enormous history and distinct licence obligations —
criteria F and G) and **Studio**. Every other application is expected to remain in the shared
workspace indefinitely.
