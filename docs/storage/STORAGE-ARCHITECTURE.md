# Storage Architecture

**Status:** PROPOSED. Target: M5.

## Layering

```
application ──> storage client API (capability handles)          L5/L6
                    │
              VFS protocol                                        L3
                    │
    ┌───────────────┼───────────────┬──────────────┐
 bootstrap FS   MalrynthFS      FAT/exFAT      ext / NTFS
 (read-only)    (research)      (interop)      (ported, RO first)
    └───────────────┴───────────────┴──────────────┘
                    │
             volume manager (GPT, encryption)                     L3
                    │
               block layer                                        L3
                    │
        storage drivers (NVMe, AHCI)                              L4
```

## Core rule

> **The kernel never parses on-disk structures from an untrusted volume.**

Filesystem implementations are user-space services. A malformed NTFS or ISO image crashes an
unprivileged filesystem process, not the kernel. This is one of the most reliably exploited
paths in every mainstream OS and one Malrynth can close by construction — see
[`KERNEL-BOUNDARY.md`](../architecture/KERNEL-BOUNDARY.md).

## Capability-oriented access

There is no global filesystem an application can name. A process holds directory and file
capabilities:

```
root directory capability  ── system services only
user documents             ── granted by the user via the picker
app-private storage        ── granted at launch by Component Manager
removable volume           ── explicit grant, revocable on eject
```

`open("/etc/passwd")` in ported software resolves through the POSIX facade against the
capabilities the process actually holds, and fails cleanly when it holds none
([`POSIX-STRATEGY.md`](../runtime/POSIX-STRATEGY.md)).

## Encryption

Full-disk encryption uses reused, audited cryptographic primitives with Malrynth-owned key
management via Vault and TPM binding. Per-file or per-directory encryption is a later
refinement. **Malrynth writes no cryptographic algorithms** ([`BUILD-VS-REUSE-MATRIX.md`](../architecture/BUILD-VS-REUSE-MATRIX.md)).

## Snapshots and recovery

Snapshots are a security mechanism, not only convenience: ransomware defence depends on
**applications being unable to delete protected snapshots even for files the user owns**
(Constitution, [`SHIELD-ARCHITECTURE.md`](../security/SHIELD-ARCHITECTURE.md)). That requires
snapshot deletion to be a capability no ordinary application ever receives.

Recovery must work **offline** with no account and no server (Constitution §11).

## Removable media

Untrusted by default. An inserted USB volume is not automatically mounted with full trust; its
filesystem parser runs sandboxed, and access is a user-visible grant.
