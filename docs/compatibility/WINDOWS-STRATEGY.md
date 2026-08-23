# Windows Compatibility Strategy

**Status:** ACCEPTED (staging). Target: far post-M7.

## Reuse Wine — do not reimplement Win32

Reimplementing the Windows API is not viable. Wine is decades of accumulated compatibility
work, and Proton adds a large game-focused corpus on top.

**Important:** Proton is built around Wine *on Linux*. It cannot be copied onto Malrynth and
expected to run. What Malrynth needs is the substrate Wine expects.

## Staging

```
Phase A   Windows VM                        correctness, no integration
Phase B   Windows app → Wine → Linux personality → Malrynth
Phase C   Windows app → Wine → native Malrynth backend → Malrynth
```

Phase B is the realistic path: Wine already runs on a POSIX-ish substrate, so the Linux
personality is the shortest route. Phase C removes a layer once it demonstrably pays for itself.

## Gaming path

```
D3D game → Wine/Proton-derived runtime → DXVK / vkd3d → Vulkan → Malrynth GPU driver
```

**The blocker is not Wine. It is Vulkan-quality GPU support** ([Q3](../architecture/OPEN-QUESTIONS.md)).
This is why GPU vendor engagement deserves far higher priority than, say, a first-party office
suite in the early years.

## Kernel-level considerations

- **NT synchronisation primitives.** Wine-class workloads benefit measurably from
  NT-semantics wait/wake. Linux added such an interface for exactly this reason. Malrynth may
  add one **if profiling justifies it** — a compatibility-motivated kernel mechanism is
  legitimate when it has a measured benefit, per [`KERNEL-BOUNDARY.md`](../architecture/KERNEL-BOUNDARY.md).
- **32-bit support.** Much Windows software is 32-bit. The loader and ABI must not make an
  `i686` path impossible, even though it is deferred.

## Anti-cheat: state the limit

Kernel-level anti-cheat (Vanguard, EAC, BattlEye) requires vendor cooperation and, in some
cases, kernel access Malrynth's architecture deliberately does not offer.

**Malrynth must not promise anti-cheat support.** This is tracked as a known limitation, not a
solvable engineering task ([Q15](../architecture/OPEN-QUESTIONS.md)).

## Licensing

Wine is LGPL; DXVK is zlib; vkd3d-proton is LGPL. These remain **separate processes**, so
Malrynth is not a derivative work — but this must be reviewed before distribution, not after
([`LICENSING-STATUS.md`](../legal/LICENSING-STATUS.md)).
