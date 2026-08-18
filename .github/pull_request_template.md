## What this changes

<!-- What and why. If it changes a boundary, ABI, dependency, or topology, link the ADR. -->

## Milestone

<!-- M0 / M1 / ... / not milestone work -->

## Verification

- [ ] `./tools/test` passes locally
- [ ] Boot smoke test observed `MALRYNTH_M0_BOOT_OK`
- [ ] Documentation status labels are still accurate (LOCKED / PROPOSED / EXPERIMENTAL / DEFERRED / UNSOLVED)

## Security

- [ ] No new `unsafe`, **or** every new `unsafe` block has a `SAFETY:` comment and is in a
      location permitted by `docs/security/UNSAFE-RUST-POLICY.md`
- [ ] No new dependency, **or** it is recorded in `THIRD_PARTY.md` and is not linked into the kernel
- [ ] No secret, credential, build output, or binary is included
- [ ] Untrusted input crossing a boundary is validated on the receiving side

## Claims

- [ ] Nothing in this PR or its documentation claims a capability that was not actually run
