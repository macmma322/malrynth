# Security Policy

## Scope and current state

Malrynth is **pre-alpha**. At M0 it boots and prints diagnostics; there is no user mode, no
capability enforcement, no network stack, and no update mechanism.

**Malrynth currently provides no security guarantees and must not be used to protect
anything.** This is stated plainly because a project that implies protection it does not have
causes more harm than one that offers none.

Malrynth is written in Rust. That eliminates a class of memory-safety defects in safe code.
It does **not** make Malrynth secure — see
[UNSAFE-RUST-POLICY.md](docs/security/UNSAFE-RUST-POLICY.md) and
[THREAT-MODEL.md](docs/security/THREAT-MODEL.md).

## Reporting a vulnerability

The repository is private and pre-release. Report privately to the maintainer via GitHub
Security Advisories on this repository, or by direct contact.

**Do not open a public issue for a security defect.**

Please include: affected component and commit, reproduction steps, observed and expected
behaviour, and impact. There is no bug bounty.

## What is in scope today

Given M0's scope, the only meaningful attack surfaces that currently exist are:

- **The ELF loader in `malboot`**, which parses an untrusted kernel image. It is
  bounds-checked and contains no `unsafe`, but it is real parsing of real untrusted input.
- **The boot handoff validation** in the kernel.
- **The build and release pipeline**, including CI configuration and dependencies.
- **Repository access control.**

Known and accepted for M0: there is **no image authenticity check**. An attacker who can
write to the EFI System Partition can replace the kernel. See
[TRUST-BOUNDARIES.md](docs/security/TRUST-BOUNDARIES.md). Signing arrives in M5.

## Out of scope

Firmware and UEFI compromise, sustained physical attacks, malicious hardware, and side
channels including Spectre-class attacks. See the threat model's non-goals.

## Security documentation

- [Threat Model](docs/security/THREAT-MODEL.md)
- [Trust Boundaries](docs/security/TRUST-BOUNDARIES.md)
- [Unsafe Rust Policy](docs/security/UNSAFE-RUST-POLICY.md)
- [Supply Chain](docs/security/SUPPLY-CHAIN.md)
- [Secrets Policy](docs/security/SECRETS-POLICY.md)
