# Windows 11 Development Bootstrap

**Status:** PROPOSED — a recommendation produced during the 2026-08-20 migration.
**Nothing in the project was modified to suit Windows.** This document records the gap
honestly so the port can be a deliberate decision rather than a scramble.

Companion document: [`WINDOWS-MIGRATION-2026-08-20.md`](WINDOWS-MIGRATION-2026-08-20.md).

---

## 1. Blunt assessment first

**The Malrynth developer tooling is Linux-shaped in practice.** All twelve scripts are
`#!/usr/bin/env bash` or `python3`. None will run under PowerShell or `cmd`. Several use
constructs with no native Windows equivalent at all.

Two consequences matter more than the rest:

1. **`find_ovmf()` in `tools/lib.sh` probes four Linux-only paths.** None exists on Windows,
   so `tools/doctor` and `tools/run-qemu` will report OVMF missing even when firmware is
   installed. This needs a Windows candidate path — it is the single most load-bearing gap.
2. **`findmnt` has no Windows equivalent.** `tools/bootstrap` and `tools/doctor` use it to
   detect a filesystem that cannot store POSIX permissions and then apply
   `core.fileMode=false`. On Windows the probe **falls through to `unknown` and silently skips
   that configuration.** A silent skip is worse than a failure, and it is exactly the class of
   bug the project's own doctor was written to catch.

**Recommendation: use WSL2 for the build and test loop.** It is the lowest-risk path, requires
no script rewriting, and preserves the reproducibility and boot-test guarantees that already
work. Native-Windows tooling is a legitimate future project — with its own milestone — not a
migration task.

---

## 2. Script portability classification

Verified by inspection of the actual scripts, not assumed.

| Script | Purpose | Portability | Specific blockers |
|---|---|---|---|
| `tools/lib.sh` | Shared library: root discovery, RUSTFLAGS single source of truth, OVMF discovery, markers | **wsl-required / git-bash** | Bash arrays; **`/usr/share/...` OVMF paths are Linux-only** |
| `tools/bootstrap` | rustup toolchain + targets + git hooks + fs-aware git config | **wsl-required** | `findmnt` — absent on Windows, so the git config it should apply is **silently skipped** |
| `tools/doctor` | Read-only host readiness report | **wsl-required** | `findmnt`; process substitution `< <(...)`; QEMU/OVMF/`/dev/kvm` probing |
| `tools/build` | Build loader + kernel, assemble ESP | **git-bash (likely)** | `stat -c` (GNU form; BSD/Windows differ). Otherwise mostly portable |
| `tools/test` | Full verification suite | **wsl-required** | `seq`; orchestrates all the above |
| `tools/run-qemu` | Boot with deterministic marker detection | **wsl-required** | Process substitution; `trap`/signal handling; bash arrays; `seq`; **QEMU invocation and OVMF paths** |
| `tools/status` | Report the exact source revision | **git-bash** | None detected — most portable script in the tree |
| `tools/scan-secrets` | Secret scan (worktree / staged / full history) | **git-bash** | Process substitution; bash arrays; needs `git cat-file`, `grep -E` |
| `tools/check-reproducible` | Byte-reproducibility regression test | **wsl-required** | `mktemp -d`; `tar` pipeline; `sha256sum`; `trap` |
| `tools/check-panic-path` | Panic/backtrace regression test | **wsl-required** | `trap`; depends on `run-qemu` |
| `tools/symbolize` | Host-side ELF symbol resolver (Python) | **native-windows** | Pure Python 3 + `struct`; **no POSIX dependency** |
| `tools/hooks/pre-commit` | Secret scan + fmt check | **git-bash** | None detected directly; calls `scan-secrets` |
| `tools/hooks/pre-push` | Reject non-fast-forward to `main`; secret scan | **git-bash** | None detected directly |

**POSIX dependencies overall:** `bash` (arrays, process substitution, `trap`), `findmnt`,
`mktemp`, `tar`, `sha256sum`, `seq`, `stat -c`, `sed`, `grep -E/-qF`, `cp`, `du`, `nproc`,
`file`, and Linux filesystem paths for OVMF.

**Also note:** this Linux host runs **uutils coreutils 0.8.0** (not GNU) and **ugrep 7.5.0**
(not GNU grep). The scripts work against both, which is mild evidence they are not tied to GNU
specifically — but it is not evidence they work on Windows.

---

## 3. Required software on Windows 11

| Component | Purpose | Notes |
|---|---|---|
| **Git for Windows** | Version control + Git Bash | Set `core.autocrlf=false` for this repo (§6) |
| **GitHub CLI (`gh`)** | Auth, repo/CI inspection | Needs scopes `gist`, `read:org`, `repo`, `workflow` |
| **rustup** | Pinned toolchain from `rust-toolchain.toml` (1.97.1) | Install **inside WSL** if building there; a Windows-side rustup builds Windows binaries |
| **Rust targets** | `x86_64-unknown-uefi`, `x86_64-unknown-none` | `tools/bootstrap` adds them |
| **QEMU** | Boot testing | QEMU for Windows exists; under WSL2 use the Linux package |
| **OVMF firmware** | UEFI firmware pair (`OVMF_CODE_4M.fd` + `OVMF_VARS_4M.fd`) | **Path discovery must be extended** — see §2 |
| **Python 3** | `tools/symbolize`, JSON validation | Works natively |
| **LLVM/Clang** | **Not required** | Rust ships `rust-lld`; M0 needs no system linker |
| **WSL2 (Ubuntu)** | Recommended build/test environment | See §4 |

---

## 4. Recommended arrangement, and why

### Recommended: source on Windows, build inside WSL2

```
D:\Malrynth                 ← git clone here (Windows-side, easy to back up and browse)
   accessed from WSL as /mnt/d/Malrynth
CARGO_TARGET_DIR=~/.cache/malrynth-target   ← inside WSL, on ext4
```

**Rationale.** A Rust `target/` directory holds tens of thousands of small files. Building onto
a Windows drive from WSL crosses the 9P/DrvFs boundary on every file operation and is
dramatically slower — the same class of problem the Linux laptop already had with ntfs-3g,
where `tools/doctor` warns about it explicitly. Keeping `target/` on WSL's own ext4 avoids it.

`CARGO_TARGET_DIR` is **already honoured** by `tools/lib.sh`, so this needs no code change.

**Deliberately not committed:** a `CARGO_TARGET_DIR` value must never go into
`.cargo/config.toml` — it is a per-machine absolute path and would break every other machine.
The repository refuses this on purpose.

### Alternative: everything inside WSL2

```
~/Malrynth  (WSL ext4)  ← fastest; Windows access via \\wsl$\...
```

Fastest and simplest, at the cost of the source being less convenient to browse and back up
from Windows.

### Not recommended yet: native Windows tooling

Would require rewriting or dual-implementing most of `tools/`. That is a real project with real
value — but it is **not** a migration task, and doing it under migration pressure is how
tooling quietly loses its guarantees.

### Path recommendation

`D:\Malrynth` is a reasonable choice; `D:\Projects\Malrynth` is equally fine. **Decide when you
sit down** — nothing in the repository hard-codes a path, and nothing should. Avoid paths with
spaces or non-ASCII characters; several scripts quote correctly but this has not been tested on
Windows.

---

## 5. Resume checklist

### Step 1 — clone (PowerShell)

```powershell
cd D:\
git clone https://github.com/macmma322/malrynth.git
cd malrynth
git fetch --all --tags --prune
```

### Step 2 — verify you have everything

```powershell
git status
git branch -a
git tag --list
git log --oneline --graph --decorate --all -n 20
```

Expect four remote branches (`main`, `docs/platform-foundation`,
`research/reference-hardware-r0`, `research/reference-hardware-r0-polish`), the
`handoff/windows-migration-2026-08-20` branch, and two tags (`v0.0.1-m0`,
`archive/orphaned-r0-drafts-2026-08-20`).

### Step 3 — read the handoff before doing anything

```powershell
git checkout handoff/windows-migration-2026-08-20
# read docs/operations/handoff/WINDOWS-MIGRATION-2026-08-20.md
```

### Step 4 — set the repository-local git configuration

`tools/bootstrap` cannot detect the filesystem on Windows (§2), so set this explicitly:

```powershell
git config core.autocrlf false
git config core.eol lf
git config core.hooksPath tools/hooks
```

Do **not** set `core.fileMode=false` on a native NTFS Windows checkout unless mode noise
appears — that setting exists for the Linux/ntfs-3g case. If `git status` starts showing
spurious mode changes, set it.

### Step 5 — WSL build environment

```bash
# inside WSL2 Ubuntu
sudo apt update && sudo apt install -y qemu-system-x86 ovmf build-essential
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

cd /mnt/d/malrynth
export CARGO_TARGET_DIR="$HOME/.cache/malrynth-target"   # add to ~/.bashrc

./tools/bootstrap     # toolchain + targets + hooks
./tools/doctor        # read-only readiness report
./tools/build
./tools/test --boots 3
```

`tools/doctor` is read-only and installs nothing. If it reports a missing item, that is the
authoritative list.

### Step 6 — worktrees (only if you want parallel branches)

**A branch already checked out somewhere cannot be checked out again.** After Step 3 the main
clone holds `handoff/windows-migration-2026-08-20`, so switch it to whichever branch you
actually want to work on first, then add worktrees for the others.

```powershell
# main clone -> the branch you will work on
git checkout docs/platform-foundation

# R0 research alongside it
git worktree add D:\Malrynth-Codex-R0 research/reference-hardware-r0

# and if you want main checked out at the same time
git worktree add D:\Malrynth-main main

git worktree list
```

### Alternative: single-clone workflow (recommended if you are not running parallel agents)

No worktrees at all — just switch branches:

```powershell
git checkout main
git checkout docs/platform-foundation
git checkout research/reference-hardware-r0
```

Simpler, no path management, and sufficient for one person working on one thing at a time.

---

## 6. Machine-local state that did NOT come from Git

Everything below mattered on Linux and is **not** in the repository. **Variable and setting
names only — no secret values are recorded anywhere.**

### Environment

| Name | Linux value | Note |
|---|---|---|
| `CARGO_TARGET_DIR` | *unset* (so `target/` sat on the slow NTFS volume) | **Set this on Windows** (§4) |
| `CARGO_HOME` | default `~/.cargo` (registry ≈ 246 MB) | Rebuilt automatically |
| `RUSTUP_HOME` | default `~/.rustup` (≈ 2.5 GB, two toolchains) | Rebuilt by `tools/bootstrap` |
| OVMF code | `/usr/share/OVMF/OVMF_CODE_4M.fd` | **No Windows equivalent — `find_ovmf()` needs a new candidate** |
| OVMF vars | `/usr/share/OVMF/OVMF_VARS_4M.fd` | Copied per run to `build/OVMF_VARS.fd` |
| QEMU | `/usr/bin/qemu-system-x86_64` v10.2.1 | Must be on `PATH` |

### Git configuration (not cloned)

| Setting | Linux value | Windows action |
|---|---|---|
| `core.hooksPath` | `tools/hooks` | **Set manually** — hooks are inert until then |
| `core.fileMode` | `false` | Only if mode noise appears on NTFS |
| `core.autocrlf` | `false` (local) — global was `input` | **Set to `false` locally**; Windows default is `true` and would rewrite line endings |
| `core.eol` | `lf` | Set locally |
| `credential.helper` | `!/usr/bin/gh auth git-credential` | Windows uses its own; re-run `gh auth login` |
| `user.name` / `user.email` | set locally and globally | Re-establish |
| **Commit signing** | **none configured** — no GPG keys, no SSH keypair | Tags and commits are unsigned. Documented target state: `docs/operations/github-ownership.md` |
| `git-lfs` filters | configured globally but **git-lfs is not installed** | Harmless (no `.gitattributes` LFS entries). Do not replicate. |

### Platform differences to expect

| Linux | Windows |
|---|---|
| KVM via a udev ACL on `/dev/kvm` (invisible in `id`, not a group membership) | **WHPX** (`-accel whpx`), which conflicts with some other hypervisors. Under WSL2, nested virtualization must be enabled or QEMU falls back to TCG |
| ntfs-3g/FUSE: no POSIX mode bits, slow builds | Native NTFS: modes behave differently again; `/mnt/d` from WSL is slow for `target/` |
| uutils coreutils, ugrep | GNU-ish tools inside WSL |

### GitHub authentication

The `gh` token lives in the **system keyring**, not on disk, and the credential helper path is
hardcoded to `/usr/bin/gh`. **Neither transfers.** On Windows:

```powershell
gh auth login          # scopes needed: gist, read:org, repo, workflow
gh auth status
```

**Never** put a token in a remote URL or a config file. The remote must stay
`https://github.com/macmma322/malrynth.git`.

### Not in Git, and intentionally so

Worktree registrations (they live in `.git` and never travel with a clone), build outputs
(`target/` 243 MB, `esp/`, `build/`), the rustup and cargo installations, installed system
packages, and KVM access.

---

## 7. Verification target on Windows

The migration is only proven when this passes on the Windows machine:

```bash
./tools/doctor                 # exit 0
./tools/build
./tools/test --boots 3         # expect: all checks passed
./tools/check-reproducible     # expect: byte-identical across build directories
./tools/check-panic-path       # expect: panic path verified
```

Expected measured values to compare against (from the Linux host):

| Artifact | Bytes |
|---|---|
| `esp/EFI/BOOT/BOOTX64.EFI` | 40,960 |
| `esp/malrynth/kernel.elf` | 130,688 |

**If the Windows sizes differ, that is a finding, not a failure** — cross-host reproducibility
was never verified and `docs/roadmap/M0.md` explicitly says it must not be claimed. Reproducibility
is currently proven **across build directories on one host with the pinned toolchain**, nothing
wider. A Windows/WSL build producing different bytes would be genuinely useful information about
what still needs remapping.

**Until this checklist passes on Windows, keep the Linux laptop.** It remains the fallback.
