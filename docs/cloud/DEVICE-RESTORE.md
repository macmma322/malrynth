# Device Restore

**Status:** PROPOSED. Target: post-M7.

## Principle

> **Restore intent, not stale binaries.**

Restoring a device is not copying an old disk onto new hardware. That is how a restored machine
inherits drivers for hardware it does not have, a kernel from two years ago, and accumulated
state nobody wanted.

## What is restored

| Restored | Not restored |
|---|---|
| Settings and preferences | Old kernel or system binaries |
| The **list** of installed applications | Old application binaries |
| Application data (per app, user choice) | Caches, temp files |
| Secrets, via Vault re-authentication | Raw secret material |
| Files and documents | Hardware-specific driver binaries |
| Device and network configuration | Stale hardware profiles |

## Flow

```
new device → identity → fetch manifest → resolve packages FOR THIS HARDWARE
   → install current versions → restore config and data → re-authenticate secrets
   → device usable
```

Applications arrive as **current versions built for the actual hardware**, so a restored device
is a correctly configured new device rather than a resurrected old one.

## Offline restore

Restore must work from a **local backup with no account and no network** (Constitution §11).
Cloud restore is a convenience, never the only path — an OS whose recovery depends on a server
that might not exist in ten years is not owned by its user.

## Partial restore

Selective restore is a first-class case: settings only, files only, a single application. A
restore that is all-or-nothing forces users to re-import problems they were trying to leave
behind.
