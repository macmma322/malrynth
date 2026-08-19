# IPC Model

**Status:** PROPOSED. Not implemented. Target: M3.

## Why this dominates the design

In a microkernel, IPC cost is the tax on every service call: a filesystem read, a network
packet, a frame presented. A microkernel with slow IPC is a slow operating system, and no
amount of work elsewhere recovers it. seL4's central lesson is that IPC performance is an
architectural property, decided early, not an optimisation applied late.

## Shape

- **Synchronous, small-message IPC** as the primary mechanism: a call transfers a small
  register-sized payload and optionally handles, blocking until reply. This maps to a fast
  path that can avoid scheduler involvement by switching directly to the receiver.
- **Shared memory for bulk data.** Bulk data is never copied through the kernel. A channel
  establishes a shared region; subsequent transfers move ownership or notify, not bytes.
  Every large-data path (storage, network, graphics, media) is expected to use this.
- **Shared descriptor rings** for sustained high-throughput producer/consumer paths:
  networking, audio, and device queues. These are architecturally distinct from the two
  mechanisms above, not an optimisation of them — they have their own lifetime, ordering and
  backpressure properties, and they are what make a user-space driver model viable at line
  rate. A channel carries the *control plane*; the ring carries the data.

- **Asynchronous notification** as a signalling primitive for events that must not block a
  sender (interrupts, completion signals). This signals that something happened; it is not a
  bulk transport.

## Rules

1. **The kernel never interprets message contents.** It transfers bytes and handles. Protocol
   parsing is a user-space concern; a kernel that parses protocols is a kernel with an
   attack surface proportional to the number of protocols.
2. **Handles transfer with messages**, subject to rights (see `CAPABILITY-MODEL.md`).
3. **Message payloads are small and bounded.** The inline channel payload budget starts at
   roughly 256-512 bytes, to be settled by benchmark rather than doctrine. Anything larger
   travels as a `MemoryObject` handle or through a shared ring.
4. **No unbounded queueing in the kernel.** Unbounded queues turn a misbehaving sender into a
   kernel memory-exhaustion attack. Backpressure is explicit.
5. **Every IPC path has a measured budget** before it is declared done. See
   `docs/performance/PERFORMANCE-CONSTITUTION.md`.

## Open questions (UNSOLVED)

- Whether a direct-switch fast path can be implemented without entangling IPC and the
  scheduler in a way that harms both.
- Multi-CPU IPC: cross-core calls, IPI cost, and cache-line behaviour of the handle table.
- Timeouts and cancellation without reintroducing unbounded kernel state.
- Whether an interface definition language is worth its complexity, and if so whether it
  generates Rust only or a stable wire format.

No decision is made here. These are the questions M3 must answer with measurements.
