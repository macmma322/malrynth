# Development Environment

**Status:** ACCEPTED. Malrynth has **two** validated development environments. Native Windows
is the canonical one; Linux remains the reference one. Re-verify either with its own doctor on
any new machine.

This document previously described a single LOCKED Linux host. That stopped being true when
native Windows development was validated, and a status label that overstates certainty is
worse than no label at all.

## The two environments

| | **Canonical** | **Reference** |
|---|---|---|
| Platform | Native Windows 11, x86_64 | Ubuntu 26.04 LTS, x86_64 |
| Workspace root | `D:\Malrynth` | `/media/Data/Malrynth` |
| Entry point | `python tools\windows\malrynth.py <command>` | `./tools/<script>` |
| Readiness check | `malrynth.py doctor` | `./tools/doctor` |
| Rust | 1.97.1, pinned by `rust-toolchain.toml` | 1.97.1, pinned by `rust-toolchain.toml` |
| Automated CI | `.github/workflows/windows-native-m0.yml` | `.github/workflows/ci.yml` |

Neither is a subset of the other, and neither is being retired. The Linux environment is what
M0 was originally proved on and is what `ci.yml` still exercises on every push and pull request
to `main`; the Windows environment is where development now happens day to day.

Deliberately **not** recorded here: exact QEMU/OVMF build strings, CPU counts, free disk space
and other host facts that change without anything meaningful changing. Each doctor reports
those live, which is where a reader should get them.

## Canonical: native Windows

Development runs natively. WSL2 is **not** required and is not the supported path.

The Windows tooling is a dependency-free Python package under `tools/windows/`, invoked through
`malrynth.py` (or the `malrynth.cmd` / `malrynth.ps1` launchers). It requires Python 3.10 or
newer; `malrynth.py` enforces the version gate itself.

```powershell
python tools\windows\malrynth.py doctor            # read-only readiness report
python tools\windows\malrynth.py build             # loader + kernel + ESP
python tools\windows\malrynth.py test              # fmt, clippy, unit tests, build, boot, panic
python tools\windows\malrynth.py run               # supervised QEMU boot
python tools\windows\malrynth.py verify            # structural checks on built artifacts
python tools\windows\malrynth.py check-panic-path  # deliberate panic + symbolisation
```

Validated natively on Windows: toolchain and host discovery, the loader and kernel builds, ESP
assembly, supervised QEMU/OVMF boot to `MALRYNTH_M0_BOOT_OK`, the deliberate panic path with
backtrace symbolisation, same-host build reproducibility, and the tooling test suite.

Two things the Windows path does **not** have, stated plainly:

- **No `bootstrap` equivalent.** The Linux `tools/bootstrap` installs the rustup toolchain,
  targets and git hooks. On Windows that setup is manual: install rustup and Python, then add
  the `x86_64-unknown-uefi` and `x86_64-unknown-none` targets. `doctor` reports what is
  missing; it never installs anything.
- **The `tools/*` shell scripts are Linux-shaped.** `find_ovmf` probes Linux firmware paths and
  the filesystem probe has no Windows equivalent, so running them under Git Bash is not
  supported. `malrynth.py` is the Windows entry point, not a wrapper around them.

`tools/lib.sh` and `tools/windows/malrynth_tooling/config.py` each define half of the shared M0
compiler/linker contract. Neither is authoritative; both must be updated together. See
`.cargo/config.toml`.

## Reference: Linux (verified 2026-08-19)

| | |
|---|---|
| OS | Ubuntu 26.04 LTS, Linux 7.0.0-29-generic |
| Architecture | x86_64, 12 CPUs |
| Repository root | `/media/Data/Malrynth` |
| Rust | 1.97.1 (pinned via `rust-toolchain.toml`) |
| QEMU | 10.2.1 |
| OVMF | 2025.11 (`/usr/share/OVMF/OVMF_CODE_4M.fd`, `OVMF_VARS_4M.fd`) |
| KVM | available |

Not installed and **not required**: `clang`, `lld`, `llvm-config`, `cmake`, `ninja`. The Rust
toolchain ships `rust-lld` and `rust-objcopy`, which is the entire link toolchain Malrynth
needs (ADR-0003). `mtools` is absent and is optional — see "Known gaps".

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
rustup state. System packages are never installed automatically; `tools/doctor` reports what is
missing and how to obtain it, and the decision stays with the developer.

## Filesystem, line endings and file modes

Both environments keep the repository on **NTFS**, so the same constraints apply to both. On
Linux the volume is mounted through ntfs-3g (FUSE); on Windows it is native.

| Property | Result |
|---|---|
| Symlinks | work |
| Case sensitivity | case-sensitive under ntfs-3g; case-insensitive on native Windows |
| **POSIX mode bits** | **not stored — `chmod` is a silent no-op; everything reads `0777`** |

### Consequence for Git, and the mitigation

With default settings Git would see every file as mode `0777` and record **every file as
`100755`**, so a fresh clone on ext4 would have every source file executable. The repository is
therefore configured with:

```
git config core.fileMode false
git config core.autocrlf false
git config core.eol lf
```

`core.fileMode=false` makes Git record `100644` for new files and ignore mode changes. Scripts
that genuinely need the executable bit are marked explicitly in the index:

```
git update-index --chmod=+x tools/build
```

Both doctors check `core.fileMode` and fail if it is not `false` on such a filesystem, because
the failure is otherwise silent and only visible to whoever clones next.

`core.autocrlf=false` with `core.eol=lf` overrides any global `autocrlf=input` so the
repository is byte-identical regardless of host or mount, and `.gitattributes` enforces
`* text=auto eol=lf` for any other clone.

### Consequence for build performance

Under ntfs-3g every file operation crosses into userspace, and a Rust `target/` directory
contains tens of thousands of small files, so Linux builds on the NTFS volume are materially
slower than on ext4. `target/` is git-ignored, so it can live anywhere:

```bash
export CARGO_TARGET_DIR="$HOME/.cache/malrynth-target"
```

`tools/lib.sh` and the Windows tooling both honour `CARGO_TARGET_DIR`, and `tools/doctor`
suggests this when it detects a FUSE/NTFS root. It is **not** set in `.cargo/config.toml`,
because a committed absolute path would break every other machine.

## Worktrees

Branches under active review are checked out as **sibling worktrees** next to the canonical
workspace (`D:\Malrynth-<topic>`), never nested inside it. A branch may occupy only one worktree
at a time.

## Known gaps

- **`mtools` is absent on the Linux host**, so no real distributable FAT ESP image can be
  produced there. The boot test uses QEMU's virtual FAT (`fat:rw:`), which needs neither root
  nor extra packages. Producing a `.img`/`.iso` requires `mtools` (or root for a loop mount)
  and is deferred; `tools/doctor` reports it as optional. It was deliberately **not** installed.
- **KVM group membership** — `/dev/kvm` is accessible on the Linux host; on a machine where it
  is not, QEMU falls back to TCG and boots more slowly. The Windows host runs TCG by default
  unless WHPX is configured. Timing measured under TCG is not representative (see
  `docs/performance/BENCHMARK-METHODOLOGY.md`).
- **No Windows `bootstrap`** — toolchain setup on Windows is manual, as described above.
