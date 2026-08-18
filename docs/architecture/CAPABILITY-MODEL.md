# Capability Model

**Status:** PROPOSED. Nothing in this document is implemented. Target: M3.

This is a design commitment recorded early because it constrains M1 and M2. It is **not** a
description of existing behaviour.

## Principle

A Malrynth program's authority is exactly the set of capabilities it holds. There is no
ambient authority: no global namespace a program can reach by naming it, no "current user"
whose permissions are implicitly applied, no path that grants access by being typed.

The practical consequence: **a compromised program's blast radius equals the capabilities it
was given**, and that set is visible in its manifest rather than inferred from a policy
engine's behaviour at runtime.

## Objects, handles, rights

- A **kernel object** is a kernel-managed resource: address space, thread, memory region,
  channel, interrupt, IRQ, device MMIO range.
- A **handle** is a process-local, unforgeable reference to an object, valid only in the
  process holding it. Handle values are process-local indices, so a leaked numeric value
  grants nothing.
- **Rights** are per-handle: `READ`, `WRITE`, `EXECUTE`, `MAP`, `TRANSFER`, `DUPLICATE`,
  `DESTROY`, and object-specific rights.
- Rights may be **attenuated** on duplication but never amplified. A process cannot
  manufacture authority it was not given. This is the invariant the whole model rests on.

## Transfer

Capabilities move over IPC channels. Sending a handle may move or copy it, subject to
`TRANSFER`/`DUPLICATE`. This makes delegation explicit and auditable: authority flows along
channels that exist in the process graph, not through a global table.

## Consequences accepted

- **POSIX cannot be implemented natively.** `open("/etc/passwd")` presumes ambient authority
  over a global namespace. POSIX compatibility is therefore a *compatibility layer* that
  holds capabilities on a program's behalf, above the kernel — never a kernel feature. This
  is a deliberate, expensive choice and the reason compatibility sits beside Malrynth rather
  than beneath it.
- **Every service must be designed for explicit delegation**, which is more work per service
  and is the point.

## Open questions (UNSOLVED)

- Revocation: immediate revocation of a delegated capability is architecturally expensive.
  Between revocation objects, generation counters, and mediating services, no choice is made.
- Persistence: how capabilities survive reboot without becoming a second ambient namespace.
- Auditability: presenting a program's effective authority to a non-expert user.
- Performance: handle-table lookup on the IPC fast path.

These are recorded as unsolved rather than glossed. They must be answered before M3, and
answering them may change this document.
