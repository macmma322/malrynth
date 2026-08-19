# Supply Chain Security

**Status:** DRAFT. The M0 controls listed are in force.

## Position

Every dependency is code that runs with the privileges of whatever links it. For a kernel
that is total authority. Malrynth's primary control is therefore **not** auditing
dependencies but **not having them**.

## Current state (verified at M0)

| Component | External dependencies | Privilege |
|---|---|---|
| `malrynth-kernel` | **none** | ring 0 |
| `malrynth-abi` | **none** | linked into both sides |
| `malboot` | `uefi` (+ its tree) | firmware-time only; gone after `ExitBootServices` |

The full transitive set is recorded in `THIRD_PARTY.md`.

## Rules

1. **The kernel takes no external dependency** without an ADR justifying why the primitive
   cannot be implemented safely in-tree.
2. **Do not reimplement cryptography, Unicode, or compression** to claim purity. A hand-rolled
   cipher is a vulnerability; a maintained implementation is a dependency. Choose the
   dependency and record it.
3. **Every dependency is recorded** in `THIRD_PARTY.md`: name, version, source, license,
   purpose, necessity, and whether it appears in privileged code.
4. **Pin exactly.** `Cargo.lock` is committed (this is a workspace producing binaries, so a
   committed lockfile is correct). The toolchain is pinned to an exact version.
5. **Pin GitHub Actions by commit SHA**, not by tag. Tags are mutable; a compromised action
   repository can retag and silently alter every workflow that references it.
6. **No secrets in CI.** M0's workflow needs none; adding one requires an ADR.
7. **No self-hosted runners.** A self-hosted runner executing untrusted PR code is a host
   compromise.

## Reproducibility

Reproducible builds are the control that makes a compromised pipeline *detectable*: an
independent rebuild that produces different bytes is evidence. Pinning the exact toolchain
and lockfile is the prerequisite, and is done.

**Measured status (2026-08-19): builds ARE reproducible across build directories, and this
is enforced by a test.** `tools/check-reproducible` builds the same source at two paths of
deliberately different length and requires byte-identical images. It runs in `tools/test` and
in CI, because a reproducibility claim without a test is a wish.

Three distinct causes were found and fixed, each identified rather than guessed:

| Cause | Fix |
|---|---|
| Absolute source, cargo-registry and Rust-sysroot paths embedded in DWARF | `--remap-path-prefix` for all three roots |
| PE `TimeDateStamp` stamped with wall-clock time (two copies) | `/Brepro` — LLD substitutes a content hash |
| PE debug-directory CodeView GUID derived from a side PDB whose contents embed path-dependent object paths | `/DEBUG:NONE` for the loader; the kernel retains full DWARF and is reproducible with it |

Flags live in `tools/lib.sh` as the single source of truth; `.cargo/config.toml` deliberately
sets no `rustflags`, because `RUSTFLAGS` replaces rather than merges with them and two
mechanisms that silently override each other is exactly the invisible failure this project
refuses to ship.

**Scope of the claim:** reproducible across *build directories* on one machine with the
pinned toolchain. Not yet demonstrated across different host distributions or over time.
Cross-host reproducibility remains unverified and must not be claimed.

## Planned

- `cargo-deny` in CI for licenses, advisories and duplicate versions.
- SBOM generation per release artifact.
- Build provenance attestation.
- A vendoring policy for anything entering the runtime TCB.
