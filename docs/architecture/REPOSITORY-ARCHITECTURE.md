# Repository Architecture

**Status:** LOCKED. Implements [ADR-0001](../adr/ADR-0001-repository-topology.md).

## Topology

**One private repository: `macmma322/malrynth`.**

Not seven, not eight. The reasoning is in ADR-0001; the summary is that at M0 the kernel ABI
does not exist, repository boundaries freeze interfaces, splitting later is cheap and
lossless (`git subtree split` preserves history) while merging later is expensive, and on
this GitHub plan each additional private repository adds an *unprotectable* branch.

## Layout

```
malrynth/
├── README.md CONTRIBUTING.md SECURITY.md GOVERNANCE.md
├── THIRD_PARTY.md THIRD_PARTY_POLICY.md
├── Cargo.toml rust-toolchain.toml rustfmt.toml
├── .cargo/config.toml .gitattributes .gitignore
│
├── docs/            constitution, architecture, adr, research, roadmap,
│                    security, performance, compatibility, specs, operations, legal
├── manifests/       workspace inventory, product compositions, release records
├── tools/           bootstrap doctor build test run-qemu status  (+ hooks/)
├── .github/         CODEOWNERS, templates, workflows
│
└── core/            first-party system code -- the future `malrynth-core`
    ├── abi/         malrynth-abi   : the boot handoff contract
    ├── boot/uefi/   malboot        : the UEFI loader
    └── kernel/      malrynth-kernel: the kernel
```

The repository root plays the **superproject role**: it answers "which exact source state is
Malrynth revision X". Today the answer is one commit SHA, reported by `tools/status`.

## Why `core/` is a top-level directory

So that extraction is mechanical, not archaeological:

```
git subtree split --prefix=core -b extract/core
```

produces a repository with `core/`'s full history, ready to push and re-add as a submodule.
The directory boundary is the future repository boundary, present from the first commit.

## What deliberately does not exist

`products/`, `ui/`, `apps/`, `sdk/`, `compat/`, `infra/` — as directories or repositories.
Each is documented (`PRODUCT-COMPOSITION.md`, `docs/apps/APPLICATION-MAP.md`,
`docs/compatibility/COMPATIBILITY-STRATEGY.md`) so the roadmap is expressed without
generating scaffolding. Empty directories are not architecture.

## Workspace

One Cargo workspace, one `Cargo.lock`, one pinned toolchain. Members build for **different
targets** and are never built together — there is no single valid `cargo build --workspace`
for this tree, which is why `tools/build` invokes cargo per package with an explicit
`--target`.

## Split and merge criteria

See ADR-0001. Splits are evidence-driven and require two demonstrable criteria; merging back
is explicitly permitted and is not treated as failure.
