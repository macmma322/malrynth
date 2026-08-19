# Compatibility Architecture

**Status:** ACCEPTED as direction. Expands
[`COMPATIBILITY-STRATEGY.md`](COMPATIBILITY-STRATEGY.md) with the per-strategy platform
dependencies that were missing.

## The invariant

```
   Linux apps      Windows apps     Android apps     native Malrynth apps
        │                │                │                   │
   personality/VM    Wine/Proton       VM/runtime              │
        └────────────────┴────────────────┴───────────────────┘
                                 │
                        Malrynth frameworks
                                 │
                          Malrynth kernel
```

**Never:**

```
   Malrynth ──> Linux kernel ──> hardware
```

This is the constraint most likely to be eroded by a plausible shortcut, so it is stated as an
invariant rather than a preference. A compatibility layer is an unprivileged, capability-
confined program. It gets no kernel privilege and no private syscall.

## Rules

1. A compatibility layer holds capabilities **on behalf of** its guest program; it cannot
   obtain authority the user did not grant.
2. **No capability laundering.** A Linux binary does not acquire ambient authority by being a
   Linux binary.
3. Compatibility is never a prerequisite for a native feature. If native Malrynth depends on
   the compat layer, the architecture has inverted.
4. Overhead is measured and disclosed.

## Platform primitives each strategy needs

This is the part the previous strategy document lacked, and it is what makes the dependency
chains in [`DEPENDENCY-GRAPH.md`](../architecture/DEPENDENCY-GRAPH.md) concrete:

| Strategy | Requires |
|---|---|
| **Any VM path** | Kernel virtualization primitives (VMX/SVM, EPT/NPT), IOMMU, user-space VMM, virtio device models |
| **Linux personality** | Processes/threads, futex-class wait/wake, `mmap` semantics, POSIX facade, VFS, socket broker, signal→exception mapping, `/proc`-like synthetic provider |
| **Wine** | Linux personality or POSIX facade, Vulkan, NT-style synchronisation primitives (measurably justified), 32-bit support |
| **Proton / DXVK / vkd3d** | Wine + a conformant Vulkan implementation |
| **Android** | VM, graphics buffer bridge, input/audio bridges, Binder semantics if ever native |
| **Web** | Browser engine, GPU, networking, storage capabilities |

**Wine and gaming sit at the confluence of two long chains** — the runtime chain and the
graphics chain — which is why they are far post-M7 rather than merely "later".

## Staging

```
Stage 1  VM             correctness first; slow but honest
Stage 2  personality    native syscall translation for CLI/static software
Stage 3  desktop        graphics/audio bridges, broader ABI surface
```

Each stage is independently useful. Stage 1 delivers working software long before Stage 2 is
credible, which matters for a platform that needs users before it can attract native ones.
