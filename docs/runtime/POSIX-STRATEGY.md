# POSIX Strategy

**Status:** PROPOSED — **facade, not native personality**. This is
[Q2](../architecture/OPEN-QUESTIONS.md).

## The question

Is POSIX *what Malrynth is*, or *something Malrynth can also do*?

## Recommendation: facade

**The native Malrynth API is capability-first. POSIX is a compatibility layer above it.**

```
   Unix-ported software          native Malrynth software
            │                              │
      POSIX facade                         │
            │                              │
            └──────────> libmalrynth <─────┘
                              │
                          syscalls
```

## Why not native POSIX

POSIX's design assumes precisely what Malrynth rejects:

| POSIX assumption | Malrynth |
|---|---|
| Global filesystem namespace reachable by name | Authority comes from held capabilities |
| Ambient authority from process credentials | No ambient authority |
| `uid`/`gid` as the authority model | Rights on handles |
| `fork()` inherits everything | Explicit handle transfer |
| Signals as asynchronous control | IPC and exception ports |
| `/proc`-style global introspection | Capability-scoped inspection |

Making POSIX native would mean **adopting Unix's security model as Malrynth's**, which
forfeits the project's central architectural claim. Every subsequent capability feature would
be fighting the platform's own primary interface.

## What the facade must do

Hold capabilities on the program's behalf and materialise a namespace *from them*:

- A process gets a **root directory capability** rather than the global filesystem.
- `open()` resolves relative to capabilities the process holds; unreachable paths fail with
  `ENOENT`/`EACCES` — which is honest, not a bug.
- File descriptors are a **facade over handles**, keeping `fd` numbering semantics that
  software depends on.
- `fork()` is the hardest case: copying an address space is natural, but "inherit all
  authority" is not. Likely: support `posix_spawn` well, support `fork` with explicitly
  transferred capabilities, and accept that some software needs patching.
- Signals map onto exception ports and IPC, with best-effort semantics documented precisely.

## Conformance target

**A useful subset, honestly labelled** — not certified conformance. Certification is expensive
and would force semantics that damage the capability model. The documentation must state
exactly which interfaces exist and which do not, so a porter knows before starting rather than
after.

## Trade-offs, stated plainly

| Consumer | Facade impact |
|---|---|
| **Unix software ports** | Most CLI software works with a good facade; anything assuming `/proc`, global paths or elaborate signal use needs patching |
| **Wine** | Needs a substantial facade plus futex-class primitives and `mmap` semantics — a major driver of facade scope |
| **Language runtimes** | Python, Node, JVM all assume POSIX; each is a porting project sized by facade completeness |
| **Native security** | **Preserved** — this is the whole point |
| **Performance** | An extra layer on some paths; hot paths should use native APIs directly |

## Consequence to accept

Some software will never run unmodified, because it fundamentally requires ambient authority.
That is the cost of the architecture, and it should be stated openly rather than discovered by
developers one port at a time.
