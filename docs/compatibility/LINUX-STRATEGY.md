# Linux Compatibility Strategy

**Status:** ACCEPTED (staging). Target: post-M7.

## Why Linux is a good compatibility target

Linux's userspace syscall interface is deliberately long-lived — its documentation treats
syscalls as stable ABI expected to remain available. That makes it a **fixed** target rather
than a moving one, which is what makes a personality layer feasible at all.

## Three stages

### 1. Linux VM (first)

```
Linux application → minimal Linux guest → virtio GPU/net/files → Malrynth VMM
```

Correctness before reimplementation. The guest is a real Linux kernel, so semantics are exact.
Cost: memory, boot time, weaker integration.

### 2. Linux personality (second)

The kernel tags a process `Personality = Linux_x86_64`; the syscall dispatcher interprets Linux
syscall numbers. Fast primitives (`clock_gettime`, `mmap`, futex, thread ops) map directly onto
Malrynth kernel primitives; complex operations forward over IPC to a Linux Compatibility
Server.

### 3. Desktop compatibility (third)

glibc requirements, dynamic loader compatibility, a **Wayland compatibility endpoint** on the
native compositor, audio bridging, Vulkan passthrough, `/proc`-like synthetic providers,
`ioctl` families, and eventually container-style namespacing.

## The central difficulty

**Linux presumes ambient authority; Malrynth grants none.** The personality layer must hold
capabilities on the program's behalf and materialise a namespace from them.

```
Linux app: open("/home/user/doc.txt")
   → personality resolves against the capabilities THIS process was given
   → no matching capability → ENOENT
```

That is correct behaviour, not a bug — and it means a Linux application under Malrynth sees
only what it was granted. It also means some software will not run unmodified, which must be
stated plainly rather than discovered.

## Scope reality

A useful Linux environment needs substantial portions of: ELF loading, signals, `mmap`/
`mprotect`, futex/`futex_waitv`, epoll, eventfd, timerfd, process/thread creation, credentials,
file descriptors, socket semantics, `ioctl` families, `/proc` information, shared memory,
filesystem semantics, vDSO expectations, and eventually namespaces.

**`ioctl` breadth is the classic underestimate.** It is effectively unbounded, and it is why
the VM stage exists.
