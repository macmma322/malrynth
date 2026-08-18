# Malrynth Threat Model

**Status:** DRAFT. Revised every milestone.
**Scope of *current* validity:** M0 only. Most mitigations below are PLANNED and explicitly
labelled as such. **Malrynth currently mitigates almost nothing, because almost nothing
exists.** Saying so is the point of this document.

## Assets

1. User data at rest and in use.
2. Kernel integrity — the ability to execute in ring 0.
3. The capability system's integrity (once it exists): no authority amplification.
4. Boot and update chain integrity.
5. Developer and release-signing credentials.
6. Source integrity.

## Attacker capabilities assumed

- **Remote:** can supply arbitrary network input and arbitrary files.
- **Local unprivileged:** can run arbitrary native code as an unprivileged program.
- **Physical, opportunistic:** can attach USB or Thunderbolt devices, and can reboot.
- **Physical, sustained:** can desolder flash, probe buses, and mount a cold-boot attack.
  **Out of scope.** Malrynth does not claim to defend against an attacker with unlimited
  physical access and time.
- **Supply chain:** can attempt to compromise a dependency, the build pipeline, or a
  developer account.

## Threats

### T1 — Malicious user-mode application
Runs attacker code with a user's consent. *Planned mitigation:* no ambient authority; a
program's power equals its capabilities (M3). *Current:* no user mode exists.

### T2 — Malicious file
Crafted document/image/filesystem exploits a parser. *Planned:* parsers run in user space,
capability-confined, and are fuzzed; the kernel never parses untrusted formats. *Current:*
no parsers exist. **The M0 loader's ELF parser is the sole exception and is in scope now** —
it is bounds-checked, rejects malformed images, and reads no field by unaligned cast.

### T3 — Malicious network input
*Planned:* the network stack is an unprivileged user-space service; a compromise yields the
network stack's capabilities, not the kernel. *Current:* no networking.

### T4 — Malicious USB / Thunderbolt device
Device claims a privileged class or exploits a driver. *Planned:* user-space drivers,
IOMMU-confined DMA, no automatic driver binding for privileged classes on an unattended
machine. *Current:* no USB support.

### T5 — Compromised driver
*Planned:* drivers are unprivileged user-space programs; compromise is contained to that
device's capabilities and the driver is restartable. *Current:* no driver framework. M0's
in-kernel UART is a documented exception.

### T6 — DMA attack
A device reads or writes memory it was never granted. *Planned:* IOMMU confinement, enabled
before any device is granted DMA. **Where no IOMMU exists, Malrynth must state that devices
are fully trusted rather than imply protection it does not have.** *Current:* no DMA, no
IOMMU configuration.

### T7 — Kernel bug
Memory corruption or logic error yielding ring-0 execution. *Mitigations:* safe Rust by
default; `unsafe` confined to audited modules with mandatory `SAFETY:` justification
(`UNSAFE-RUST-POLICY.md`); a small kernel; `overflow-checks = true` even in release, because
a silent wrap in a kernel is a bug regardless of profile. **Rust does not eliminate this
class — it narrows it.**

### T8 — Filesystem corruption
*Planned:* checksums, copy-on-write transactions, crash-consistency testing with fault
injection, and a reference-model comparison. MalrynthFS is R&D and must not hold data
anyone cares about. *Current:* no filesystem.

### T9 — Build-pipeline compromise
A malicious build produces a backdoored image. *Mitigations now:* pinned exact toolchain;
pinned Actions by commit SHA; no self-hosted runners; no secrets in CI. *Planned:*
reproducible builds so an independent rebuild can detect divergence, then provenance
attestation.

### T10 — Malicious dependency
*Mitigations now:* the kernel has **zero** external dependencies; the loader has exactly one
(`uefi`), which stops executing at `ExitBootServices`; every dependency is recorded in
`THIRD_PARTY.md` with license, purpose, and whether it is privileged. *Planned:* `cargo-deny`
in CI, and a vendoring policy for anything that reaches the runtime TCB.

### T11 — Compromised developer credentials
An attacker with the founder's GitHub token can push to `main`. **This is currently the
single highest-impact realistic threat, and it is inadequately mitigated.** `main` cannot be
protected server-side on this plan; local hooks are bypassable and do not apply to an
attacker using the API directly. *Mitigations now:* the token is stored in the system
keyring, not on disk; the repository is private. *Planned:* hardware-backed 2FA, signed
commits, and server-side rulesets once the account plan or owner permits (see
`docs/operations/github-ownership.md`). Recorded as an accepted, documented risk.

### T12 — Compromised release-signing key
*Current:* **no signing key exists**, so nothing is signed and nothing can be verified.
Creating one before there is a secure place to keep it would be worse than not having one.
*Planned:* hardware-backed keys, an offline root, and short-lived subkeys (M5).

### T13 — Rollback / downgrade attack
The attacker forces a known-vulnerable earlier version. *Planned:* monotonic version
counters enforced by the updater, with anti-rollback state that survives a factory reset.
Explicitly noted because transactional rollback (Constitution §10) and anti-rollback are in
direct tension, and the resolution must be designed rather than discovered.

### T14 — Firmware / UEFI compromise
**Explicitly outside Malrynth's TCB.** Malrynth runs after firmware and cannot verify what
loaded it. Secure Boot and measured boot may later let Malrynth *detect* certain firmware
states, never *guarantee* them. Any claim that Malrynth is secure against compromised
firmware would be false.

### T15 — Cloud account compromise (future)
*Planned, when the account exists:* the device must remain fully usable offline
(Constitution §3), so account compromise must not yield device control. Sync data
end-to-end encrypted with device-held keys.

## Non-goals

Malrynth does not currently claim to defend against: sustained physical attackers, malicious
firmware, malicious hardware, side channels including Spectre-class attacks, or nation-state
adversaries. These are stated so that no reader infers protection from silence.

## Review

Revised at every milestone. Each entry moves from PLANNED to a mitigation with a test, or its
absence is re-accepted explicitly.
