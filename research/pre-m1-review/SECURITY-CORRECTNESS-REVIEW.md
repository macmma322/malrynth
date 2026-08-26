# Pre-M1 Security and Correctness Review

**Review target:** `origin/main...origin/integration/pre-m1-foundation`  
**Verified base:** `7a421b4e86cdb9114bf2657536a3643c50e2558d`  
**Verified candidate:** `0f25552edd20a9f40bdbf002d70f1f38fb8970ad`  
**Relationship:** candidate is 27 commits ahead and 0 behind.  
**Scope:** adversarial executable/tooling review first; security architecture checked for contradictions, not prose aesthetics.

## Decision

**REQUEST CHANGES before M1A.** No CI privilege-escalation blocker or kernel non-PIE blocker was found. The Windows boot validator has a reproducible false-pass race, the panic test does not cryptographically or immutably bind the booted image to the symbolized image, and the loader silently truncates a memory map that M1A is expected to treat as complete.

## Findings

### HIGH — Windows boot result can remain `ok` after a failure marker arrives

- **Evidence:** `tools/windows/malrynth_tooling/runner.py:139-154` classifies the first log snapshot, stops on `MALRYNTH_M0_BOOT_OK`, then terminates QEMU. Lines 156-176 reread the final log but do not reclassify it.
- **Impact:** a failure marker appended after the success snapshot but before/during teardown is present in `cleaned_output` while `status == "ok"`. This violates the documented rule that no higher-priority failure condition may exist.
- **Why tests miss it:** `tests/windows-tooling/test_runner.py:77-91` puts both markers in the same initial snapshot.
- **Minimal test:** make the child write and flush OK; arrange `_terminate_process_tree` to append FAIL; assert the returned status is `fail-marker`.
- **Required correction:** after termination, read and normalize the final log, classify it again, and let an exact-line FAIL marker override every success observation. Preserve cancellation/timeout as failures even if an OK marker is appended only after the deadline/cancellation decision.

### HIGH — Panic output and symbolization are not bound to one immutable image

- **Evidence:** `panic.py:47-53` builds and boots the shared `esp`; `panic.py:65-76` later symbolizes the current `esp/malrynth/kernel.elf`; `panic.py:85-89` rebuilds that shared tree. `build.py:83-97` deletes and reconstructs the shared ESP non-atomically.
- **Impact:** a concurrent build or panic check can replace the kernel after boot and before symbolization. A wrong but address-compatible ELF can still satisfy the weak “at least one `+0x...`” check. Concurrent restoration can also leave an unintended image published.
- **Minimal test:** return valid panic output from a mocked boot, swap the ESP kernel before the symbolizer call for a different valid ELF covering one address, and demonstrate a pass. A barrier-based two-invocation test should verify image identity and final restoration.
- **Required correction:** stage a panic image in a unique run directory, hash the kernel, boot that exact staged ESP, and symbolize that exact immutable path. Publish/restore the normal ESP atomically or serialize publication. Report both booted and symbolized SHA-256 values and require equality.

### HIGH — Loader silently truncates the firmware memory map

- **Evidence:** `core/boot/uefi/src/main.rs:53-58` states overflow is reported; `normalise_memory_map` at lines 264-267 instead breaks silently at 256 entries. `BootInfo` has no truncation flag. The kernel only prints the capped count.
- **Impact:** M1A cannot distinguish a complete canonical input from a prefix. Omitted usable memory is conservative, but omitted ownership information makes “every physical frame has one classification” unprovable and diagnostics misleading. Firmware descriptor count is explicitly an untrusted input.
- **Minimal test concept:** feed 257 synthetic descriptors to extracted pure normalization logic and assert an explicit `TooManyRegions` error rather than a 256-entry success.
- **Required correction:** before M1A, make overflow boot-fatal or version the ABI with an explicit incomplete-map status that M1A rejects. Prefer boot-fatal: a partial physical ownership map is not a valid allocator input.

### MEDIUM — “Exact” markers are substring matches

- **Evidence:** `runner.py:53-59` uses Python `in`; `panic.py:32,34-35` does the same for message/markers.
- **Reproduction:** `_classify_output("NOT_MALRYNTH_M0_BOOT_OK_BOGUS") == "ok"`.
- **Correction:** strip ANSI first, then match full logical lines (`^MALRYNTH_M0_BOOT_(OK|FAIL)\r?$`) with FAIL precedence. Add prefix/suffix, embedded, split-write, CRLF, and ANSI cases.

### MEDIUM — QEMU drive paths do not escape commas

- **Evidence:** `runner.py:117-121` places filesystem paths inside QEMU comma-delimited `-drive` option strings. `shell=False` correctly prevents shell injection, and spaces/metacharacters remain argv data, but commas are QEMU syntax.
- **Impact:** a legal path containing a comma can alter parsing or make boot fail.
- **Correction:** use QEMU's required escaping for drive values or reject commas with an explicit diagnostic. Test repository, firmware, temp, and log paths containing spaces, commas, quotes, and shell metacharacters.

### MEDIUM — Windows CI is not an automatic PR/merge gate

- **Evidence:** `.github/workflows/windows-native-m0.yml:5-8` runs only on pushes to `ci/windows-native-m0-hardened` or manual dispatch.
- **Impact:** it does not validate untrusted pull requests or future pushes to `main`/the integration branch. This is gating correctness, not a token/security escalation.
- **Correction:** add `pull_request` and the intended protected push branches; preserve current least-privilege controls.

### LOW — Firmware discovery has check/use races but no trust guarantee is claimed

`find_qemu` and `find_ovmf` validate paths and later launch/read them. A local actor able to replace those files can win the interval. `shell=False` prevents command-string injection, but it does not establish executable/firmware identity. For local developer tooling this is not a security boundary. If CI later downloads firmware/QEMU, pin hashes and stage immutable copies before launch.

## Boot success state machine audit

| Case | Current result | Assessment |
|---|---|---|
| no output + exit 0 | `process-exited` | safe failure |
| exact success marker | `ok` | intended, subject to final-log race |
| failure/panic marker | `fail-marker` | intended |
| both in one snapshot | failure wins | correct |
| OK observed, FAIL appended during teardown | `ok` | false pass; blocker |
| marker then hang | process tree terminated | correct terminal behavior |
| exit before log flush | one 50 ms reread | possible false negative, not false pass |
| cancellation | `cancelled` | safe failure |
| exact deadline boundary | possible timeout | false negative; define boundary as deadline-exclusive and document it |

The only normal success token remains `MALRYNTH_M0_BOOT_OK`, but current substring matching and missing final reclassification make enforcement weaker than the stated contract.

## Panic-test trust assessment

Fresh per-run serial logs and per-run copied NVRAM prevent ordinary stale-log and stale-VARS passes. The test also requires the deliberate message, source location, failure marker, multiple frames, and absence of OK. However, shared mutable ESP state means it does **not** prove that the symbolized ELF is the booted ELF. Restoration failure correctly forces a nonzero result, but restoration is non-atomic and races concurrent builds. Until artifact identity is bound, the intended M0 diagnostic contract is only partially proven.

## CI adversarial review

- Workflow permissions are read-only (`contents: read`).
- Checkout credentials are disabled.
- No `pull_request_target`, secrets, write-capable token use, or privileged interpolation was found.
- `actions/checkout` is pinned to a full commit SHA.
- Branch-controlled scripts execute only in the ordinary ephemeral job context with no repository secrets exposed by this workflow.
- The missing PR trigger is a coverage defect, classified separately above.

**CI security blocker: NO.**

## Kernel build invariant

`core/kernel/build.rs:7-12` scopes linker arguments to the kernel package, derives the linker script from Cargo's package manifest directory, and forces `--no-pie` even for a bare Cargo build. It does not silently affect unrelated crates. Windows tooling separately supplies `relocation-model=static`; the loader and artifact verifier reject non-`ET_EXEC` images. This defense-in-depth matches ADR-0003's operational invariant.

Two limitations are non-blocking:

1. ADR-0003 describes both static relocation model and `--no-pie`, while bare Cargo structurally guarantees only the linker half. The produced ELF must remain verified as `ET_EXEC`; add a bare-build regression test if this path is supported.
2. A deliberately hostile build environment can inject later linker arguments. Build reproducibility assumes a controlled toolchain environment; it is not a defense against a developer who controls Cargo/rustc inputs.

**Kernel build-invariant blocker: NO.** Revisit the fixed-address invariant when M1 adopts higher-half mappings/custom targets; do not carry `--no-pie` forward accidentally if the new loader design requires relocation.

## Architecture review

The capability, native-app, package/update/recovery, Shield, storage, and account/sync documents are directionally consistent: ambient authority is rejected; revocation/broker cost is acknowledged; package and system trust roots are separated; update rollback versus anti-rollback is explicitly unresolved; filesystem parsing is outside the kernel; protected snapshot deletion is separately privileged; local identity remains independent from cloud identity; sync is not backup. These are proposed future contracts, not executable security controls. No candidate merge blocker was found in them. Their unresolved items must become ADRs and tests before their target milestones, especially revocation semantics, signing-key custody, anti-rollback, E2E recovery, and organization/BYOD policy.

## Classification

### BLOCKERS

1. Boot false-pass race after OK observation.
2. Panic boot/symbolization artifact identity race.
3. Silent memory-map truncation prevents a trustworthy M1A input contract.

### PRE-M1 fixes

Exactly **3 required fixes**, corresponding to the blockers above. The exact-line marker correction, QEMU comma handling, and CI trigger coverage should land in the same preparation window but are not counted as security/correctness blockers.

### Deferred debt

- Stronger local provenance for QEMU/firmware if these tools become downloaded CI dependencies.
- Process-exit log draining based on handle closure/stable reads instead of a fixed 50 ms delay.
- Atomic ESP publication and explicit cross-process build locking for all tooling, not only panic tests.
- Convert proposed security-architecture decisions into milestone-specific ADRs and executable acceptance tests.

## Final answers

SECURITY/CORRECTNESS BLOCKER FOUND: YES

WINDOWS BOOT VALIDATOR FALSE-PASS RISK FOUND: YES

CI SECURITY BLOCKER FOUND: NO

KERNEL BUILD-INVARIANT BLOCKER FOUND: NO

PRE-M1 FIXES REQUIRED: 3

M1A IMPLEMENTATION BRIEF READY: YES

SAFE FOR CLAUDE TO MAKE FINAL MERGE DECISION: YES

INTEGRATION CANDIDATE MODIFIED: NO

MAIN MODIFIED: NO

M1 CODE WRITTEN: NO
