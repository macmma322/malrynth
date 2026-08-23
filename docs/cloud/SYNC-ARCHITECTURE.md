# Sync Architecture

**Status:** PROPOSED. Target: post-M7.

## Sync is not Backup

| | Sync | Backup |
|---|---|---|
| Purpose | Same state on several devices | Recover from loss or mistake |
| History | Current state (+ limited versions) | Point-in-time, retained |
| Deletion | **Propagates** | Does not propagate |
| Failure mode | Deleting on one device deletes everywhere | Deleted data survives |

**Treating Sync as Backup is how people lose data**, because deletion and corruption replicate
faithfully. They are separate services with separate storage and separate policies, and the UI
must never blur them.

## Per-category and opt-in

```
Settings          ☐        Passwords/passkeys  ☐ (Vault, E2E)
Files             ☐        Application data    ☐ per app
Photos            ☐        Browser data        ☐
Notes             ☐        Device list         ☐
```

Each category is independently switchable. There is no single "sync everything" that quietly
includes something the user did not expect.

## End-to-end encryption

Keys derive from user secrets and device keys; **the server stores ciphertext and never holds
content keys**. Metadata minimisation is a design goal, and where metadata is unavoidable it is
documented in [`DATA-CLASSIFICATION.md`](../privacy/DATA-CLASSIFICATION.md) rather than quietly
collected.

Conflict resolution must preserve both sides by default. Silent last-writer-wins loses user
work, and users never forgive that.

## Offline

A device that has never seen the network works fully. A device that loses the network keeps
working and reconciles later. **Sync is a convenience layer over local truth, never the source
of truth.**
