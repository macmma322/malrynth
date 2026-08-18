# Artifact Policy

**Status:** LOCKED.

## Rule

**Git stores source and small deterministic metadata. Nothing else.**

A binary committed once is in history permanently, in every clone, forever. Removing it later
requires rewriting published history — which ADR-0002 forbids except for leaked secrets.

## Never committed

- `target/`, `build/`, `esp/` — every build output
- Disk, ISO and VM images (`*.img`, `*.iso`, `*.qcow2`, `*.vhd`)
- Firmware blobs, including OVMF copies (`OVMF_VARS*.fd` is generated per run)
- Toolchains, QEMU, or any third-party binary
- Logs, serial captures, crash dumps — these routinely contain host paths and can contain
  private data
- Secrets of any kind (`docs/security/SECRETS-POLICY.md`)

All of the above are covered by `.gitignore`.

## Committed

Source, documentation, `Cargo.lock`, `rust-toolchain.toml`, linker scripts, manifests, and CI
configuration. Linker scripts and `.gitattributes` entries are text and must keep exact bytes.

## Generated artifacts

Produced locally by `tools/build` and by CI. Release artifacts will be attached to releases,
never committed.

## Git LFS

**Not enabled**, and not enabled speculatively. LFS adds a second storage system, a second
authentication path, and a bandwidth quota. It is justified only by a genuine long-lived
binary asset requirement — realistically design assets or reference media, neither of which
exists. Note that `git-lfs` filters are configured *globally* on the reference host; because
no `.gitattributes` entry marks anything as LFS, this repository is unaffected.

## Repository size

Monitored as a health metric. A sudden jump means something was committed that should not
have been. The remedy is to catch it before the push, which is what the pre-commit hook and
the pre-publication scan exist for.
