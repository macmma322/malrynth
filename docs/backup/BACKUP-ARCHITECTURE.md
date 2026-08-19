# Backup Architecture

**Status:** PROPOSED. Target: post-M7.

## Principles

1. **Backup is independent of Sync** ([`SYNC-ARCHITECTURE.md`](../cloud/SYNC-ARCHITECTURE.md)).
2. **Local backup requires no account and no Internet** (Constitution §3).
3. **Backups resist ransomware** — this is a security mechanism, not only convenience.
4. **A backup that has never been restored is a hypothesis.** Restore testing is part of the product.

## Targets

| Target | Account needed | Notes |
|---|---|---|
| Local external drive | No | The baseline; must work standalone |
| Network share / NAS | No | Local network only |
| Malrynth Cloud Backup | Yes | Optional, E2E encrypted |
| Third-party provider | Depends | Provider interface, not a closed system |

## Ransomware resistance

The mechanism that makes this work is architectural rather than heuristic:

- Backup and snapshot deletion is a **capability no ordinary application receives** — even for
  files the user owns.
- Protected snapshots are immutable for their retention window.
- The backup service holds capabilities applications cannot obtain.
- Offline/rotated targets are supported and encouraged, because online backup alone is
  reachable by an attacker with sufficient authority.

## Scope

```
included   /config  /data  user documents  system configuration  package list
excluded   /cache  /temp  reconstructible content  swap
choice     large media libraries, VM images
```

Restoring the **package list** rather than package binaries is deliberate — see
[`DEVICE-RESTORE.md`](../cloud/DEVICE-RESTORE.md).
