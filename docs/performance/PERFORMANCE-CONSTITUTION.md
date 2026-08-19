# Performance Constitution

**Status:** DRAFT. All numeric targets are **PROPOSED** until measured.

## Position

Performance is a correctness property with a deadline, not an optimisation phase. Operating
systems get slow the same way they get insecure: one defensible regression at a time, none of
which is individually worth blocking.

**No number in this document is a measurement unless labelled MEASURED.** Inventing plausible
targets would make the whole exercise theatre.

## Rules

1. **A budget is defined before the subsystem is built.** A budget written after the first
   implementation is a description, not a constraint.
2. **Every budget has a test.** An unenforced budget is a wish.
3. **Regressions block.** A change that exceeds a budget does not merge without an ADR
   raising it, stating what was bought and what was paid.
4. **Measure on fixed hardware and a fixed configuration.** See `BENCHMARK-METHODOLOGY.md`.
5. **Report distributions, never means alone.** Latency is a tail problem; a mean hides
   exactly the behaviour users feel.
6. **Idle cost is a first-class metric.** Idle CPU and idle RAM determine battery life and
   how much of the machine remains for the user.
7. **Malrynth must not get slower because it got bigger** (Constitution §21). Each milestone
   re-measures the previous milestone's budgets.

## Metric inventory

Recorded now so the list is complete before anyone is tempted to omit an inconvenient entry.
All PROPOSED unless marked.

**Kernel:** boot time (firmware exit → kernel entry → first service); syscall round trip;
context switch; IPC round trip (small message); IPC bulk throughput (shared memory);
allocator alloc/free; scheduling latency under load; interrupt-to-handler latency.

**System:** storage read/write throughput and latency; network throughput, latency, packets
per second; filesystem metadata operations; process creation.

**User-visible:** compositor frame time and dropped frames; input-to-photon latency; audio
round-trip latency; application cold and warm start; Files navigation on a large directory.

**Whole system:** idle CPU; idle RAM; image size; update apply and rollback duration.

**Feature overhead:** Shield (security) overhead; Broadcast (streaming) overhead. Both must
be measured as deltas against the same workload with the feature disabled.

## Proposed release gates

**PROPOSED — none of these is measured, and none is a claim.** They exist because a budget
defined after the first implementation is a description rather than a constraint. Every one
will move once real prototypes exist; the requirement is that they exist *now*.

| Metric | Initial target on reference hardware |
|---|---:|
| Small same-core IPC round trip | < 1.5 us p50 |
| Kernel context-switch path | < 1 us p50 |
| Minimal native app warm launch | < 100 ms p50 |
| Files navigation, existing window | < 50 ms p50; < 100 ms p95 |
| Indexed filename first result | < 50 ms p50 |
| Full-text first result | < 100 ms p50 |
| Desktop services idle CPU | < 0.5% typical |
| Desktop base private memory (excl. cache) | < 750 MB |
| NVMe sequential throughput | > 90% of validated reference-driver baseline |
| Network throughput | > 90% of validated hardware baseline |
| Compositor fullscreen direct path | no material FPS regression |
| Shield gaming overhead | < 2% median FPS regression |
| Broadcast 1440p60 hardware encode | < 3% median game FPS regression |
| OS handoff to shell | < 5 s on a certified desktop |
| Audio | stable 128-frame / 48 kHz path under stress |

Each gate becomes enforceable only in the milestone that builds the subsystem it measures;
until then it is a target with no test, and is labelled as such.

## M0 budgets

M0 is a boot path with no scheduler, so only size and boot are meaningful. Capturing them now
establishes the ratchet before there is anything to hide.

| Metric | Value | Status |
|---|---|---|
| Loader image size | 40,960 bytes | **MEASURED** (release, 2026-08-19) |
| Kernel image size | 130,688 bytes | **MEASURED** (release, 2026-08-19) |
| Build reproducibility | byte-identical across build paths | **MEASURED**, enforced by `tools/check-reproducible` |
| Kernel loaded extent | 16 KiB | **MEASURED** (three `PT_LOAD` segments) |
| Kernel image size ceiling | 256 KiB | PROPOSED |
| Loader image size ceiling | 128 KiB | PROPOSED |
| Firmware-exit → boot marker | not yet instrumented | UNSOLVED |

The kernel grew from 116,208 to 130,688 bytes when the panic backtrace and
`-C force-frame-pointers=yes` were added. That is a deliberate, recorded trade: a kernel that
cannot say where it panicked costs far more engineering time than the bytes are worth. It is
recorded here rather than absorbed silently, which is the entire point of tracking sizes from
M0.

The gap between the on-disk ELF and the 16 KiB loaded extent is debug information,
retained deliberately for symbolisation (see ADR-0003) and stripped from distributable
images later. **Both numbers are tracked** so that a real code-size regression cannot hide
behind the debug-info difference.

`tools/build` writes `build/size-report.txt` on every build. Enforcing the ceilings in CI is
M1 work, tracked in `docs/roadmap/M1.md`.

## Boot time

Not yet instrumented, because doing it honestly requires a timestamp source Malrynth trusts,
and M0 has neither the TSC calibrated nor ACPI parsed. Wall-clock QEMU timing would measure
the host and the firmware more than Malrynth. Recorded as **UNSOLVED**, scheduled for M1
where the timer subsystem provides the instrument.
