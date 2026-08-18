# Kernel Boundary

**Status:** PROPOSED. M0 implements only the boot-time portion.

## The question this document answers

For any proposed piece of code: *does it belong in the kernel?* Without a written test, the
kernel accretes functionality until it is a monolith with a microkernel's performance
characteristics — the worst of both.

## The test

Code belongs in the kernel **only if all four hold**:

1. **It cannot be expressed with capabilities.** If a user-space program holding the right
   capability could do it, it goes to user space.
2. **It manages a resource the kernel must arbitrate.** Address spaces, threads, CPU time,
   the object table, IPC.
3. **Placing it outside would create an unavoidable, measured performance failure.** Measured
   — not assumed.
4. **Its failure would be unrecoverable anyway.** If a user-space failure could be contained
   and restarted, containing it is strictly better.

Everything else is a service or a driver.

## In the kernel

- Physical and virtual memory management; page tables.
- Thread and address-space objects; the scheduler.
- The object table, handles, and capability rights enforcement.
- Synchronous IPC and shared-memory establishment.
- Exception and interrupt entry; dispatch to user-space handlers.
- Time.
- The minimum architecture support for the above.

## Not in the kernel

- Filesystems, the network stack, device drivers, the compositor, audio, package management,
  update logic, policy engines, and every application.
- Filesystem *format* knowledge — in particular the kernel never parses on-disk structures
  from an untrusted volume. This is one of the most reliable sources of kernel compromise in
  every operating system that does it.

## Boundaries inside the kernel

These are enforced now, at M0, because they are cheap now and expensive later:

1. **Architecture code is confined to `arch/`.** No `asm!`, port I/O, or
   `#[cfg(target_arch)]` outside it. `arch/mod.rs` rejects unsupported targets with a
   `compile_error!` rather than a stub that pretends to work.
2. **`unsafe` is confined to audited modules and carries a `SAFETY:` justification.** See
   `docs/security/UNSAFE-RUST-POLICY.md`.
3. **The firmware boundary is absolute.** The kernel contains no UEFI type, no UEFI calling
   convention, and no UEFI memory-type number. Everything firmware-shaped stops in
   `malboot` and is translated into `malrynth-abi`. This is what makes UEFI a *supported boot
   environment* rather than an architectural dependency — and it is what will let a
   non-UEFI boot path be added without touching the kernel.
4. **The kernel has zero external dependencies.** Every crate added to the kernel runs in
   ring 0 with full authority. M0's kernel depends only on `core` and `malrynth-abi`.

## Trusted computing base at M0

Firmware (outside Malrynth's TCB, and not verified by Malrynth) → `malboot` → kernel.

`malboot` is inside the TCB while it runs and stops existing at `ExitBootServices`. It is
therefore not part of the *runtime* TCB, which is why depending on the `uefi` crate there is
an acceptable trade while a kernel dependency would not be.
