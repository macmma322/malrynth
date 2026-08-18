# Governance

**Status:** DRAFT. Appropriate to a solo project; revised before the second contributor.

## Current model

Malrynth is founded and maintained by **Nikolay Nikolov Georgiev** (`@macmma322`), who is
currently the sole decision-maker. Pretending otherwise would be theatre.

This document exists because the decisions that matter most — architecture, licensing,
security posture — are being made now, and the rules for changing them should predate the
disagreements.

## How decisions are recorded

**Architecture Decision Records** in `docs/adr/`. An ADR is required for anything that:

- changes a boundary (kernel/user, loader/kernel, repository topology),
- changes an ABI or a stability commitment,
- adds a dependency to privileged code,
- changes the toolchain, target, or language policy,
- amends the [Constitution](docs/constitution/MALRYNTH-CONSTITUTION-DRAFT.md).

An ADR must state what was **rejected** and why. A decision record that lists only the chosen
option is a press release.

Superseded ADRs are marked SUPERSEDED and kept. Deleting them destroys the reasoning that
future maintainers need most.

## The Constitution

The [Constitution](docs/constitution/MALRYNTH-CONSTITUTION-DRAFT.md) states what Malrynth is
for. It is a DRAFT and amendable by ADR, which must name the principle changed, the reason,
and what is given up.

A principle removed without an ADR has not been removed — it has been forgotten. That is the
failure mode the document exists to prevent.

## Code review

Currently none: there is one developer. `tools/test` and CI are the automated gate, and
`main` is protected only by policy and a bypassable local hook (see
[ADR-0002](docs/adr/ADR-0002-branching-and-release-model.md)).

**Configuring a rule requiring a second approver would lock the sole maintainer out of their
own repository**, so it is deliberately not configured. `.github/CODEOWNERS` exists with a
future-compatible layout and is advisory until a second person exists.

## When a second contributor arrives

1. Enable required review on `main` — which requires a plan supporting branch protection on
   private repositories (see [github-ownership.md](docs/operations/github-ownership.md)).
2. Make `CODEOWNERS` enforcing rather than advisory.
3. Decide contributor terms (DCO or CLA) — **before** the first external contribution, since
   obtaining agreement retroactively is often impossible.
4. Resolve licensing ([LICENSING-STATUS.md](docs/legal/LICENSING-STATUS.md)).
5. Revise this document to describe a real multi-person process.

## Organisation migration

Malrynth currently lives under a personal account. The migration plan to a dedicated
organisation — and the decisions made today that keep it cheap — is recorded in
[ADR-0001](docs/adr/ADR-0001-repository-topology.md) and
[github-ownership.md](docs/operations/github-ownership.md).
