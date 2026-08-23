# Target Triples

**Status:** PROPOSED. Not implementable before the libc decision ([Q1](../architecture/OPEN-QUESTIONS.md)).

## Proposal

```
x86_64-unknown-malrynth      primary, M5
aarch64-unknown-malrynth     ARM64, post-M4
```

Form: `<arch>-<vendor>-<os>[-<env>]`. `unknown` in the vendor field is the correct convention
for a non-vendor-specific OS and matches existing targets (`x86_64-unknown-linux-gnu`,
`x86_64-unknown-none`).

**No environment suffix initially.** An environment suffix (`-gnu`, `-musl`, `-msvc`)
distinguishes *multiple* ABIs on one OS. Malrynth will have exactly one native ABI at first,
so a suffix would encode a distinction that does not exist. If a second ABI ever appears —
most plausibly a POSIX-compatibility variant — the suffix can be added then, since
`x86_64-unknown-malrynth` remains valid as the default.

## Rust integration path

Rust organises targets into three tiers. Malrynth would enter as **Tier 3** ("best effort";
the Rust project does not build or test it automatically, and official builds are not
available), which is exactly right for a new OS.

Tier 3 requirements Malrynth must meet:

| Requirement | Malrynth plan |
|---|---|
| Implement as much of `core`/`alloc`/`std` as appropriate | `core` and `alloc` first; `std` follows libc |
| Document how to build for the target, cross-compiling if possible | `docs/toolchain/`, `malrynth` CLI |
| Document how to run binaries/tests, using emulation if necessary | QEMU harness (already exists for the kernel) |
| Document baseline CPU/OS/library expectations | this document + `SYSROOT-STRATEGY.md` |
| A target maintainer | founder initially |

**Before upstreaming**, development uses a custom target JSON, which requires nightly and
`-Z build-std`. That is a deliberate, later departure from ADR-0003's stable-only stance and
will need its own ADR — it applies to *userspace*, and the kernel can remain on stable
built-in targets.

## Baseline expectations (PROPOSED)

| Aspect | x86-64 | AArch64 |
|---|---|---|
| Baseline ISA | x86-64-v2 (SSE4.2, POPCNT) — candidate; v3 excludes older hardware | ARMv8-A |
| Endianness | little | little |
| Pointer width | 64 | 64 |
| Float ABI | hard (userspace); kernel is soft-float/no-SSE | hard |
| Executable format | ELF64 | ELF64 |
| Calling convention | SysV AMD64 | AAPCS64 |
| TLS model | ELF TLS, initial-exec/global-dynamic | ELF TLS |
| Stack | guard-paged, non-executable | same |

The x86-64 baseline is deliberately open: v2 vs v3 trades hardware reach against code quality
and should be decided with data, not taste.

## Naming consistency

`malrynth` is lowercase everywhere in identifiers, matching
[`docs/specs/naming.md`](../specs/naming.md). Architecture names use Rust's spelling —
`x86_64`, `aarch64` — never `amd64`/`arm64`, so directory names match `target_arch` exactly and
no mapping table is ever needed.
