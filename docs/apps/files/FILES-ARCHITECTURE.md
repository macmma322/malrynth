# Files Architecture

**Status:** PROPOSED. Target: M7.

Files is the benchmark application for platform quality. If Files is slow, the platform is
slow — there is nowhere for the blame to hide.

## The invariant

> **Enumerate → render immediately → enrich asynchronously.**

```
open folder
   → read directory entries          (fast, VFS)
   → RENDER NOW                      ← nothing blocks this
        ├── async thumbnails
        ├── async media metadata
        ├── async Git status
        ├── async Sync state
        ├── async folder sizes
        └── async semantic data
```

**Nothing on the enrichment path may delay first paint.** A folder with 100,000 files, a
malformed thumbnail, a slow USB stick or an offline network share must not stall the window.
This is the single most violated rule in file managers, and it is why the invariant is stated
before any feature.

## Every parser runs outside Files

Thumbnailers, metadata extractors and preview generators handle untrusted input, so they run
in separate sandboxed processes with narrow capabilities. A malicious image crashes a
thumbnailer, not the file manager, and certainly not the system.

## Search

The local index supports name, path, size, type, timestamps, tags, document text, media
metadata and optional semantic vectors — with **user-configurable scope**:

```
Documents      full          Projects   names + source
Pictures       metadata      node_modules  OFF
VM images      metadata only Private    OFF
```

**Search works without the Internet.** Semantic indexing is explicitly optional and off by
default — it is a capability, not an assumption.

## Providers

Local volumes, network shares, archives, disk images and cloud providers all appear through
the same VFS provider interface, so Files does not special-case them.

## File operations

Copy, move and delete must be **resumable, interruptible and correct across volumes**, with
conflict handling that never silently destroys data. Long operations are cancellable and
report honest progress.

## Capabilities

Files is a system application, and — per Constitution §7 — holds **no ordinary capability a
third-party file manager could not obtain**. It receives storage capabilities and the picker
role; that is all. If a competing file manager cannot be written, the platform has failed its own
rule.

**The picker role is a narrow platform role, not a privileged system role.** Providing the system
file picker means brokering a user's decision into a capability: the act of choosing *is* the
grant ([`APPLICATION-CAPABILITY-MODEL.md`](../APPLICATION-CAPABILITY-MODEL.md)). The picker
returns a handle to exactly what the user selected and acquires no ambient filesystem authority
of its own. That is what separates it from the high-authority roles in
[`NATIVE-APPLICATION-MODEL.md`](../NATIVE-APPLICATION-MODEL.md), and why it is deliberately not
one of them.
