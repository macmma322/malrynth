# Compatibility Strategy

**Status:** PROPOSED. Nothing implemented. Not before M7.

## The invariant

Compatibility with Linux, Windows and Android sits **above or beside** Malrynth — never
underneath its kernel.

```
   [Linux apps]  [Windows apps]  [Android apps]   [native Malrynth apps]
        |               |               |                   |
   [compat layer]  [compat layer]  [compat layer]           |
        \_______________|_______________/                   |
                        |                                   |
                 MALRYNTH KERNEL  <---------------------------
```

Any design in which Malrynth code runs on a Linux kernel is rejected by definition, however
convenient. This is the constraint most likely to be eroded by a plausible-sounding shortcut,
so it is stated as an invariant rather than a preference.

## Approaches under consideration

- **Linux:** a personality layer translating Linux syscalls to Malrynth capabilities, and/or
  a confined Linux guest VM. The personality layer's central difficulty is that Linux
  presumes ambient authority over a global namespace while Malrynth grants none — so the
  layer must *hold capabilities on the program's behalf* and materialise a namespace from
  them. That is the whole design problem, and it is UNSOLVED.
- **Windows:** Wine on top of the Linux personality, or ported directly onto Malrynth.
  Graphics translation is the hard part.
- **Android:** a confined VM is the realistic path; the runtime's assumptions are too deep to
  translate.

## Rules

1. A compatibility layer is an unprivileged, capability-confined program. It gets no kernel
   privilege and no special-cased syscall.
2. A compatibility layer may not weaken a native security boundary. A Linux program does not
   acquire ambient authority by being a Linux program.
3. Compatibility is never a prerequisite for a native feature. If native Malrynth depends on
   the compat layer, the architecture has inverted.
4. Compatibility is measured (see `docs/performance/`) and its overhead disclosed.

## Repository

No `compat/` directory exists and none will be created before the work is real. See ADR-0001.
