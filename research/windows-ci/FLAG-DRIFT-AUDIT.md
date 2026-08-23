# Windows-native M0 flag-drift audit

Date: 2026-08-23

Branch baseline: `ci/windows-native-m0` at `78c15210375032ae4a56708c5ea04324d4aaea3b`

Windows tooling baseline: `a016b10dae35e7149bc5bb5aee9078f8e0996ec2`

## Result

The Linux authority (`tools/lib.sh`) and Windows implementation
(`tools/windows/malrynth_tooling/config.py`) agree on the effective M0 target triples,
compiler/linker invariants, remap destinations, and serial markers. They do not share a
machine-readable source, so a one-sided edit can silently break cross-host equivalence.

Windows intentionally adds forward-slash variants of each host remap source. Those variants
are platform-specific inputs to the same canonical destinations, not drift.

## Classification

| Value | Linux | Windows | Class | Required invariant |
|---|---|---|---|---|
| Loader target | `x86_64-unknown-uefi` | same | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Exact target triple |
| Kernel target | `x86_64-unknown-none` | same | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Exact target triple |
| Kernel relocation | `-C relocation-model=static` | same encoded argv | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Static relocation model |
| Kernel frames | `-C force-frame-pointers=yes` | same encoded argv | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Frame-pointer unwinder remains valid |
| Loader reproducibility | `-C link-arg=/Brepro` | same encoded argv | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Reproducible PE timestamp/debug marker |
| Loader debug suppression | `-C link-arg=/DEBUG:NONE` | same encoded argv | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | No path-dependent CodeView/PDB payload |
| Workspace remap destination | `/malrynth` | same | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Canonical destination |
| Cargo-home remap destination | `/cargo` | same | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Canonical destination |
| Rust-sysroot remap destination | `/rust` | same | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Canonical destination |
| Workspace remap source | resolved repository root | resolved repository root plus slash variant | DERIVED; PLATFORM-SPECIFIC | Resolve the active worktree, never a recorded machine path |
| Cargo-home remap source | `$CARGO_HOME`, else `$HOME/.cargo` | `%CARGO_HOME%`, else `Path.home()/.cargo` | DERIVED; PLATFORM-SPECIFIC | Resolve the active Cargo home |
| Rust-sysroot remap source | `rustc --print sysroot` | same | DERIVED | Resolve selected toolchain sysroot; failure sentinel is `/nonexistent` |
| Rustflags transport | space-expanded `RUSTFLAGS` | unit-separated `CARGO_ENCODED_RUSTFLAGS` | PLATFORM-SPECIFIC | Preserve paths containing spaces |
| Success marker | `MALRYNTH_M0_BOOT_OK` | same | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Exact, case-sensitive marker |
| Failure marker | `MALRYNTH_M0_BOOT_FAIL` | same | MUST MATCH; CANDIDATE FOR SHARED MANIFEST | Exact, case-sensitive marker |
| Output roots | repository `target`, `esp`, `build` | same semantics via `pathlib` | DERIVED; PLATFORM-SPECIFIC | Stay under active worktree unless explicitly overridden |

## Drift hazards

1. Neither implementation validates itself against the other.
2. Comments in `tools/lib.sh` call the file a single source of truth, but Windows now has a
   second executable definition.
3. A target, marker, remap destination, or code-generation flag can change on one host while
   all host-local tests remain green.
4. Plain string comparison would be wrong because Windows legitimately encodes flags and
   duplicates host-source remaps using forward slashes.

## Future single-source design

Add a repository-owned, declarative `tools/m0-contract.toml` containing target triples,
ordered logical flags, canonical remap destinations, and boot markers. Keep host paths and
flag transport out of it. Linux and Windows adapters should:

1. load the manifest;
2. derive host-specific remap sources;
3. render Bash `RUSTFLAGS` or Cargo unit-separated encoded flags;
4. fail if the manifest is missing or contains an unknown contract key.

A host-neutral test should load both adapters, normalize tokens into logical flag records,
and assert equality against the manifest. Do not generate checked-in source files: runtime
loading plus a CI contract test avoids generated-file drift.

This migration is intentionally deferred; Linux remains authoritative during the spike.

## Independent loader measurement

The canonical Windows CLI build produced a 40,960-byte PE with `.rdata` virtual size
`0x2B4C` (11,084), `.rdata` raw size `0x2C00` (11,264), and `FileAlignment=0x200` (512).
A direct build with remapping and `/Brepro /DEBUG:NONE` omitted produced 41,472 bytes with
`.rdata` virtual size `0x2CD9` (11,481) and raw size `0x2E00` (11,776). Restoring the canonical
CLI flags restored the 40,960-byte artifact.

This independently reproduces the reported mechanism and the exact +512-byte file-size/raw
allocation step. The local unremapped virtual-size delta was +397 bytes, not the previously
recorded +344 bytes, because embedded absolute path payload length is host/build-path
dependent. Therefore +344 is a valid observation from the earlier environment, while the
portable root cause is: unremapped host paths cross the 512-byte `.rdata` raw-alignment
boundary.
