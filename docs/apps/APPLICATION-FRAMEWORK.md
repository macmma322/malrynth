# Application Framework

**Status:** PROPOSED. Target: M7.

## Purpose

The framework is what makes writing a *correct* Malrynth application the path of least
resistance. If accessibility, localisation, crash handling and capability hygiene are opt-in,
most applications will not have them.

## Responsibilities

| Concern | Framework provides | App provides |
|---|---|---|
| **Lifecycle** | Start, activate, suspend, resume, terminate hooks | Behaviour per transition |
| **Activation** | Typed activation carrying its capability (file, URI, notification, background) | Handling per kind |
| **UI** | Toolkit, layout, theming, adaptive breakpoints | Its interface |
| **Settings** | Typed per-app store, automatically scoped | Schema |
| **Localisation** | Catalogues, formatting, RTL, pluralisation | Translatable strings |
| **Accessibility** | Semantics from standard controls, AT bridge | Labels for custom controls |
| **Storage** | Handles for config/data/cache; picker integration | What to store |
| **Logging/tracing** | Structured, capability-scoped | What to log |
| **Crash handling** | Capture, minidump, restart policy | Recovery behaviour |
| **Notifications** | Post, update, revoke; user-visible policy | Content |
| **Permissions** | Portal integration, grant state, revocation handling | **Behaving correctly when denied** |
| **Media** | Playback, capture sessions, routing | Content |
| **IPC** | Typed protocol clients/servers | Its protocols |
| **Update/migration** | Version detection, data migration hooks | Migration logic |

## The rule that matters most

**A denied capability is a normal state, not an error path bolted on at the end.** The
framework makes the "no camera capability" branch as easy to write as the happy path —
otherwise apps will demand capabilities defensively at install time, and the model collapses
into Android-style permission fatigue.

## Application classes

The framework serves all classes from [`NATIVE-APPLICATION-MODEL.md`](NATIVE-APPLICATION-MODEL.md).
Ordinary classes differ in manifest and defaults, not in privilege; only an enumerated
**privileged system role** carries authority an ordinary application cannot request:

| Class | Framework surface |
|---|---|
| Ordinary app | Full |
| System app | Full; larger manifest, **no private API** |
| System role holder | Full; plus the narrow authority of the role it holds, and nothing beyond it |
| Privileged service | Headless subset: lifecycle, IPC, logging |
| Background service | Headless + budget awareness |
| Driver | Driver framework instead ([`DDK-ARCHITECTURE.md`](../sdk/DDK-ARCHITECTURE.md)) |
| CLI | Minimal: lifecycle, storage, logging |
| Compatibility process | Not framework-based; hosted by its personality layer |

## Quality contract

From the founder vision, enforced by framework defaults and Store review rather than hope:

```
fast launch · low idle memory · works offline · keyboard-first
accessible · no ads · no mandatory account · clean uninstall
no unnecessary background service
```

Several are measurable and become gates in
[`PERFORMANCE-CONSTITUTION.md`](../performance/PERFORMANCE-CONSTITUTION.md).

## Non-goal

The framework is **not** a required runtime. A native application may use `libmalrynth` and
the protocols directly — necessary for ported software, compatibility layers and language
runtimes. The framework is the ergonomic default, not a gate.
