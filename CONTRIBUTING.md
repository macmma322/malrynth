# Contributing to Malrynth

Malrynth is currently a solo project. This document exists so the working rules are written
down before there is a second person, not after.

## Setup

```bash
./tools/bootstrap   # rustup toolchain + targets + git hooks (user-local only)
./tools/doctor      # verify the host; installs nothing
```

`tools/bootstrap` is the only tool that changes anything, and it touches only user-local
rustup state and this repository's git config. **System packages are never installed
automatically** — `tools/doctor` tells you what is missing and you decide.

## Before every commit

```bash
./tools/test
```

`fmt`, `clippy -D warnings` on the real targets, ABI unit tests, a full build, and three
consecutive QEMU boots. The hooks installed by `bootstrap` run a subset automatically, but
they are bypassable and are not a substitute for running the suite.

## Branching

`main` is always buildable and bootable. Work happens on:

- `feature/<topic>` — new functionality
- `fix/<topic>` — bug fixes
- `research/<topic>` — spikes and experiments, **not expected to build**

History is linear: rebase or squash, never a merge commit, so `git bisect` stays unambiguous.
Never force-push a published branch. See [ADR-0002](docs/adr/ADR-0002-branching-and-release-model.md).

**`main` is not protected server-side.** GitHub Free does not offer branch protection or
rulesets on private repositories, so the pre-push hook is the only enforcement that exists.
Treat it accordingly.

## Commit messages

```
<type>: <imperative summary>

Why this change is needed. What was considered and rejected.
```

Types: `docs`, `build`, `kernel`, `boot`, `abi`, `ci`, `test`, `fix`, `refactor`, `chore`.

## Code rules

1. **Safe Rust by default.** `unsafe` only where nothing safe expresses the operation, only
   in the locations listed in [UNSAFE-RUST-POLICY.md](docs/security/UNSAFE-RUST-POLICY.md),
   and **always with a `SAFETY:` comment**. A block without one is a defect even if correct.
2. **No new kernel dependency without an ADR.** Everything linked into the kernel runs in
   ring 0. The kernel currently has zero external dependencies and that is a property worth
   defending.
3. **Architecture-specific code lives in `core/kernel/src/arch/`.** No `asm!`, port I/O, or
   `#[cfg(target_arch)]` anywhere else.
4. **Validate untrusted input on the receiving side.** A sender's promise is not a check.
5. **Never claim something works without running it.** Documentation states what is
   implemented and what is not, and labels every document's status.

## Architectural changes

Anything that changes a boundary, an ABI, a dependency policy, or the repository topology
needs an ADR in `docs/adr/`. Copy the structure of an existing one: Status, Context,
Decision, Alternatives, Consequences. **Record what was rejected and why** — that is the part
future readers actually need.

## What not to do

- Do not commit build output, images, logs, or secrets ([ARTIFACT-POLICY.md](docs/operations/ARTIFACT-POLICY.md)).
- Do not copy code from another project without recording it in `THIRD_PARTY.md`. Studying an
  architecture is research; pasting an implementation creates license obligations.
- Do not create empty directories or placeholder crates for future work. Document the plan
  instead.
- Do not add a milestone's work to an earlier milestone because it seems easy.
