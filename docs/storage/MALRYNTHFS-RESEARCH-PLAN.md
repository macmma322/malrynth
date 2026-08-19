# MalrynthFS Research Plan

**Status:** EXPERIMENTAL — research only. **No milestone depends on it. It must not hold data
anyone values.**

## Long-term goals

64-bit extent/object addressing · copy-on-write metadata · atomic root commit · checksummed
metadata **and** data · snapshots · reflinks · transparent compression · sparse files · quotas
· TRIM/discard · online scrub and repair · replication/send · large-directory scalability ·
case-sensitive native semantics with optional compatibility case-folding · encryption
integration · storage pools eventually.

## Transaction model

```
transaction begins
   → allocate new metadata blocks (never overwrite in place)
   → write data/extents
   → persist checksums
   → persist new B-tree roots
   → atomically advance the superblock root pointer
```

Power loss before the root commit leaves the previous committed root authoritative. That
single property is what makes crash consistency provable rather than hoped for.

## Testing is the project

**A production filesystem cannot be tested by copying ISO files around.** The core of this
research is a test harness, not a filesystem:

1. **Simulated block device that can crash after every persistence event.**
   ```
   write metadata block 928 → FLUSH → write root block → <POWER LOSS>
   → restart → mount → verify invariants → repeat, millions of times
   ```
2. **Reference-model testing** — compare against a simple in-memory model.
3. **Fault injection** — I/O errors, torn writes, bit rot, reordering.
4. **Fuzzing** — malformed on-disk structures, always parsed unprivileged.
5. **Rust typestate** to encode ordering constraints at compile time (SquirrelFS-inspired).

## Promotion path

```
disk image → VM test volume → developer scratch drive → non-critical physical volume
   → developer home volume → certified optional consumer volume
   → default (only after multi-year qualification)
```

Each stage requires evidence, not confidence. Skipping a stage because the previous one "went
fine" is exactly how filesystems lose data.
