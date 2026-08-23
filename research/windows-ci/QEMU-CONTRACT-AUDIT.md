# Native Windows QEMU contract audit

Date: 2026-08-23

Compared: `tools/run-qemu`, `tools/test`, and
`tools/windows/malrynth_tooling/runner.py` / `cli.py`

## Result

The supervised, non-interactive Windows runner reproduces the core Linux M0 machine and boot
contract. It does not yet reproduce the full Linux validation suite. One automatic firmware
candidate is invalid, interactive mode can false-pass, and mutable VARS/process cleanup is
weaker than the Linux contract. Combined status: **NOT READY** pending Gemini-owned tooling
corrections and a real native boot.

## Option and behavior mapping

| Linux contract | Windows implementation | Class | Audit result |
|---|---|---|---|
| `-machine q35` | `-machine q35` | SAME | Exact |
| `-m 1024` | `-m 1024` | SAME | Exact |
| `-cpu qemu64` | `-cpu qemu64` | SAME | Exact |
| CODE pflash, raw, read-only | same `-drive` tokens | WINDOWS EQUIVALENT | Correctly keeps CODE read-only |
| writable VARS pflash | copy then writable `-drive` | WINDOWS EQUIVALENT | Template preserved, but fixed copy is not run-specific |
| `fat:rw:<esp>` | same via Windows absolute path in one argv token | WINDOWS EQUIVALENT | No shell interpolation |
| `-display none` | same | SAME | Headless; default VGA still exposes GOP |
| `-net none` | same | SAME | Exact |
| `-no-reboot` | same | SAME | Exact |
| `-serial file:<log>` | same | WINDOWS EQUIVALENT | Exact supervised behavior |
| `-serial mon:stdio` interactive | same | WINDOWS EQUIVALENT | Launch equivalent, validation semantics differ |
| 60-second timeout | monotonic 60-second default | WINDOWS EQUIVALENT | Exact default |
| failure marker checked before success marker | same in polling loop | SAME | Correct if both are already present during polling |
| exact success marker required | required in supervised mode | SAME | Correct for non-interactive mode |
| clean QEMU exit without marker fails | same plus final log read | WINDOWS EQUIVALENT | Correct for non-interactive mode |
| terminate on every exit/signal path | terminate, then kill parent | MISSING | No Windows Job Object/process-tree kill; interrupt robustness is not demonstrated |
| per-run pristine VARS state | overwrites `build/OVMF_VARS.fd` | MISSING | Template safe, but concurrent runs race and the mutable copy remains |
| three boot repetitions | `test --boots 3` default | SAME | Available only after dependencies exist |
| deliberate panic-path test | no Windows equivalent in `test` | MISSING | `--panic-test` builds only; no boot/assertion of panic output |
| cross-path reproducibility test | Windows unit/build-path test coverage | WINDOWS EQUIVALENT | Build reproducibility is covered, not part of post-install `test` boot stage |

## Findings

### High: automatic ARM VARS mismatch

`discovery.py` accepts `edk2-x86_64-code.fd` with `edk2-arm-vars.fd`. QEMU's upstream EDK2
layout uses `edk2-i386-vars.fd` as the shared x86 variable-store template for
`edk2-x86_64-code.fd`; the ARM template is not an x86 fallback. The invalid ARM pair must be
removed before automatic discovery can be trusted. This is a Gemini tooling defect and was
not edited here.

### High: interactive false success

Interactive mode maps QEMU exit code zero directly to `ok` without observing
`MALRYNTH_M0_BOOT_OK`. That contradicts the Linux contract and can report a firmware-shell
exit as a valid boot. Interactive mode must be explicitly non-validating or supervise the
marker. This is a Gemini tooling defect and was not edited here.

### Medium: VARS and process cleanup

The original VARS template is never passed writable to QEMU; it is copied first. However,
the destination is always `build/OVMF_VARS.fd`, is not deleted, and is shared by concurrent
runs. Use a run-specific temporary directory and remove it after QEMU closes.

Timeout cleanup terminates/kills only the direct process. A Windows Job Object with
kill-on-close is the reliable process-tree contract. Existing tests cover a single sleeping
process, not a child process that outlives its parent.

### Medium: suite and CI gaps

The Windows CLI has no panic-boot validator. The CI workflow deliberately performs no boot.
Its doctor step accepts every exit code `1`, although doctor uses that code for any missing
requirement, not only QEMU/OVMF. Later explicit Rust/build steps reduce the masking risk but
do not make the doctor gate selective.

### Other reviewed risks

- Python subprocesses use argument lists and do not enable `shell=True`; no shell-injection
  path was found.
- GitHub Actions has read-only contents permission, a full-SHA checkout pin, and disabled
  persisted credentials.
- Generated `build`, `esp`, `target`, and Python cache paths are ignored and absent from Git.
- Windows Git is configured with `core.autocrlf=false` and `core.eol=lf`; no line-ending
  dependency was found in the runner.
- Documentation claiming Python 3.8+ is inaccurate: union syntax requires Python 3.10, and
  the syntax test parses with the current interpreter rather than a 3.8 grammar.

## Firmware contract

For the WinGet QEMU distribution, the expected non-Secure-Boot pair is:

- read-only CODE: `%ProgramFiles%\qemu\share\edk2-x86_64-code.fd`;
- pristine VARS template: `%ProgramFiles%\qemu\share\edk2-i386-vars.fd`;
- writable per-run copy: a Malrynth run-specific temporary file.

`edk2-x86_64-secure-code.fd` is not required. M0 currently supplies no Secure Boot keys and
the runner does not enable SMM/secure pflash, so the non-secure CODE image matches the M0
contract.

## H0.5 repeatability

After the M0 runner defects are corrected and native boot is accepted on this branch, create
a separate worktree at `docs/platform-foundation` commit
`3428b5b491b5b0847e13d6f4135f5cfef819ca40`, then invoke the Windows tooling from this
branch with that worktree as the active repository root. Do not merge the branches. Rebuild,
verify, run three boots, exercise the panic path once implemented, and re-measure the H0.5
kernel. The observed 130,704-byte value remains unaccepted until that run.
