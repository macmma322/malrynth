# libc Strategy

**Status:** **UNSOLVED.** This is [Q1](../architecture/OPEN-QUESTIONS.md), the
highest-leverage open decision in the project.

## Why it dominates

libc gates POSIX, Rust `std`, the C/C++ SDK surface, every **ported** application, and all of
Wine/Proton. Choosing wrongly is not a local mistake: it propagates into every layer above the
runtime.

**What it does not gate.** libc is **not** the root prerequisite for native Malrynth userspace.
`libmalrynth` is the platform boundary and libc sits on top of it (see "Non-negotiable
constraints" below), so a native application written in Rust against `no_std` + `alloc` is
possible before this question is answered. What is at stake is **ecosystem reach** — how much
existing software can be carried, and how soon — not whether userspace can exist at all.

It is also genuinely hard, because Malrynth's authority model is not Unix's. `open("/etc/passwd")`
presumes ambient authority over a global namespace; Malrynth grants none. Whatever libc is
chosen, **its bottom layer must be rewritten** to acquire authority from capabilities rather
than assume it.

## Candidates

### musl — port

*For:* complete, small, readable, standards-focused, MIT-licensed, proven as the libc for
Alpine and many static-linking workflows. A large ecosystem already builds against it.

*Against:* deeply Linux-syscall-shaped. The port is not "swap a syscall table" — it is
replacing the bottom layer with capability-based equivalents while preserving semantics that
callers depend on. Process, signal and filesystem models need genuine translation.

### LLVM libc — adopt

*For:* modern C++ implementation, modular, explicitly multi-platform (Linux, GPU, baremetal,
UEFI), actively developed, aligned with the LLVM toolchain Malrynth already uses.

*Against, verified 2026:* full build mode supports **only fully statically linked binaries —
no dynamic loader**, and many functions needed by non-trivial applications are missing
(regex, locale, wide-character I/O). Malrynth needs dynamic linking for side-by-side runtimes.
Promising, **not currently sufficient**.

### relibc-style — study

*For:* Redox's libc is the closest existing analogue — a libc written for a Rust microkernel
that is not Unix underneath. Its *structure* is directly instructive.

*Against:* smaller ecosystem; adopting it couples Malrynth's schedule to another project's.

### Write our own

*For:* exact fit to the capability model; no foreign assumptions.

*Against:* enormous, and re-solves solved problems. Standards conformance is a long tail that
consumes years and produces subtle breakage in ported software.

## Current inclination (not a decision)

**Port musl's upper layers onto a Malrynth bottom layer, with `libmalrynth` as the real
platform interface underneath.** It gives the most working software soonest, its licence is
unproblematic, and the work is bounded and well-understood.

LLVM libc should be **re-evaluated at the decision point** — its dynamic-linking and coverage
gaps may close, and its architecture is a better long-term fit.

## Decision procedure

**Decide by end of M4.** M5 cannot begin without it.

Evidence required, in order:
1. A spike porting a **minimal** musl subset (`malloc`, `read`, `write`, `mmap`, `pthread`
   basics) onto the M3 syscall surface. This measures the real cost of the bottom layer.
2. An inventory of what the POSIX facade actually needs — likely far less than full POSIX.
3. Re-check LLVM libc's dynamic loader and function coverage at that date.
4. A read of relibc's structure for lessons, without adopting it.

## Non-negotiable constraints

Whatever is chosen:

- **libc sits on `libmalrynth`, not beside it.** The native API is primary; libc is a consumer.
- **No ambient authority.** A libc call that appears to open a global path must resolve through
  a capability the process holds. If it holds none, the call fails — that is correct behaviour,
  not a bug.
- **Thread-safe and reentrant** from the start.
- **Dynamic linking required.** Static-only forecloses side-by-side runtimes.
- **Ledger entry** in `THIRD_PARTY.md` before any code is imported.
