# Native Application Model

**Status:** PROPOSED. Connects [ADR-0004](../adr/ADR-0004-kernel-object-model.md)'s kernel
objects to something an application developer can reason about.

## The governing rule

> **An application starts with minimal authority. Running "as Nikolay" does NOT mean it can
> read everything Nikolay owns.**

This is the single most consequential difference between Malrynth and every mainstream desktop
OS, and it is the thing most easily lost by accident.

## What an application is at start

```
Process
├── private address space
├── read-only package content
├── private config / data / cache
├── one channel to the Component Manager
└── NOTHING ELSE
```

No filesystem. No network. No devices. No other processes. No global namespace to name.

Everything else arrives as an explicit capability — from the manifest at launch, from user
action at runtime, or from policy.

## Concept mapping

| Concept | Kernel object | How an app obtains it |
|---|---|---|
| Application identity | — | Package manifest; assigned by the system, unforgeable |
| Process | `Process` | Created by Component Manager with an explicit handle set |
| Thread | `Thread` | Created within its own process |
| Window | compositor `Surface` | Compositor grants on request; not a kernel object |
| File | VFS handle over `Channel` | User picks, or directory capability, or app-private storage |
| Directory | directory capability | User picks; persists if the user chose that |
| Socket | socket capability | Socket broker, gated by manifest + policy |
| Settings | settings capability | Framework provides per-app scope automatically |
| Secret | Vault handle | Vault; never plaintext to the app |
| Notification | notification capability | Manifest-declared, user-revocable |
| Camera / microphone | device capability | Runtime grant, revocable, with a system indicator |
| GPU | GPU context | Graphics framework, mediated |
| Background work | job budget | Component Manager, budgeted and revocable |

## Application classes

Different classes get different *default* authority. None gets ambient authority.

| Class | Examples | Defaults |
|---|---|---|
| **Ordinary application** | Notes, Photos, third-party apps | Minimal; everything by grant |
| **System application** | Files, Settings, Monitor | More manifest-declared capabilities — **and no private API a third party could not obtain** (Constitution §7) |
| **Privileged service** | Component Manager, device manager | Broad capabilities; still ring 3, still unprivileged |
| **Background service** | indexer, sync agent | No UI; budgeted; suspendable |
| **Driver** | NVMe, xHCI | Device capabilities only ([`DRIVER-MODEL.md`](../architecture/DRIVER-MODEL.md)) |
| **CLI tool** | shell utilities | Inherits the shell's *explicitly passed* capabilities |
| **Compatibility process** | Linux/Windows app under a personality | Capabilities held by the personality layer on its behalf |
| **System role holder** | Recovery, Shield containment, updater, package service, firmware service, login/session | Holds one of the enumerated **privileged system roles** below — narrow, explicit and auditable |

**Being first-party is not a privilege.** For *ordinary* applications the rule is parity: an
equivalent third-party application can request equivalent ordinary capabilities. If Files can do
something a third-party file manager cannot, that is a bug against the constitution.

### Privileged system roles

Parity is a rule about *ordinary* capabilities. A small, **enumerated** set of system roles
carries authority that is deliberately unavailable to arbitrary applications, because the role is
part of the system's trust base rather than part of its application surface:

| Role | Why it cannot be an ordinary capability |
|---|---|
| **Recovery** | Must act when the running system is untrusted, including on protected snapshots |
| **Shield containment** | Freezes processes and revokes their authority; an ordinary app holding it could disable security |
| **Update authority** | Determines what system code becomes the next boot |
| **Package authority** | Determines what installs, and which signatures are accepted |
| **Firmware management** | Writes persistent pre-OS state |
| **Login / session infrastructure** | Owns credential entry and the session's root of trust |

Four rules keep this a distinction rather than a loophole:

1. **Role-based, never identity-based.** Authority attaches to the *role*, not to who wrote the
   application. A third-party implementation appointed to a role receives exactly the same
   authority; a first-party application not holding the role receives none.
2. **Explicit and narrow.** Each role is a named, enumerated capability set. Nothing is ever
   "trusted" as a general property.
3. **Auditable.** Exercise of role authority is observable through `SecurityEventStream`, and the
   current set of role holders is visible to the user.
4. **Not a bypass.** A role confers its own authority and nothing else. It never grants ambient
   authority and never widens the ordinary capability surface.

**Being first-party is not itself a role, and a role is not a reward for being first-party.**
Conflating the two is precisely how "system app" becomes a privilege ladder on other platforms.

## Lifecycle

```
installed → activated (launch, file open, URI, notification, background trigger)
   → running → suspended (no CPU, memory retained)
   → hibernated (state serialised, memory reclaimed)   [later]
   → terminated
```

Activation is **explicit and typed**: an app knows *why* it started, which is what allows a
file-open activation to carry exactly one file capability rather than a path string the app
must go and resolve.

## What the app never gets

- The ability to enumerate other processes' memory or handles
- Ambient filesystem access
- A registry-equivalent global mutable namespace
- A per-app background update service
- The ability to delete protected recovery snapshots — **even for files the user owns**

## Uninstall

Deterministic by construction, because state is partitioned by lifetime
([`APP-STATE-MODEL.md`](../packages/APP-STATE-MODEL.md)): remove package, cache and app data;
optionally keep user-created documents. Nothing is scattered outside those locations, because
the app never had the authority to write anywhere else.
