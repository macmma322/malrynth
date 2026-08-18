# Third-Party Code Policy

**Status:** LOCKED.

## Principle

Every dependency runs with the privileges of whatever links it. In a kernel that is total
authority. The primary control is therefore **not having dependencies**, and only then
auditing the ones that survive that test.

The opposite failure is equally real: hand-rolling cryptography, Unicode handling,
compression, or firmware bindings to claim purity produces worse code than the library it
replaced. The policy targets the *decision*, not a dependency count.

## Rules

### 1. The kernel takes no external dependency without an ADR
It currently has zero. An ADR must show the primitive cannot be implemented safely in-tree
and that the dependency's own dependency tree is acceptable in ring 0.

### 2. Do not reimplement what must be correct
Cryptography, Unicode, compression, and standards bindings are used, not reinvented. A
hand-rolled cipher is a vulnerability; a maintained implementation is a dependency to record.

### 3. Do not add a dependency for convenience
If the kernel can reasonably implement a primitive safely, it does.

### 4. Every dependency is recorded before it is committed
`THIRD_PARTY.md` records name, version, source, license, purpose, necessity, and whether it
appears in privileged code.

### 5. Copying is different from depending
Copying code — even a function, even with attribution — creates a derivative work. It
requires recording the exact source, exact license, obligations, and modifications, **and**
verifying compatibility with every licensing option still open (`docs/legal/LICENSING-STATUS.md`).
A single incompatible copy can foreclose an entire licensing branch permanently.

### 6. Studying is not copying
Reading how Linux, Fuchsia, seL4 or Redox solved a problem is research and is encouraged;
cite it in `docs/research/`. Transcribing their code is copying and follows rule 5.

### 7. Pin exactly
`Cargo.lock` is committed. The toolchain is pinned to an exact version. GitHub Actions are
pinned by commit SHA, never by tag — tags are mutable and a compromised action repository can
retag silently.

### 8. Prefer permissive licenses while licensing is unresolved
Until Malrynth's own license is chosen, avoid dependencies whose terms would foreclose
options. Copyleft in privileged code requires an ADR.

## Review triggers

Any new dependency, any version bump crossing a major version, any new transitive dependency
in privileged code, and any license change in an existing dependency.
