# ADR-0004 — Kernel Object Model, Rights and Syscall Naming

- **Status:** PROPOSED (not LOCKED). Binding as *direction*; the concrete set is expected to change before M3.
- **Deciders:** Nikolay Nikolov Georgiev (founder)
- **Depends on:** [ADR-0001](ADR-0001-repository-topology.md), [ADR-0003](ADR-0003-toolchain-and-targets.md)
- **Input:** [`docs/research/deep-research-integration.md`](../research/deep-research-integration.md)
- **Review trigger:** M3 (capabilities and IPC). This ADR is expected to be superseded by a LOCKED version then.

## Context

`docs/architecture/CAPABILITY-MODEL.md` states the *principle* — no ambient authority, authority
is exactly the set of held capabilities — but deliberately did not name the objects or rights,
because at M0 nothing existed to constrain them.

The deep research report supplies a concrete namespace and rights vocabulary derived from
Zircon and seL4. Recording it now costs nothing to change and buys something real: **M1 and M2
make decisions that either fit this model or quietly foreclose it.** A page-table design that
assumes a global address space, or an M2 syscall layer that hands out ambient authority "just
for now", is expensive to undo at M3.

The alternative — deciding at M3 — was rejected for exactly that reason. This is a *direction*
recorded early, not a specification frozen early, which is why the status is PROPOSED.

## Decision

### 1. Kernel object namespace (initial)

| Group | Objects |
|---|---|
| Execution | `Job`, `Process`, `Thread` |
| Memory | `AddressSpace`, `MemoryObject`, `MemoryMapping` |
| Communication | `Channel`, `Port`, `Event`, `Timer` |
| Device | `Interrupt`, `Device`, `IoRegion`, `DmaDomain`, `DmaMapping` |
| Meta | `Resource`, `DebugObject`, `ExceptionPort` |

`Job` is adopted deliberately: a hierarchical container above `Process` is what makes
resource limits and bulk termination expressible without a separate policy mechanism.

### 2. Handles are distinct from objects

An **object** is the kernel-managed resource. A **handle** is a process-local, unforgeable
reference *to* an object, carrying its own rights. Two handles to the same object may carry
different rights. Handle values are process-local indices, so a leaked numeric value grants
nothing outside the process holding it.

### 3. Rights vocabulary

```
READ  WRITE  EXECUTE  MAP        access
WAIT  SIGNAL                     synchronisation
TRANSFER  DUPLICATE              delegation
ENUMERATE  CONFIGURE             inspection and control
DEBUG  ADMIN                     privileged
```

Rights are **object-type-specific**: `SIGNAL` is meaningful on an `Event`, not on a sealed
executable image. There is no generic `ROOT` right, and no application ever receives `ADMIN`.

### 4. Attenuation-only

**A process may duplicate a handle with the same rights or fewer, never more.** This single
invariant is what the entire model rests on, and it is the thing M3's security tests must
attack adversarially rather than assert.

### 5. Memory object kinds

`anonymous`, `file-backed`, `device-backed`, `contiguous`, `DMA-pinnable`,
`copy-on-write clone`, `read-only sealed`, `executable sealed`.

`WRITE` and `EXECUTE` are strictly separated: an ordinary mapping is never both.

### 6. Syscall naming: `mly_<object>_<verb>`

```
mly_handle_close        mly_channel_create      mly_channel_write
mly_memory_create       mly_memory_clone        mly_memory_seal
mly_address_map         mly_object_wait         mly_process_create
mly_dma_domain_create   mly_dma_map             mly_interrupt_bind
```

`mly_` is short because it prefixes every syscall in the system; the rest of the name is
spelled out because it is read far more often than typed. This is the one sanctioned
abbreviation in `docs/specs/naming.md`.

### 7. The syscall ABI stays small

Native application APIs live **above** the syscall boundary in versioned system libraries. If
the syscall ABI becomes the public platform contract, every application binds directly to the
kernel and the kernel can never change. Keeping it small is what makes ADR-0002's API
stability commitment affordable.

## Consequences for milestones before M3

This is the reason the ADR exists now rather than at M3:

- **M1** must not assume a single global address space. `AddressSpace` is an object, and page
  tables are per-address-space from the start.
- **M2's syscall layer is explicitly temporary** and must be documented as such
  (`docs/roadmap/M2.md`). Any ambient-authority syscall introduced for convenience in M2 is a
  debt that M3 must repay in full, and each one must be listed when it is added.
- **M2 must not expose a "get any process by ID" style interface**, which is ambient authority
  wearing a different name and is very hard to withdraw once software depends on it.

## Alternatives considered

- **Defer entirely to M3** — rejected: M1/M2 would make foreclosing decisions unknowingly.
- **Freeze the model now (LOCKED)** — rejected: nothing has been built against it, so freezing
  would be confidence without evidence. The open questions in `CAPABILITY-MODEL.md`
  (revocation, persistence, auditability, handle-table cost on the IPC fast path) are
  unanswered, and at least one of them may change this list.
- **Copy Zircon's object set wholesale** — rejected: Zircon carries objects serving Fuchsia
  decisions Malrynth has not made. The subset above is adopted because each entry has a stated
  role; the rest can be added when something needs them.

## Open questions (UNSOLVED — must be answered by M3)

1. **Revocation.** Immediate revocation of a delegated capability is architecturally
   expensive. Revocation objects, generation counters, and broker mediation are all
   unresolved.
2. **Persistence.** How capabilities survive reboot without becoming a second ambient namespace.
3. **Handle-table cost** on the IPC fast path, which may constrain the table's representation.
4. **Rights granularity.** Twelve rights may prove too coarse or too fine; only real services
   will show which.
