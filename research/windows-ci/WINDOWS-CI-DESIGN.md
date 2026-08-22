# Windows Native M0 CI Design

## Status and scope

This workflow is an experimental CI consumer of `feature/windows-native-tooling-spike`. It does
not adopt the Windows toolchain into the production build architecture. Its purpose is to test
the spike independently on a fresh GitHub-hosted Windows machine before later integration is
considered.

The workflow proves that one clean Windows host can:

- select the repository-pinned Rust 1.97.1 toolchain, including `rustfmt`, `clippy`,
  `x86_64-unknown-uefi`, and `x86_64-unknown-none`;
- use the runner's modern Python 3 runtime and Git installation;
- run the complete inherited `tests/windows-tooling` unittest suite, including the explicit
  path-with-spaces test and Python 3.8 grammar/AST compatibility check;
- build `esp\EFI\BOOT\BOOTX64.EFI` and `esp\malrynth\kernel.elf` without WSL;
- validate a non-empty PE32+ loader and a non-empty ELF64 `ET_EXEC` kernel using the spike's
  existing verifier; and
- produce byte-identical loader and kernel artifacts when the existing reproducibility test
  builds the same source from two different paths on the same Windows host.

Artifact sizes and SHA-256 values are printed for diagnosis and run-to-run evidence. Exact sizes
and hashes are not hard-coded gates because they may change intentionally with source changes.
The structural formats, executable type, non-zero size, and same-host byte equality are gates.

## Runner and environment

The job uses the explicit `windows-2025` x64 GitHub-hosted runner label. GitHub's hosted-runner
reference listed this as a supported stable label for private repositories when this workflow was
created; using an explicit image avoids an unreviewed migration when `windows-latest` changes.
Each hosted job starts on a fresh virtual machine.

The workflow uses preinstalled `rustup`, explicitly installs and selects Rust 1.97.1, and asks
rustup for the components and targets declared by `rust-toolchain.toml`. It does not use Gemini's
machine-local isolated Rust installation. No Cargo cache is used, so this is deliberately clean
build evidence.

The workflow uses the modern `python` already supplied by the runner. It does not install an
obsolete Python 3.8 runtime. Python 3.8 compatibility is syntax-level evidence supplied by the
inherited AST compatibility test; runtime behavior is tested only on the runner's reported modern
Python version.

## Test and reproducibility claim

The authoritative Windows tooling test command is:

```text
python -m unittest discover -s tests/windows-tooling -p "test_*.py" -v
```

That suite owns the expected assertions. CI does not copy them. In particular,
`test_reproducibility.py` builds in the checkout and in an alternate temporary source path and
compares SHA-256 values byte-for-byte. The precise claim is **Windows same-host build-path
reproducibility**. It is not cross-host reproducibility and does not prove Linux and Windows emit
identical artifacts.

After the suite, CI performs the documented canonical build and verifier invocations separately
so build and artifact failures are visible as distinct workflow steps.

## What is not tested

QEMU boot is not tested. GitHub's standard Windows image is not assumed to contain the project's
required QEMU and OVMF combination, and this workflow installs neither. `doctor` output is retained
as a diagnostic, but its expected missing boot environment does not fail this build-only phase.
No Chocolatey, Scoop, Winget, third-party firmware, or embedded firmware blob is introduced.

This workflow also does not prove cross-host, Linux-to-Windows, or long-term reproducibility. It
does not replace Linux M0 CI: the established Linux workflow remains responsible for its complete
format, lint, test, QEMU/OVMF boot, and repeated-boot contract. Bash-only repository checks remain
Linux-owned except for the existing secret scanner, which is invoked explicitly through the Git
Bash environment already supplied by the Windows runner.

## Trust and security boundary

The workflow has only `contents: read`. It requires no secrets, write permissions, OIDC token,
package access, or release publication. Checkout uses the repository's existing full-SHA-pinned
official action and disables credential persistence. No artifact upload or cache action is used.
All repository code runs as untrusted input inside the ephemeral runner with no repository secrets.

Triggers are intentionally limited to manual dispatch and pushes to `ci/windows-native-m0`; the
experimental workflow does not run on every repository branch or change established `main` CI.
It does not use `pull_request_target`. If pull-request coverage is added later, ordinary
`pull_request` with the same read-only and secret-free boundary is required.

PowerShell steps do not interpolate branch-controlled values into commands. Artifact paths and the
pinned toolchain are fixed workflow literals. The only Bash-only check invoked on Windows is the
existing repository secret scanner, explicitly under Git Bash. Build products are neither uploaded
nor published.
