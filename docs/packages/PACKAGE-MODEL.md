# Package Model

**Status:** PROPOSED. Target: M5.

## Four separate concepts

The most common packaging mistake is collapsing these. Malrynth keeps them distinct:

| Concept | Question | Mechanism |
|---|---|---|
| **Identity** | Who is this, and who published it? | Package ID + publisher identity + signature |
| **Content** | What bytes? | Content-addressed blobs (Merkle root) |
| **Authority** | What may it do? | Capability manifest — **independent of identity** |
| **State** | What has it accumulated? | Partitioned per lifetime ([`APP-STATE-MODEL.md`](APP-STATE-MODEL.md)) |

> **A signature proves who published these bytes. It does not mean the application may read
> everything.** Conflating signing with permission is how "trusted publisher" becomes
> "unlimited authority".

## Structure

```
package.mpk
├── manifest              identity, version, ABI, entry points, capabilities, protocols
├── content index         blob hashes (Merkle root)
├── SBOM                  components and licences
├── provenance            how/where/when built (SLSA-style)
├── signature(s)          publisher, optionally Store countersignature
└── repository metadata   update source, channel
```

Large content lives in a **content-addressed store**, not inside the archive:

```
manifest ──> hash A ──> executable (ELF)
             hash B ──> shared object
             hash C ──> icon
             hash D ──> font    ← shared by every package that references it
```

Deduplication falls out for free, integrity is verifiable per blob, and activation becomes
atomic: an update is complete when the new root is written, and a partially downloaded update
is simply not referenced.

`.mpk` is a **distribution container, not a machine-code format** — the blobs are ordinary ELF
([`EXECUTABLE-MODEL.md`](../runtime/EXECUTABLE-MODEL.md)).

## Identity

- **Package ID**: reverse-DNS, `com.example.photoeditor` ([`naming.md`](../specs/naming.md)).
- **Publisher identity**: a key, plus optional verified metadata.
- **Application ID**: equals the package ID of the providing package.

Package ID and publisher key are bound at first install; a package cannot silently change
publisher.

## Dependencies

Malrynth avoids both extremes — statically bundling everything, and one mutable shared `/usr/lib`:

```
application
   ├─> Malrynth Platform ABI    (stable, system-provided)
   ├─> versioned framework runtimes  (side-by-side: "Runtime UI 5")
   └─> app-private libraries     (bundled in the package)
```

Multiple runtime versions coexist, so the system can move forward without recreating
dependency hell.

## Signing

Signing is a **package** property. See [`UPDATE-MODEL.md`](UPDATE-MODEL.md) for the TUF-style
repository roles and threshold model. Sideloading remains possible (Constitution §5) — the
system may require an explicit informed action, never make it impossible.

## Non-goals

- No registry-equivalent global mutable namespace.
- No per-application background updater.
- No install-time scripts running with elevated authority. **Installation is declarative**:
  the manifest states what is needed; the system does it. Arbitrary install scripts are the
  main way package systems become privilege-escalation vectors.
