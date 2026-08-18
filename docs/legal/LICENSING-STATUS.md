# Licensing Status

**Status:** UNRESOLVED — deliberately.

## Current position

**Malrynth is private, unreleased, and carries no license.** No `LICENSE` file exists, and
this is intentional, not an oversight.

Under the Berne Convention and essentially all national copyright law, an original work is
copyrighted on creation. Absent a license, **all rights are reserved** by the author. That is
the correct default for a project whose governance and commercial model are undecided.

## Why no license is assigned yet

Choosing a license is a governance decision with consequences that are difficult to reverse:

- **Permissive (MIT/Apache-2.0)** maximises adoption and allows proprietary derivatives,
  including a competitor shipping Malrynth without contributing back.
- **Copyleft (GPL-3.0)** keeps derivatives open but constrains commercial partners and
  interacts badly with some hardware-vendor driver arrangements.
- **Weak copyleft (MPL-2.0)** is file-level and often fits operating systems well.
- **Split licensing** (permissive SDK/ABI, copyleft core) is common for platforms and needs
  the boundary decided *before* contributions arrive.

A license granted cannot be revoked for code already released. Choosing before the
architecture and governance are settled would be choosing under maximum uncertainty and
minimum reversibility.

## Constraints on future choice

1. Any license must permit the eventual product family described in the architecture docs.
2. It must be compatible with every third-party component in `THIRD_PARTY.md`. **Today that
   is `uefi` (MIT OR Apache-2.0), which is compatible with every plausible option.** This
   compatibility must be re-checked before each new dependency, because a single
   incompatible dependency can foreclose an entire licensing branch.
3. Contributor terms (DCO or CLA) must be decided **before** the first external contribution.
   Retroactively obtaining agreement from contributors is often impossible.

## Rules in force now

- **Do not copy code from any project** — GPL, BSD, MIT, Apache, or otherwise — without
  recording it in `THIRD_PARTY.md`: exact source, exact license, whether it was *copied* or
  *studied*, obligations incurred, and modifications made.
- **Studying an architecture is not permission to paste an implementation.** Reading how
  Linux, Fuchsia, seL4 or Redox solved a problem is research; transcribing their code is a
  derivative work with license obligations.
- **No Malrynth code is published publicly** while licensing is unresolved. All repositories
  are private.

## Decision trigger

A license must be chosen before **any** of: making a repository public, accepting an external
contribution, or distributing a binary outside the founder's machines. Whichever comes first
requires an ADR.
