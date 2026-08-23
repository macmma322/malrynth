# VFS Architecture

**Status:** PROPOSED. Target: M5.

## What is different here

A conventional VFS resolves paths against a global namespace. Malrynth's VFS resolves
operations against **capabilities**, so there is no global root to reach.

```
client holds: directory capability for /home/nikolay/Projects
   open("malrynth/README.md")  → resolved RELATIVE to that capability
   open("../../.ssh/id_ed25519") → REFUSED: escapes the capability
```

Path traversal is not a bug class to defend against — it is structurally impossible, because
there is nothing above the capability to traverse to.

## Protocol shape

A typed IPC protocol, not a syscall surface:

| Operation group | Notes |
|---|---|
| Directory | enumerate, open child, create, remove, rename within a capability |
| File | read, write, truncate, seek, metadata; bulk data via memory objects, never channel copies |
| Watch | change notification as an explicit capability |
| Extended metadata | tags, provider-specific attributes |
| Transactions | where the filesystem supports them |

**Enumeration returns metadata cheaply and defers everything expensive.** This is what makes
the Files invariant achievable ([`FILES-ARCHITECTURE.md`](../apps/files/FILES-ARCHITECTURE.md)).

## Providers

The same protocol serves local filesystems, network shares, archives, disk images and
synthetic providers. A provider is an ordinary unprivileged service holding capabilities to
whatever it needs — so an archive browser is not a special case in the VFS, it is just another
provider.

## Performance

Bulk data moves through shared memory objects; the channel carries control only
([`IPC-MODEL.md`](../architecture/IPC-MODEL.md)). A read does not copy the file through the
kernel — it transfers a handle to pages. This is the difference between a microkernel VFS that
is usable and one that is a benchmark embarrassment.
