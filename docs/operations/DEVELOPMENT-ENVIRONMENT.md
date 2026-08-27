# Development Environment

**Status:** LOCKED for the current development model. Re-verify with the platform doctor on
any new machine.

## Canonical development environment

Native Windows is the canonical/current development environment. The supported entry point is:

```powershell
python tools/windows/malrynth.py doctor
python tools/windows/malrynth.py build
python tools/windows/malrynth.py test --boots 3
```

The repository and build outputs remain path-independent: a particular drive letter, user
profile, worktree name, Cargo home, or rustup home is never part of the compiler/linker
contract. QEMU and a matching OVMF code/variables pair are required for boot validation;
the pinned Rust toolchain and targets are defined by the repository. The Windows tooling
discovers host installations and reports missing dependencies rather than installing them.

Git Bash remains necessary for the repository secret scanner and Git hooks. It is not the
build-system authority: native Windows build, test, artifact verification, panic validation,
and reproducibility are owned by `tools/windows/malrynth.py` and its package.

## Linux reference environment (historically validated 2026-08-19)

Linux remains a supported reference and historical validation environment. Its tools are
valuable for cross-platform contract validation, but the host below is no longer described
as the current canonical machine.

| | |
|---|---|
| OS | Ubuntu 26.04 LTS, Linux 7.0.0-29-generic |
| Architecture | x86_64, 12 CPUs |
| Historical repository root | `/media/Data/Malrynth` |
| Rust | 1.97.1 (pinned via `rust-toolchain.toml`) |
| QEMU | 10.2.1 |
| OVMF | 2025.11 (`/usr/share/OVMF/OVMF_CODE_4M.fd`, `OVMF_VARS_4M.fd`) |
| KVM | available |

Not installed and **not required**: `clang`, `lld`, `llvm-config`, `cmake`, `ninja`. The Rust
toolchain ships `rust-lld` and `rust-objcopy`, which is the entire link toolchain Malrynth
needs (ADR-0003). `mtools` is absent and is optional — see "Known gaps".

## The NTFS constraint (important)

`/media/Data` is **NTFS via ntfs-3g (FUSE)**. Verified behaviour:

| Property | Result |
|---|---|
| Symlinks | work |
| Case sensitivity | case-sensitive |
| **POSIX mode bits** | **not stored — `chmod` is a silent no-op; everything reads `0777`** |

### Consequence for Git, and the mitigation

With default settings Git would see every file as mode `0777` and record **every file as
`100755`**, so a fresh clone on ext4 would have every source file executable. The repository
is therefore configured with:

```
git config core.fileMode false
git config core.autocrlf false
git config core.eol lf
```

`core.fileMode=false` makes Git record `100644` for new files and ignore mode changes.
Scripts that genuinely need the executable bit are marked explicitly in the index:

```
git update-index --chmod=+x tools/build
```

**`tools/doctor` checks this and fails if `core.fileMode` is not `false` on such a
filesystem**, because the failure is otherwise silent and only visible to whoever clones next.

`core.autocrlf=false` with `core.eol=lf` overrides the global `autocrlf=input` so the
repository is byte-identical regardless of host or mount, and `.gitattributes` enforces
`* text=auto eol=lf` for any other clone.

### Consequence for build performance

ntfs-3g is a FUSE filesystem: every file operation crosses to userspace. A Rust `target/`
directory contains tens of thousands of small files, so builds are materially slower than on
ext4. `target/` is git-ignored, so it can live anywhere:

```bash
export CARGO_TARGET_DIR="$HOME/.cache/malrynth-target"
```

`tools/lib.sh` honours `CARGO_TARGET_DIR`, and `tools/doctor` suggests this when it detects a
FUSE/NTFS root. It is **not** set in `.cargo/config.toml`, because a committed absolute path
would break every other machine.

These NTFS/FUSE rules describe that Linux reference mount only. They do not prohibit a native
Windows checkout; Windows repository hygiene is validated by the native tooling and CI.

## Linux reference quick start

```bash
git clone https://github.com/macmma322/malrynth.git
cd malrynth
./tools/bootstrap   # user-local rustup toolchain + targets only
./tools/doctor      # read-only readiness report
./tools/build       # loader + kernel + ESP
./tools/test        # fmt, clippy, unit tests, 3x QEMU boot
./tools/run-qemu --interactive   # watch it boot
```

`tools/bootstrap` is the only tool that mutates anything, and it touches **only** user-local
rustup state. System packages are never installed automatically; `tools/doctor` reports what
is missing and how to obtain it, and the decision stays with the developer.

## Known gaps

- **`mtools` is absent**, so no real distributable FAT ESP image can be produced. The boot
  test uses QEMU's virtual FAT (`fat:rw:`), which needs neither root nor extra packages.
  Producing a `.img`/`.iso` requires `mtools` (or root for a loop mount) and is deferred;
  `tools/doctor` reports it as optional. It was deliberately **not** installed.
- **KVM group membership** — `/dev/kvm` is accessible here; on a machine where it is not,
  QEMU falls back to TCG and boots more slowly. Timing measured under TCG is not
  representative (see `docs/performance/BENCHMARK-METHODOLOGY.md`).
