# Shield Architecture

**Status:** PROPOSED. Target: M7+ (baseline), post-M7 (full).

## Position

> **Malrynth's security advantage is not a more aggressive scanner. It is that malware starts
> from a much weaker position than on an ambient-authority desktop.**

Shield is the layer that observes, detects, contains and recovers — **after** the architecture
has already denied most authority. If Shield is doing the heavy lifting, the architecture has
failed.

No claim of "best antivirus" is made anywhere. Detection quality is measured by independent
evaluation, not asserted.

## Four layers

```
PREVENT   verified boot · package signatures · capabilities · sandboxing · W^X · ASLR · IOMMU
   ↓
DETECT    static scanning · behaviour engine · network anomaly · integrity checks
   ↓
CONTAIN   freeze process tree · revoke capabilities · isolate network · protect snapshots
   ↓
RECOVER   rollback update · restore snapshot · repair system · offline recovery
```

**Prevention does most of the work.** A calculator with no network capability cannot exfiltrate
anything — no firewall rule is required, because no socket can exist.

## Prevent

Inherited from platform architecture rather than built by Shield: verified and measured boot,
signed content-addressed packages, capability confinement, per-app sandboxing, W^X, ASLR, guard
pages, hardware CFI where available, SMEP/SMAP-class protections, IOMMU-confined DMA, and
sandboxed parsers for every untrusted format.

## Detect

**Static layer.** Signature and rule-based scanning of files and packages. Reused engines
(candidates evaluated post-M7), running **heavily sandboxed** — a scanner parses hostile input
by definition and is itself an attack surface.

**Behaviour layer.** Consumes a kernel-provided `SecurityEventStream`:

```
ProcessStarted · ExecutableMapped · HandleGranted · PrivilegeChanged
DriverLoaded · PackageInstalled · FileMutationBurst · CredentialAccessAttempt
NetworkConnection · ListeningPortCreated · PersistenceChanged · ExecutableModified
```

Shield holds a **privileged read-only subscription**. It does not scrape kernel structures and
has no private kernel interface. This makes EDR observability an intentional architecture
rather than a collection of undocumented hooks — and it must be designed at M3, alongside the
object model, because retrofitted observability is exactly how undocumented hooks appear.

**Network layer.** Capability policy first, then stateful filtering, DNS/reputation, protocol
anomaly detection, IDS/IPS, rate limiting and flow telemetry.

## Contain

```
process opens 5,000 files · rewrites with high entropy · deletes originals
   · attempts snapshot deletion
        ↓
freeze process + descendants · revoke file capabilities · revoke network
   · preserve protected snapshot · record event graph · ask user/admin
```

**Applications never hold the authority to delete protected recovery snapshots — even for
files the user owns.** That single rule is the strongest structural ransomware defence
available, and it depends on snapshot deletion being a capability no ordinary app receives.

## Recover

Boot the previous slot · verify system files · roll back update or driver · restore user
snapshot · mount user files read-only · repair filesystem · export files · restore backup ·
reinstall without erasing user data. **All of it works offline** (Constitution §11).

## Threat coverage

Viruses, trojans, worms, spyware, ransomware, rootkits, bootkits, keyloggers, credential
stealers, cryptominers, malicious scripts and documents, malicious browser extensions, and
persistence mechanisms — mapped against
[`THREAT-MODEL.md`](THREAT-MODEL.md), which remains the authority on what is and is not
mitigated.

## Honest limits

- **DoS:** Malrynth can rate-limit malformed traffic and per-source abuse. It cannot defeat
  volumetric DDoS once the physical link is saturated. Upstream scrubbing is required, and
  claiming otherwise would be false.
- **Detection quality** is an ongoing intelligence problem, not a one-time build
  ([`EFFORT-AND-RISK.md`](../roadmap/EFFORT-AND-RISK.md)).
- **Rust is not a security argument** (Constitution §12).

## UX

```
MALRYNTH SHIELD   Protected ✓
System integrity ✓   Malware protection ✓   Network ✓   Credentials ✓   Recovery ✓
```

Advanced mode exposes the process tree, network flows, capability grants, blocked connections,
scanner events, driver trust, boot measurements and a threat timeline.

**No "your device is 73% protected, buy premium".** Shield reports state; it does not
manufacture anxiety.
