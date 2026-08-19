# Filesystem Strategy

**Status:** PROPOSED. Target: M5.

## Sequencing

| Stage | Filesystem | Role |
|---|---|---|
| M5 | Read-only bootstrap/system images | Boot and system content; content-addressed, verified |
| M5 | FAT / exFAT | ESP requirement + removable interop |
| M5 | A simple, well-tested read-write FS **or** ext-family port | Carries user data until MalrynthFS earns trust — [Q4](../architecture/OPEN-QUESTIONS.md) |
| post-M5 | ext (RO → RW), NTFS (RO → carefully qualified RW) | Dual-boot and data recovery |
| research | MalrynthFS | Long-term native default |
| far future | MalrynthFS as default | Only after multi-year qualification |

## Reference designs studied

| Design | Lesson |
|---|---|
| **Btrfs** | COW, reflinks, snapshots, checksums, compression in one design — and how much complexity that costs |
| **OpenZFS** | Transactional groups, atomic root commit, end-to-end integrity |
| **ext4** | Journaling maturity without integrated COW/snapshots |
| **SquirrelFS** | Using Rust's type system to encode crash-consistency ordering rather than relying on developer discipline |

Compatibility with an on-disk format does **not** mean transplanting another OS's
implementation. Foreign filesystems run as constrained user-space services.

## The rule

> **A production filesystem earns trust over years. MalrynthFS does not become the default
> because the name is attractive.**

Data loss is the one failure users never forgive, and a filesystem bug can destroy everything
a person owns. No M0–M7 milestone depends on MalrynthFS.
