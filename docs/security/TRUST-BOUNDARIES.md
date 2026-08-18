# Trust Boundaries

**Status:** DRAFT. Only the M0 boundaries are real.

A trust boundary is a point where data or control crosses between components with different
authority. Every one must be enumerated, because an unenumerated boundary is an unvalidated
boundary.

## M0 — implemented

```
  [firmware / UEFI]          outside the TCB; unverifiable by Malrynth
        |
        |  (B1) firmware loads BOOTX64.EFI
        v
  [malboot]                  in the TCB while it runs; ceases to exist at ExitBootServices
        |
        |  (B2) reads kernel.elf from the ESP
        |  (B3) BootInfo handoff
        v
  [malrynth-kernel]          the runtime TCB
```

**B1 — firmware → loader.** Malrynth cannot validate the firmware that loaded it. Trusted by
necessity, documented as such (`THREAT-MODEL.md` T14).

**B2 — ESP → loader.** The kernel image is untrusted input: it comes from a filesystem an
attacker with disk access could modify. *Validated now:* ELF magic, 64-bit little-endian
class, `ET_EXEC`, `EM_X86_64`, `p_filesz <= p_memsz`, every segment's bytes present within
the file, segment count bounded, and the link address matching the loader's expectation.
Fields are read by bounds-checked little-endian extraction, never by casting a possibly
unaligned buffer. *Not validated:* authenticity. There is no signature check, so an attacker
who can write to the ESP can replace the kernel. This is **accepted and documented** for M0;
Secure Boot and image signing are M5.

**B3 — loader → kernel.** The kernel validates magic, ABI version and struct size before
touching any other field, and refuses to run if the load address disagrees with its link
address. A mismatch here would otherwise produce a kernel interpreting arbitrary memory as
structured data — a silent failure, which is the worst kind.

## Planned boundaries (not implemented)

| Boundary | Crossing | Validation required |
|---|---|---|
| user → kernel | syscalls | Every argument untrusted; all pointers validated; no TOCTOU |
| kernel → user | IPC delivery | No kernel memory disclosure; no uninitialised padding |
| service → service | IPC | Each service treats peers as untrusted |
| driver → kernel | interrupts, DMA | IOMMU confinement; drivers unprivileged |
| device → memory | DMA | IOMMU; explicitly absent protection where no IOMMU exists |
| network → stack | packets | Fully untrusted; stack unprivileged |
| filesystem → VFS | on-disk structures | Untrusted; parsed in user space, never in the kernel |
| update → system | images | Signature verification, anti-rollback |
| build → artifact | CI | Pinned deps, reproducibility, provenance |

## Rule

**Data crossing a boundary is untrusted until validated, and validation happens on the
receiving side.** A sender's promise is not a check. This applies to the M0 ELF loader
exactly as it will apply to the M3 syscall layer.
