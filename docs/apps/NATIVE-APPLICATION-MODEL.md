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

**A first-party app is an ordinary app with a bigger manifest, not a privileged one.** If
Files can do something a third-party file manager cannot, that is a bug against the
constitution.

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
