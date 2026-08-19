# Rust `std` Port

**Status:** DEFERRED — blocked on [Q1](../architecture/OPEN-QUESTIONS.md) (libc).

## Why it matters

Without `std`, Malrynth can only run `no_std` Rust: no heap collections by default, no
threads, no filesystem, no networking. Practically every Rust crate assumes `std`, so porting
it is what unlocks the Rust ecosystem for Malrynth applications — the single largest
"ecosystem for free" lever available.

## Approach

Upstream `std` is layered: portable code, then `sys` backends per platform. A Malrynth port
means **adding a `sys` backend**, not forking `std`. This is the same path Redox, Fuchsia,
Hermit and others took, and it is a Tier-3 target activity
([`TARGET-TRIPLES.md`](../toolchain/TARGET-TRIPLES.md)).

## Inventory of what must exist

| `std` module | Requires | Notes |
|---|---|---|
| `alloc` (global allocator) | heap | Earliest; needed by everything else |
| `std::io` | handles, IPC | Read/Write over Malrynth handles |
| `std::fs` | VFS, capabilities | **The hard one**: `File::open("/etc/x")` presumes ambient authority. Must resolve through the POSIX facade, and failure with no capability is correct |
| `std::path` | — | Portable; needs Malrynth path semantics defined |
| `std::net` | netstack, socket broker | Sockets are capabilities, not ambient |
| `std::thread` | threads, TLS, sync | Depends on M2 |
| `std::sync` | futex-class primitive | Needs a kernel wait/wake primitive |
| `std::process` | process creation, handle transfer | `Command` must express *which capabilities* the child receives — a genuine API-design question |
| `std::time` | monotonic + wall clock | Depends on M1 |
| `std::env` | process environment | Environment is not authority |
| `std::os::malrynth` | native extensions | Where handles/capabilities surface to Rust |
| dynamic libraries | dynamic loader | Later |

## The interesting design problem

`std::process::Command` on Unix inherits the parent's authority. On Malrynth it must not.
The port therefore needs an explicit way to say *which capabilities the child receives* — a
Malrynth-specific extension trait. Getting this right is what stops "port `std`" from
smuggling ambient authority back in through the most-used API in the language.

## Sequencing

1. `core` + `alloc` — available now via built-in targets.
2. Custom target JSON with `std` stubs returning "unsupported".
3. Fill in `sys` backend as platform pieces land.
4. Upstream as Tier 3 once it builds and a maintainer is committed.

**No implementation in H0.5.**
