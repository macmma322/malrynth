# Sysroot Strategy

**Status:** PROPOSED. **No sysroot exists, and none will be faked.**

A sysroot is the directory a cross-compiler treats as the target's root for headers and
libraries. Malrynth needs one before any userspace program can be compiled.

## Conceptual contents

```
malrynth-sysroot/<target-triple>/
├── lib/
│   ├── crt0.o crti.o crtn.o     process startup / init-fini
│   ├── libc.so  libc.a          C standard library            ← blocked on Q1
│   ├── libm.so  libm.a          math
│   ├── libmalrynth.so           native runtime: syscalls, IPC, capabilities
│   ├── ld-malrynth.so           dynamic loader
│   └── rustlib/                 Rust core/alloc/std for the target
├── include/
│   ├── (C standard headers)
│   └── malrynth/                native API headers — the stable C ABI surface
├── share/
│   ├── linker/                  linker scripts and specs
│   └── metadata/                ABI version, baseline ISA, capability schema
└── sdk/                         higher-level SDK libraries (UI, media, storage clients)
```

## Layering

```
application
   ├─> SDK libraries      (optional, versioned)
   ├─> libc / libm        (POSIX-shaped surface)
   └─> libmalrynth        (native: capabilities, IPC, handles)
            └─> syscalls
```

**`libmalrynth` is the real platform boundary.** libc is implemented *on top of it*, not
beside it — which is what makes POSIX a facade rather than the native personality
([`POSIX-STRATEGY.md`](../runtime/POSIX-STRATEGY.md)).

## Versioning and distribution

The sysroot is versioned with the platform ABI, and multiple versions must coexist so an
older application keeps building. It ships as a downloadable artifact rather than something
built from source per developer — a from-source bootstrap is a barrier that costs adoption.

Content is **content-addressed and signed**, reusing the package integrity mechanism
([`PACKAGE-MODEL.md`](../packages/PACKAGE-MODEL.md)) so that toolchain and package integrity
are one problem rather than two.

## Blocked on

1. **[Q1](../architecture/OPEN-QUESTIONS.md) — libc.** The largest single sysroot component.
2. **[Q5](../architecture/OPEN-QUESTIONS.md) — stable ABI mechanism.** Determines the header layout.
3. **M3 capabilities.** `libmalrynth` cannot be designed before the object model exists.

## Anti-goal

**Do not create an empty sysroot tree to make the toolchain look real.** A sysroot with
headers but no implementation produces programs that link and cannot run — worse than no
sysroot, because it hides the gap.
